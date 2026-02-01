"""Subprocess transport for CLI communication."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from collections.abc import AsyncIterable, AsyncIterator, Callable
from typing import Any, TypeGuard, cast

from .._binary import get_cli_path, get_cli_version
from .._version import __version__
from ..mcp.sdk_control_server_transport import SdkControlServerTransport
from ..mcp.types import JSONRPCMessage, SdkMcpServer
from ..types import AppendSystemPrompt, CodeBuddyAgentOptions, McpSdkServerConfig, McpServerConfig
from .base import Transport

# Buffer limit for subprocess streams (100 MB)
# Prevents asyncio.LimitOverrunError when MCP servers return large JSON responses
_STREAM_BUFFER_LIMIT = 100 * 1024 * 1024  # 100 MB


def _is_sdk_mcp_server(config: McpServerConfig) -> TypeGuard[McpSdkServerConfig]:
    """Type guard to check if config is an SDK MCP server."""
    return isinstance(config, dict) and config.get("type") == "sdk"


class SubprocessTransport(Transport):
    """Transport that communicates with CLI via subprocess."""

    def __init__(
        self,
        options: CodeBuddyAgentOptions,
        prompt: str | AsyncIterable[dict[str, Any]] | None = None,
    ):
        self.prompt = prompt
        self._process: asyncio.subprocess.Process | None = None
        self._closed = False

        # Validate session_id format
        if options.session_id:
            session_id_pattern = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_:]*$")
            if not session_id_pattern.match(options.session_id):
                raise ValueError(
                    f'Invalid session ID format: "{options.session_id}". '
                    "Session IDs support numbers, letters, hyphens, underscores, and colons, "
                    "but must start with a letter or number."
                )

        # SDK MCP Server management
        self._sdk_mcp_transports: dict[str, SdkControlServerTransport] = {}
        self._sdk_mcp_servers: dict[str, SdkMcpServer] = {}
        self._sdk_mcp_server_names: list[str] = []

        # Extract SDK MCP servers from options
        sdk_servers, regular_servers = self._extract_mcp_servers(options.mcp_servers)

        # Store modified options with only regular MCP servers
        self.options = CodeBuddyAgentOptions(
            session_id=options.session_id,
            allowed_tools=options.allowed_tools,
            disallowed_tools=options.disallowed_tools,
            tools=options.tools,
            system_prompt=options.system_prompt,
            mcp_servers=regular_servers or {},
            permission_mode=options.permission_mode,
            continue_conversation=options.continue_conversation,
            resume=options.resume,
            max_turns=options.max_turns,
            model=options.model,
            fallback_model=options.fallback_model,
            cwd=options.cwd,
            codebuddy_code_path=options.codebuddy_code_path,
            env=options.env,
            extra_args=options.extra_args,
            stderr=options.stderr,
            hooks=options.hooks,
            include_partial_messages=options.include_partial_messages,
            fork_session=options.fork_session,
            agents=options.agents,
            setting_sources=options.setting_sources,
            can_use_tool=options.can_use_tool,
        )

        # Connect SDK MCP servers
        for name, server in sdk_servers.items():
            self._connect_sdk_mcp_server(name, server)

    def _extract_mcp_servers(
        self,
        mcp_servers: dict[str, McpServerConfig] | None,
    ) -> tuple[dict[str, SdkMcpServer], dict[str, McpServerConfig] | None]:
        """
        Extract SDK MCP servers from the mcp_servers config.
        SDK servers are identified by having type: 'sdk'.

        Returns:
            Tuple of (sdk_servers dict, regular_servers dict or None)
        """
        if not mcp_servers or not isinstance(mcp_servers, dict):
            return {}, None

        sdk_servers: dict[str, SdkMcpServer] = {}
        regular_servers: dict[str, McpServerConfig] = {}

        for name, config in mcp_servers.items():
            if _is_sdk_mcp_server(config):
                # SDK MCP server
                sdk_servers[name] = config["server"]
                self._sdk_mcp_server_names.append(name)
            else:
                # Regular MCP server (stdio)
                regular_servers[name] = config

        return (
            sdk_servers,
            regular_servers if regular_servers else None,
        )

    def _connect_sdk_mcp_server(self, name: str, server: SdkMcpServer) -> None:
        """Connect an SDK MCP server."""

        def _create_message_forwarder(server_name: str) -> Callable[[JSONRPCMessage], None]:
            def forwarder(msg: JSONRPCMessage) -> None:
                # This callback sends MCP messages from server to CLI
                # For SDK servers, responses go through handle_mcp_message_request
                pass

            return forwarder

        # Create custom transport that forwards to CLI
        transport = SdkControlServerTransport(_create_message_forwarder(name))

        # Store transport and server
        self._sdk_mcp_transports[name] = transport
        self._sdk_mcp_servers[name] = server

        # Connect server to transport
        server.connect(transport)

    @property
    def sdk_mcp_server_names(self) -> list[str]:
        """Get the list of SDK MCP server names."""
        return self._sdk_mcp_server_names

    async def handle_mcp_message_request(
        self,
        request_id: str,
        request: dict[str, Any],
    ) -> None:
        """Handle MCP message control request from CLI."""
        server_name = request.get("server_name", "")
        message = cast(JSONRPCMessage, request.get("message", {}))

        server = self._sdk_mcp_servers.get(server_name)

        if not server:
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "error",
                    "request_id": request_id,
                    "error": f"SDK MCP server not found: {server_name}",
                },
            }
            await self.write(json.dumps(response))
            return

        try:
            # Handle the message with the MCP server
            mcp_response = await server.handle_message(message)

            response = {
                "type": "control_response",
                "response": {
                    "subtype": "success",
                    "request_id": request_id,
                    "response": {
                        "mcp_response": mcp_response or {"jsonrpc": "2.0", "result": {}, "id": 0},
                    },
                },
            }
            await self.write(json.dumps(response))

        except Exception as e:
            response = {
                "type": "control_response",
                "response": {
                    "subtype": "error",
                    "request_id": request_id,
                    "error": str(e),
                },
            }
            await self.write(json.dumps(response))

    def _get_cli_path(self) -> str:
        """Get the path to CLI executable."""
        # User-specified path takes highest precedence
        if self.options.codebuddy_code_path:
            return str(self.options.codebuddy_code_path)

        # Use the binary resolver (env var -> package binary -> monorepo)
        return get_cli_path()

    def _build_args(self) -> list[str]:
        """Build CLI arguments from options."""
        args = [
            "--input-format",
            "stream-json",
            "--verbose",
            "--output-format",
            "stream-json",
            "--print",
        ]
        opts = self.options

        # Model options
        if opts.model:
            args.extend(["--model", opts.model])
        if opts.fallback_model:
            args.extend(["--fallback-model", opts.fallback_model])

        # Permission options
        if opts.permission_mode:
            args.extend(["--permission-mode", opts.permission_mode])

        # Turn limits
        if opts.max_turns:
            args.extend(["--max-turns", str(opts.max_turns)])

        # Session options
        if opts.session_id:
            args.extend(["--session-id", opts.session_id])
        if opts.continue_conversation:
            args.append("--continue")
        if opts.resume:
            args.extend(["--resume", opts.resume])
        if opts.fork_session:
            args.append("--fork-session")

        # Tool options
        if opts.allowed_tools:
            args.extend(["--allowedTools"] + list(opts.allowed_tools))
        if opts.disallowed_tools:
            args.extend(["--disallowedTools"] + list(opts.disallowed_tools))
        if opts.tools is not None:
            args.extend(["--tools", ",".join(opts.tools)])

        # MCP options
        if opts.mcp_servers and isinstance(opts.mcp_servers, dict):
            args.extend(["--mcp-config", json.dumps({"mcpServers": opts.mcp_servers})])

        # Settings
        # SDK default: don't load any filesystem settings for clean environment isolation
        # When setting_sources is explicitly provided (including empty list), use it
        # When not provided (None), default to 'none' for SDK isolation
        if opts.setting_sources is not None:
            setting_value = (
                "none" if len(opts.setting_sources) == 0 else ",".join(opts.setting_sources)
            )
            args.extend(["--setting-sources", setting_value])
        else:
            # SDK default behavior: no filesystem settings loaded
            args.extend(["--setting-sources", "none"])

        # Output options
        if opts.include_partial_messages:
            args.append("--include-partial-messages")

        # System prompt options
        if opts.system_prompt is not None:
            if isinstance(opts.system_prompt, str):
                args.extend(["--system-prompt", opts.system_prompt])
            elif isinstance(opts.system_prompt, AppendSystemPrompt):
                args.extend(["--append-system-prompt", opts.system_prompt.append])

        # Extra args (custom flags)
        for flag, value in opts.extra_args.items():
            if value is None:
                args.append(f"--{flag}")
            else:
                args.extend([f"--{flag}", value])

        return args

    async def connect(self) -> None:
        """Start the subprocess."""
        cli_path = self._get_cli_path()
        args = self._build_args()
        cwd = str(self.options.cwd) if self.options.cwd else os.getcwd()

        env = {
            **os.environ,
            **self.options.env,
            "CODEBUDDY_CODE_ENTRYPOINT": "sdk-py",
        }

        # Build SDK UserAgent and inject via CODEBUDDY_CUSTOM_HEADERS
        # Format: CodeBuddy Agent SDK/Version (Language/RuntimeVersion) CodeBuddy Code/Version
        # SDK UserAgent is placed first so user's headers can override it
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        cli_version = get_cli_version(cli_path)
        sdk_user_agent = f"User-Agent: CodeBuddy Agent SDK/{__version__} (Python/{python_version}) CodeBuddy Code/{cli_version}"
        existing_headers = env.get("CODEBUDDY_CUSTOM_HEADERS", "")
        if existing_headers:
            env["CODEBUDDY_CUSTOM_HEADERS"] = f"{sdk_user_agent}\n{existing_headers}"
        else:
            env["CODEBUDDY_CUSTOM_HEADERS"] = sdk_user_agent

        self._process = await asyncio.create_subprocess_exec(
            cli_path,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            limit=_STREAM_BUFFER_LIMIT,
        )

        # Start stderr reader if callback provided
        if self.options.stderr and self._process.stderr:
            asyncio.create_task(self._read_stderr())

    async def _read_stderr(self) -> None:
        """Read stderr and call callback."""
        if self._process and self._process.stderr and self.options.stderr:
            async for line in self._process.stderr:
                self.options.stderr(line.decode())

    async def read(self) -> AsyncIterator[str]:
        """Read lines from stdout."""
        if not self._process or not self._process.stdout:
            return

        async for line in self._process.stdout:
            if self._closed:
                break
            yield line.decode().strip()

    async def write(self, data: str) -> None:
        """Write data to stdin."""
        if self._process and self._process.stdin:
            self._process.stdin.write((data + "\n").encode())
            await self._process.stdin.drain()

    async def close(self) -> None:
        """Close the subprocess."""
        if self._closed:
            return

        self._closed = True

        # Clean up SDK MCP resources
        for transport in self._sdk_mcp_transports.values():
            await transport.close()
        self._sdk_mcp_transports.clear()
        self._sdk_mcp_servers.clear()

        if self._process:
            self._process.kill()
            await self._process.wait()
