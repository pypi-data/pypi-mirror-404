"""
MCP (Model Context Protocol) Integration

This module provides utilities for creating and managing SDK MCP servers
that can be integrated with the CLI via the control protocol.
"""

from .create_sdk_mcp_server import (
    create_sdk_mcp_server,
    tool,
)
from .sdk_control_server_transport import SdkControlServerTransport
from .types import (
    CallToolResult,
    SdkMcpServerOptions,
    SdkMcpServerResult,
    SdkMcpToolDefinition,
    TextContent,
    ToolHandler,
)

__all__ = [
    # Factory functions
    "create_sdk_mcp_server",
    "tool",
    # Transport
    "SdkControlServerTransport",
    # Types
    "SdkMcpServerOptions",
    "SdkMcpServerResult",
    "SdkMcpToolDefinition",
    "ToolHandler",
    "CallToolResult",
    "TextContent",
]
