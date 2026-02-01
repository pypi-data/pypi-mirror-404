"""
create_sdk_mcp_server - Create an SDK MCP Server

This function creates an MCP server that can be integrated into the SDK
and used with the CLI via the control protocol.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from .types import (
    CallToolResult,
    SdkMcpServer,
    SdkMcpServerOptions,
    SdkMcpServerResult,
    SdkMcpToolDefinition,
    ToolInputSchema,
)

# Tool handler type
ToolHandler = Callable[[dict[str, Any]], CallToolResult | Awaitable[CallToolResult]]

# Type variable for the decorated function
F = TypeVar("F", bound=ToolHandler)


def _python_type_to_json_schema(py_type: type) -> dict[str, Any]:
    """Convert Python type to JSON Schema type."""
    type_mapping = {
        str: {"type": "string"},
        int: {"type": "integer"},
        float: {"type": "number"},
        bool: {"type": "boolean"},
        list: {"type": "array"},
        dict: {"type": "object"},
    }
    return type_mapping.get(py_type, {"type": "string"})


def _convert_schema(input_schema: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """
    Convert input schema to JSON Schema format.

    Supports multiple formats:
    1. Simple type mapping: {"latitude": float, "longitude": float}
    2. JSON Schema format: {"properties": {...}, "required": [...]}

    Returns:
        Tuple of (properties dict, required list)
    """
    # Check if it's already in JSON Schema format
    if "properties" in input_schema:
        return input_schema.get("properties", {}), input_schema.get("required", [])

    if "type" in input_schema and input_schema.get("type") == "object":
        return input_schema.get("properties", {}), input_schema.get("required", [])

    # Simple type mapping format: {"param_name": type}
    properties = {}
    required = []

    for param_name, param_type in input_schema.items():
        if isinstance(param_type, type):
            properties[param_name] = _python_type_to_json_schema(param_type)
            required.append(param_name)
        elif isinstance(param_type, dict):
            properties[param_name] = param_type
            if "default" not in param_type:
                required.append(param_name)
        else:
            properties[param_name] = {"type": "string"}
            required.append(param_name)

    return properties, required


def tool(name: str, description: str, input_schema: dict[str, Any]) -> Callable[[F], F]:
    """
    Decorator to define an MCP tool.

    Example:
        ```python
        @tool("get_weather", "Get current weather", {"latitude": float, "longitude": float})
        async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
            return {"content": [{"type": "text", "text": f"Weather: sunny"}]}
        ```

    Args:
        name: Tool name (unique within the server)
        description: Tool description
        input_schema: Input parameters schema. Supports:
            - Simple types: {"latitude": float, "longitude": float}
            - JSON Schema: {"properties": {...}, "required": [...]}

    Returns:
        Decorated function with tool metadata attached
    """
    properties, required = _convert_schema(input_schema)
    tool_schema = ToolInputSchema(type="object", properties=properties, required=required)

    def decorator(func: F) -> F:
        func._tool_definition = SdkMcpToolDefinition(  # type: ignore[attr-defined]
            name=name,
            description=description,
            input_schema=tool_schema,
            handler=func,
        )
        return func

    return decorator


def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[Callable[..., Any]] | None = None,
) -> SdkMcpServerResult:
    """
    Create an SDK MCP Server.

    Args:
        name: Server name (unique within the session)
        version: Server version (defaults to "1.0.0")
        tools: List of functions decorated with @tool

    Returns:
        SDK MCP server result for use with query()

    Example:
        ```python
        from codebuddy_agent_sdk import create_sdk_mcp_server, tool, query

        @tool("get_weather", "Get weather", {"location": str})
        async def get_weather(args: dict) -> dict:
            return {"content": [{"type": "text", "text": f"Weather: sunny"}]}

        server = create_sdk_mcp_server(
            name="my-server",
            tools=[get_weather]
        )
        ```
    """
    tool_definitions: list[SdkMcpToolDefinition] = []
    if tools:
        for func in tools:
            if not hasattr(func, "_tool_definition"):
                raise ValueError(f"Function {func.__name__} is not decorated with @tool")
            tool_definitions.append(func._tool_definition)

    server = SdkMcpServer(SdkMcpServerOptions(name=name, version=version, tools=tool_definitions))

    return SdkMcpServerResult(type="sdk", name=name, server=server)
