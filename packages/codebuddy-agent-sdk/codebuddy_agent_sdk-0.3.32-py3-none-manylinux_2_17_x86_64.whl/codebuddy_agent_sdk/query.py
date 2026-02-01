"""Query function for one-shot interactions with CodeBuddy."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import asdict
from typing import Any

from ._errors import ExecutionError
from ._message_parser import parse_message
from .transport import SubprocessTransport, Transport
from .types import (
    AppendSystemPrompt,
    CanUseToolOptions,
    CodeBuddyAgentOptions,
    ErrorMessage,
    HookCallback,
    HookMatcher,
    Message,
    ResultMessage,
)


async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: CodeBuddyAgentOptions | None = None,
    transport: Transport | None = None,
) -> AsyncIterator[Message]:
    """
    Query CodeBuddy for one-shot or unidirectional streaming interactions.

    This function is ideal for simple, stateless queries where you don't need
    bidirectional communication or conversation management. For interactive,
    stateful conversations, use CodeBuddySDKClient instead.

    Args:
        prompt: The prompt to send to CodeBuddy. Can be a string for single-shot
                queries or an AsyncIterable[dict] for streaming mode.
        options: Optional configuration (defaults to CodeBuddyAgentOptions() if None).
        transport: Optional transport implementation. If provided, this will be used
                  instead of the default subprocess transport.

    Yields:
        Messages from the conversation.

    Example:
        ```python
        async for message in query(prompt="What is 2+2?"):
            print(message)
        ```
    """
    if options is None:
        options = CodeBuddyAgentOptions()

    os.environ["CODEBUDDY_CODE_ENTRYPOINT"] = "sdk-py"

    # Transport handles SDK MCP server extraction automatically
    if transport is None:
        transport = SubprocessTransport(options=options, prompt=prompt)

    await transport.connect()

    # Hook callback registry
    hook_callbacks: dict[str, HookCallback] = {}

    try:
        hook_callbacks = await _send_initialize(transport, options)
        await _send_prompt(transport, prompt)

        async for line in transport.read():
            if not line:
                continue

            try:
                data = json.loads(line)

                # Handle control requests (hooks, permissions, MCP messages)
                if data.get("type") == "control_request":
                    await _handle_control_request(transport, data, options, hook_callbacks)
                    continue

                message = parse_message(data)
                if message:
                    # Check for execution error BEFORE yielding
                    if isinstance(message, ResultMessage):
                        if message.is_error and message.errors and len(message.errors) > 0:
                            raise ExecutionError(message.errors, message.subtype)
                        yield message
                        break

                    yield message

                    if isinstance(message, ErrorMessage):
                        break

            except json.JSONDecodeError:
                continue  # Ignore non-JSON lines

    finally:
        await transport.close()


async def _send_initialize(
    transport: Transport,
    options: CodeBuddyAgentOptions,
) -> dict[str, HookCallback]:
    """Send initialization control request.

    Returns:
        Hook callbacks registry (callback_id -> hook function)
    """
    hooks_config, hook_callbacks = _build_hooks_config(options.hooks)
    agents_config = (
        {name: asdict(agent) for name, agent in options.agents.items()} if options.agents else None
    )

    # Parse system_prompt config
    system_prompt: str | None = None
    append_system_prompt: str | None = None
    if isinstance(options.system_prompt, str):
        system_prompt = options.system_prompt
    elif isinstance(options.system_prompt, AppendSystemPrompt):
        append_system_prompt = options.system_prompt.append

    # Get SDK MCP server names from transport
    sdk_mcp_server_names = transport.sdk_mcp_server_names

    request = {
        "type": "control_request",
        "request_id": f"init_{id(options)}",
        "request": {
            "subtype": "initialize",
            "hooks": hooks_config,
            "systemPrompt": system_prompt,
            "appendSystemPrompt": append_system_prompt,
            "agents": agents_config,
            # Include SDK MCP server names from transport
            "sdkMcpServers": sdk_mcp_server_names if sdk_mcp_server_names else None,
        },
    }
    await transport.write(json.dumps(request))
    return hook_callbacks


async def _send_prompt(transport: Transport, prompt: str | AsyncIterable[dict[str, Any]]) -> None:
    """Send user prompt."""
    if isinstance(prompt, str):
        message = {
            "type": "user",
            "session_id": "",
            "message": {"role": "user", "content": prompt},
            "parent_tool_use_id": None,
        }
        await transport.write(json.dumps(message))
    else:
        async for msg in prompt:
            await transport.write(json.dumps(msg))


async def _handle_control_request(
    transport: Transport,
    data: dict[str, Any],
    options: CodeBuddyAgentOptions,
    hook_callbacks: dict[str, HookCallback],
) -> None:
    """Handle control request from CLI."""
    request_id = data.get("request_id", "")
    request = data.get("request", {})
    subtype = request.get("subtype", "")

    if subtype == "hook_callback":
        # Handle hook callback
        callback_id = request.get("callback_id", "")
        hook_input = request.get("input", {})
        tool_use_id = request.get("tool_use_id")

        # Find and execute the hook using callback registry
        response = await _execute_hook(callback_id, hook_input, tool_use_id, hook_callbacks)

        # Send response
        control_response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": response,
            },
        }
        await transport.write(json.dumps(control_response))

    elif subtype == "can_use_tool":
        await _handle_permission_request(transport, request_id, request, options)

    elif subtype == "mcp_message":
        # MCP messages are handled at the transport level
        if isinstance(transport, SubprocessTransport):
            await transport.handle_mcp_message_request(request_id, request)


async def _handle_permission_request(
    transport: Transport,
    request_id: str,
    request: dict[str, Any],
    options: CodeBuddyAgentOptions,
) -> None:
    """Handle permission request from CLI."""
    tool_name = request.get("tool_name", "")
    input_data = request.get("input", {})
    tool_use_id = request.get("tool_use_id", "")
    agent_id = request.get("agent_id")

    can_use_tool = options.can_use_tool

    # Default deny if no callback provided
    if not can_use_tool:
        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": {
                    "allowed": False,
                    "reason": "No permission handler provided",
                    "tool_use_id": tool_use_id,
                },
            },
        }
        await transport.write(json.dumps(response))
        return

    try:
        callback_options = CanUseToolOptions(
            tool_use_id=tool_use_id,
            signal=None,
            agent_id=agent_id,
            suggestions=request.get("permission_suggestions"),
            blocked_path=request.get("blocked_path"),
            decision_reason=request.get("decision_reason"),
        )

        result = await can_use_tool(tool_name, input_data, callback_options)

        if result.behavior == "allow":
            response_data = {
                "allowed": True,
                "updatedInput": result.updated_input,
                "tool_use_id": tool_use_id,
            }
        else:
            response_data = {
                "allowed": False,
                "reason": result.message,
                "interrupt": result.interrupt,
                "tool_use_id": tool_use_id,
            }

        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": response_data,
            },
        }
        await transport.write(json.dumps(response))

    except Exception as e:
        response = {
            "type": "control_response",
            "response": {
                "subtype": "success",
                "request_id": request_id,
                "response": {
                    "allowed": False,
                    "reason": str(e),
                    "tool_use_id": tool_use_id,
                },
            },
        }
        await transport.write(json.dumps(response))


async def _execute_hook(
    callback_id: str,
    hook_input: dict[str, Any],
    tool_use_id: str | None,
    hook_callbacks: dict[str, HookCallback],
) -> dict[str, Any]:
    """Execute a hook callback by looking up in the callback registry."""
    hook = hook_callbacks.get(callback_id)
    if not hook:
        return {"continue": True}

    try:
        result = await hook(hook_input, tool_use_id, {"signal": None})
        return dict(result)
    except Exception as e:
        return {"continue": False, "stopReason": str(e)}


def _build_hooks_config(
    hooks: dict[Any, list[HookMatcher]] | None,
) -> tuple[dict[str, list[dict[str, Any]]] | None, dict[str, HookCallback]]:
    """Build hooks configuration for CLI and callback registry.

    Returns:
        Tuple of (config for CLI, callback_id -> hook function mapping)
    """
    callbacks: dict[str, HookCallback] = {}

    if not hooks:
        return None, callbacks

    config: dict[str, list[dict[str, Any]]] = {}

    for event, matchers in hooks.items():
        event_str = str(event)
        matcher_configs = []

        for i, m in enumerate(matchers):
            callback_ids = []
            for j, hook in enumerate(m.hooks):
                callback_id = f"hook_{event_str}_{i}_{j}"
                callback_ids.append(callback_id)
                callbacks[callback_id] = hook

            matcher_configs.append(
                {
                    "matcher": m.matcher,
                    "hookCallbackIds": callback_ids,
                    "timeout": m.timeout,
                }
            )

        config[event_str] = matcher_configs

    return (config if config else None), callbacks
