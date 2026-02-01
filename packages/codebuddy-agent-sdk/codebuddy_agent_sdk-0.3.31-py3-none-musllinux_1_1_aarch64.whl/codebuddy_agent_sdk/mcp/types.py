"""Type definitions for SDK MCP Server."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

if TYPE_CHECKING:
    from .sdk_control_server_transport import SdkControlServerTransport


# ============= JSON-RPC Types =============


class JSONRPCRequest(TypedDict, total=False):
    """JSON-RPC 2.0 request."""

    jsonrpc: Literal["2.0"]
    id: str | int
    method: str
    params: dict[str, Any] | list[Any] | None


class JSONRPCError(TypedDict, total=False):
    """JSON-RPC 2.0 error."""

    code: int
    message: str
    data: Any


class JSONRPCResponse(TypedDict, total=False):
    """JSON-RPC 2.0 response."""

    jsonrpc: Literal["2.0"]
    id: str | int | None
    result: Any
    error: JSONRPCError


class JSONRPCNotification(TypedDict, total=False):
    """JSON-RPC 2.0 notification."""

    jsonrpc: Literal["2.0"]
    method: str
    params: dict[str, Any] | list[Any] | None


JSONRPCMessage = JSONRPCRequest | JSONRPCResponse | JSONRPCNotification


# ============= MCP Tool Types =============


class TextContent(TypedDict, total=False):
    """Text content in tool result."""

    type: Literal["text"]
    text: str


class ImageContent(TypedDict, total=False):
    """Image content in tool result."""

    type: Literal["image"]
    data: str
    mimeType: str


class EmbeddedResource(TypedDict, total=False):
    """Embedded resource content in tool result."""

    type: Literal["resource"]
    resource: dict[str, Any]


ToolResultContent = TextContent | ImageContent | EmbeddedResource


class CallToolResult(TypedDict, total=False):
    """Result from calling a tool."""

    content: list[ToolResultContent]
    isError: bool


# Tool handler type - takes arguments dict and returns CallToolResult
ToolHandler = Callable[[dict[str, Any]], CallToolResult | Awaitable[CallToolResult]]


@dataclass
class ToolInputProperty:
    """Property definition for tool input schema."""

    type: str
    description: str | None = None
    enum: list[str] | None = None
    default: Any = None
    minimum: float | None = None
    maximum: float | None = None


@dataclass
class ToolInputSchema:
    """JSON Schema for tool input."""

    type: Literal["object"] = "object"
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    required: list[str] = field(default_factory=list)


@dataclass
class SdkMcpToolDefinition:
    """
    Tool definition for SDK MCP Server.

    Example:
        ```python
        tool_def = SdkMcpToolDefinition(
            name="get_weather",
            description="Get the current weather for a location",
            input_schema=ToolInputSchema(
                properties={
                    "location": {"type": "string", "description": "The city name"},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                required=["location"],
            ),
            handler=get_weather_handler,
        )
        ```
    """

    name: str
    description: str
    input_schema: ToolInputSchema
    handler: ToolHandler


@dataclass
class SdkMcpServerOptions:
    """
    Options for creating an SDK MCP Server.

    Attributes:
        name: Server name (must be unique within the session)
        version: Server version (defaults to "1.0.0")
        tools: List of tool definitions to register
    """

    name: str
    version: str = "1.0.0"
    tools: list[SdkMcpToolDefinition] = field(default_factory=list)


@dataclass
class SdkMcpServerResult:
    """
    Result type for create_sdk_mcp_server.

    Attributes:
        type: Type discriminator - always "sdk" for SDK MCP servers
        name: Server name
        server: The MCP server instance
    """

    type: Literal["sdk"]
    name: str
    server: SdkMcpServer


class SdkMcpServer:
    """
    SDK MCP Server implementation.

    This class implements an MCP server that runs within the SDK process
    and communicates with the CLI via the control protocol.
    """

    def __init__(self, options: SdkMcpServerOptions):
        self.name = options.name
        self.version = options.version
        self.tools: dict[str, SdkMcpToolDefinition] = {}
        self._transport: SdkControlServerTransport | None = None

        # Register tools
        for tool_def in options.tools:
            self.tools[tool_def.name] = tool_def

    def connect(self, transport: SdkControlServerTransport) -> None:
        """Connect the server to a transport."""
        self._transport = transport

    async def handle_message(self, message: JSONRPCMessage) -> JSONRPCMessage | None:
        """Handle an incoming JSON-RPC message."""
        # Check if it's a request (has method and id)
        if "method" not in message:
            return None

        method = cast(str, message.get("method", ""))
        msg_id = cast("str | int | None", message.get("id"))
        params = cast("dict[str, Any] | None", message.get("params", {}))

        if method == "initialize":
            return await self._handle_initialize(msg_id, params)
        elif method == "tools/list":
            return await self._handle_tools_list(msg_id)
        elif method == "tools/call":
            return await self._handle_tools_call(msg_id, params)
        elif method == "notifications/initialized":
            # Notification, no response needed
            return None
        else:
            # Unknown method
            if msg_id is not None:
                return self._create_error_response(msg_id, -32601, f"Method not found: {method}")
            return None

    async def _handle_initialize(
        self, msg_id: str | int | None, params: dict[str, Any] | None
    ) -> JSONRPCMessage:
        """Handle initialize request."""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
        }
        return self._create_response(msg_id, result)

    async def _handle_tools_list(self, msg_id: str | int | None) -> JSONRPCMessage:
        """Handle tools/list request."""
        tools_list = []
        for tool_def in self.tools.values():
            tools_list.append(
                {
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "inputSchema": {
                        "type": tool_def.input_schema.type,
                        "properties": tool_def.input_schema.properties,
                        "required": tool_def.input_schema.required,
                    },
                }
            )
        return self._create_response(msg_id, {"tools": tools_list})

    async def _handle_tools_call(
        self, msg_id: str | int | None, params: dict[str, Any] | None
    ) -> JSONRPCMessage:
        """Handle tools/call request."""
        if not isinstance(params, dict):
            return self._create_error_response(msg_id, -32602, "Invalid params")

        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool_def = self.tools.get(tool_name)
        if not tool_def:
            return self._create_error_response(msg_id, -32602, f"Tool not found: {tool_name}")

        try:
            # Call the handler
            result = tool_def.handler(arguments)
            # Handle async handlers
            if inspect.isawaitable(result):
                result = await result

            return self._create_response(msg_id, result)
        except Exception as e:
            # Return error as tool result
            error_result: CallToolResult = {
                "content": [{"type": "text", "text": str(e)}],
                "isError": True,
            }
            return self._create_response(msg_id, error_result)

    def _create_response(self, msg_id: str | int | None, result: Any) -> JSONRPCResponse:
        """Create a JSON-RPC response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": result,
        }

    def _create_error_response(
        self, msg_id: str | int | None, code: int, message: str
    ) -> JSONRPCResponse:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": code, "message": message},
        }
