"""CodeBuddy SDK Client for interactive conversations."""

from __future__ import annotations

import contextlib
import json
import os
from collections.abc import AsyncIterable, AsyncIterator
from types import TracebackType
from typing import Any

from ._errors import CLIConnectionError, ExecutionError
from ._message_parser import parse_message
from .transport import SubprocessTransport, Transport
from .types import (
    CanUseToolOptions,
    CodeBuddyAgentOptions,
    ErrorMessage,
    Message,
    ResultMessage,
)


class CodeBuddySDKClient:
    """
    Client for bidirectional, interactive conversations with CodeBuddy.

    This client provides full control over the conversation flow with support
    for streaming, interrupts, and dynamic message sending. For simple one-shot
    queries, consider using the query() function instead.

    Key features:
    - Bidirectional: Send and receive messages at any time
    - Stateful: Maintains conversation context across messages
    - Interactive: Send follow-ups based on responses
    - Control flow: Support for interrupts and session management

    Example:
        ```python
        async with CodeBuddySDKClient() as client:
            await client.query("Hello!")
            async for msg in client.receive_response():
                print(msg)
        ```
    """

    def __init__(
        self,
        options: CodeBuddyAgentOptions | None = None,
        transport: Transport | None = None,
    ):
        """Initialize CodeBuddy SDK client."""
        self.options = options or CodeBuddyAgentOptions()
        self._custom_transport = transport
        self._transport: Transport | None = None
        self._connected = False
        # Hook callback registry: callback_id -> hook function
        self._hook_callbacks: dict[str, Any] = {}

        # Permission mode and model tracking
        # Initial values (passed to CLI via command line args)
        self._initial_permission_mode: str = (
            options.permission_mode if options and options.permission_mode else "default"
        )
        self._initial_model: str | None = options.model if options else None
        # Current state starts same as initial
        self._current_permission_mode: str = self._initial_permission_mode
        self._current_model: str | None = self._initial_model

        # Session tracking for control requests
        self._session_id: str | None = None
        self._has_sent_query: bool = False

        os.environ["CODEBUDDY_CODE_ENTRYPOINT"] = "sdk-py-client"

    async def connect(self, prompt: str | AsyncIterable[dict[str, Any]] | None = None) -> None:
        """Connect to CodeBuddy with an optional initial prompt."""
        if self._custom_transport:
            self._transport = self._custom_transport
        else:
            self._transport = SubprocessTransport(
                options=self.options,
                prompt=prompt,
            )

        await self._transport.connect()
        self._connected = True
        await self._send_initialize()

    async def _send_initialize(self) -> None:
        """Send initialization control request."""
        if not self._transport:
            return

        hooks_config, self._hook_callbacks = self._build_hooks_config()

        # Get SDK MCP server names from transport
        sdk_mcp_server_names = self._transport.sdk_mcp_server_names

        request = {
            "type": "control_request",
            "request_id": f"init_{id(self)}",
            "request": {
                "subtype": "initialize",
                "hooks": hooks_config,
                # Include SDK MCP server names from transport
                "sdkMcpServers": sdk_mcp_server_names if sdk_mcp_server_names else None,
            },
        }
        await self._transport.write(json.dumps(request))

    def _build_hooks_config(self) -> tuple[dict[str, list[dict[str, Any]]] | None, dict[str, Any]]:
        """Build hooks configuration for CLI and callback registry.

        Returns:
            Tuple of (config for CLI, callback_id -> hook function mapping)
        """
        callbacks: dict[str, Any] = {}

        if not self.options.hooks:
            return None, callbacks

        config: dict[str, list[dict[str, Any]]] = {}

        for event, matchers in self.options.hooks.items():
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

    async def query(
        self,
        prompt: str | AsyncIterable[dict[str, Any]],
        session_id: str = "default",
    ) -> None:
        """
        Send a new request.

        Args:
            prompt: Either a string message or an async iterable of message dicts
            session_id: Session identifier for the conversation
        """
        if not self._connected or not self._transport:
            raise CLIConnectionError("Not connected. Call connect() first.")

        # Mark that a query has been sent (for control request tracking)
        self._has_sent_query = True

        if isinstance(prompt, str):
            message = {
                "type": "user",
                "message": {"role": "user", "content": prompt},
                "parent_tool_use_id": None,
                "session_id": session_id,
            }
            await self._transport.write(json.dumps(message))
        else:
            async for msg in prompt:
                if "session_id" not in msg:
                    msg["session_id"] = session_id
                await self._transport.write(json.dumps(msg))

    async def receive_messages(self) -> AsyncIterator[Message]:
        """Receive all messages from CodeBuddy."""
        if not self._transport:
            raise CLIConnectionError("Not connected.")

        async for line in self._transport.read():
            if not line:
                continue

            try:
                data = json.loads(line)

                # Handle control requests (permissions, hooks)
                if data.get("type") == "control_request":
                    await self._handle_control_request(data)
                    continue

                # Capture session_id from CLI messages for use in control requests
                if not self._session_id and data.get("session_id"):
                    self._session_id = data.get("session_id")

                    # Send pending permission mode change (if set before query)
                    if self._current_permission_mode != self._initial_permission_mode:
                        await self._send_pending_permission_mode()

                    # Send pending model change (if set before query)
                    if self._current_model != self._initial_model:
                        await self._send_pending_model()

                message = parse_message(data)
                if message:
                    yield message
            except json.JSONDecodeError:
                continue

    async def _handle_control_request(self, data: dict[str, Any]) -> None:
        """Handle control request from CLI."""
        if not self._transport:
            return

        request_id = data.get("request_id", "")
        request = data.get("request", {})
        subtype = request.get("subtype", "")

        if subtype == "can_use_tool":
            await self._handle_permission_request(request_id, request)
        elif subtype == "hook_callback":
            callback_id = request.get("callback_id", "")
            hook_input = request.get("input", {})
            tool_use_id = request.get("tool_use_id")

            # Execute the hook
            hook_response = await self._execute_hook(callback_id, hook_input, tool_use_id)

            response = {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": request_id,
                    "response": hook_response,
                },
            }
            await self._transport.write(json.dumps(response))
        elif subtype == "mcp_message":
            # MCP messages are handled at the transport level
            from .transport import SubprocessTransport

            if isinstance(self._transport, SubprocessTransport):
                await self._transport.handle_mcp_message_request(request_id, request)

    async def _handle_permission_request(self, request_id: str, request: dict[str, Any]) -> None:
        """Handle permission request from CLI."""
        if not self._transport:
            return

        tool_name = request.get("tool_name", "")
        input_data = request.get("input", {})
        tool_use_id = request.get("tool_use_id", "")
        agent_id = request.get("agent_id")

        can_use_tool = self.options.can_use_tool

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
            await self._transport.write(json.dumps(response))
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
            await self._transport.write(json.dumps(response))

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
            await self._transport.write(json.dumps(response))

    async def _execute_hook(
        self,
        callback_id: str,
        hook_input: dict[str, Any],
        tool_use_id: str | None,
    ) -> dict[str, Any]:
        """Execute a hook callback by looking up in the callback registry."""
        hook = self._hook_callbacks.get(callback_id)
        if not hook:
            return {"continue": True}

        try:
            result = await hook(hook_input, tool_use_id, {"signal": None})
            return dict(result)
        except Exception as e:
            return {"continue": False, "stopReason": str(e)}

    async def _send_pending_permission_mode(self) -> None:
        """Send pending permission mode change to CLI (fire-and-forget)."""
        if not self._transport or not self._session_id:
            return
        request = {
            "type": "control_request",
            "request_id": f"perm_pending_{id(self)}",
            "request": {
                "subtype": "set_permission_mode",
                "session_id": self._session_id,
                "mode": self._current_permission_mode,
            },
        }
        with contextlib.suppress(Exception):
            await self._transport.write(json.dumps(request))

    async def _send_pending_model(self) -> None:
        """Send pending model change to CLI (fire-and-forget)."""
        if not self._transport or not self._session_id:
            return
        request = {
            "type": "control_request",
            "request_id": f"model_pending_{id(self)}",
            "request": {
                "subtype": "set_model",
                "session_id": self._session_id,
                "model": self._current_model,
            },
        }
        with contextlib.suppress(Exception):
            await self._transport.write(json.dumps(request))

    async def receive_response(self) -> AsyncIterator[Message]:
        """
        Receive messages until and including a ResultMessage or ErrorMessage.

        Yields each message as it's received and terminates after
        yielding a ResultMessage or ErrorMessage.
        Raises ExecutionError if ResultMessage indicates an error.
        """
        async for message in self.receive_messages():
            # Check for execution error BEFORE yielding
            if isinstance(message, ResultMessage):
                if message.is_error and message.errors and len(message.errors) > 0:
                    raise ExecutionError(message.errors, message.subtype)
                yield message
                return

            yield message

            if isinstance(message, ErrorMessage):
                return

    async def interrupt(self) -> None:
        """Send interrupt signal."""
        if not self._transport:
            raise CLIConnectionError("Not connected.")

        request = {
            "type": "control_request",
            "request_id": f"interrupt_{id(self)}",
            "request": {"subtype": "interrupt"},
        }
        await self._transport.write(json.dumps(request))

    async def set_permission_mode(self, mode: str) -> None:
        """
        Set the permission mode.

        - Before first query: only updates local state
        - After first query: sends fire-and-forget control request to CLI
        """
        self._current_permission_mode = mode

        # Only sync to CLI if a query has been sent (CLI has session)
        if self._has_sent_query and self._session_id and self._transport:
            request = {
                "type": "control_request",
                "request_id": f"perm_{id(self)}",
                "request": {
                    "subtype": "set_permission_mode",
                    "session_id": self._session_id,
                    "mode": mode,
                },
            }
            with contextlib.suppress(Exception):
                await self._transport.write(json.dumps(request))

    def get_permission_mode(self) -> str:
        """Get the current permission mode."""
        return self._current_permission_mode

    async def set_model(self, model: str | None = None) -> None:
        """
        Set the AI model.

        - Before first query: only updates local state
        - After first query: sends fire-and-forget control request to CLI
        """
        self._current_model = model

        # Only sync to CLI if a query has been sent (CLI has session)
        if self._has_sent_query and self._session_id and self._transport:
            request = {
                "type": "control_request",
                "request_id": f"model_{id(self)}",
                "request": {
                    "subtype": "set_model",
                    "session_id": self._session_id,
                    "model": model,
                },
            }
            with contextlib.suppress(Exception):
                await self._transport.write(json.dumps(request))

    def get_model(self) -> str | None:
        """Get the current model."""
        return self._current_model

    async def disconnect(self) -> None:
        """Disconnect from CodeBuddy."""
        if self._transport:
            await self._transport.close()
            self._transport = None
        self._connected = False

    async def __aenter__(self) -> CodeBuddySDKClient:
        """Enter async context - automatically connects."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit async context - always disconnects."""
        await self.disconnect()
        return False
