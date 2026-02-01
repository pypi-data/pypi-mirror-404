"""CodeBuddy Agent SDK for Python."""

from ._errors import (
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    CodeBuddySDKError,
    ExecutionError,
    ProcessError,
)
from ._version import __version__
from .client import CodeBuddySDKClient
from .mcp import (
    CallToolResult,
    SdkControlServerTransport,
    SdkMcpServerOptions,
    SdkMcpServerResult,
    SdkMcpToolDefinition,
    TextContent,
    ToolHandler,
    create_sdk_mcp_server,
    tool,
)
from .query import query
from .transport import Transport
from .types import (
    AgentDefinition,
    AppendSystemPrompt,
    AskUserQuestionInput,
    AskUserQuestionOption,
    AskUserQuestionQuestion,
    AssistantMessage,
    CanUseTool,
    CanUseToolOptions,
    Checkpoint,
    CheckpointFileChangeStats,
    CodeBuddyAgentOptions,
    ContentBlock,
    ErrorMessage,
    FileVersion,
    HookCallback,
    HookContext,
    HookEvent,
    HookJSONOutput,
    HookMatcher,
    McpSdkServerConfig,
    McpServerConfig,
    McpStdioServerConfig,
    Message,
    PermissionMode,
    PermissionResult,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    SettingSource,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

__all__ = [
    # Main API
    "query",
    "CodeBuddySDKClient",
    "Transport",
    "__version__",
    # MCP Server API
    "create_sdk_mcp_server",
    "tool",
    "SdkControlServerTransport",
    "SdkMcpServerOptions",
    "SdkMcpServerResult",
    "SdkMcpToolDefinition",
    "ToolHandler",
    "CallToolResult",
    "TextContent",
    # Types - Permission
    "PermissionMode",
    # Types - Messages
    "Message",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "StreamEvent",
    "ErrorMessage",
    # Types - Content blocks
    "ContentBlock",
    "TextBlock",
    "ThinkingBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    # Types - Configuration
    "CodeBuddyAgentOptions",
    "AgentDefinition",
    "AppendSystemPrompt",
    "SettingSource",
    # Types - Permission
    "CanUseTool",
    "CanUseToolOptions",
    "PermissionResult",
    "PermissionResultAllow",
    "PermissionResultDeny",
    # Types - AskUserQuestion
    "AskUserQuestionOption",
    "AskUserQuestionQuestion",
    "AskUserQuestionInput",
    # Types - Hooks
    "HookEvent",
    "HookCallback",
    "HookMatcher",
    "HookJSONOutput",
    "HookContext",
    # Types - Checkpoint
    "Checkpoint",
    "CheckpointFileChangeStats",
    "FileVersion",
    # Types - MCP
    "McpServerConfig",
    "McpStdioServerConfig",
    "McpSdkServerConfig",
    # Errors
    "CodeBuddySDKError",
    "CLIConnectionError",
    "CLINotFoundError",
    "CLIJSONDecodeError",
    "ProcessError",
    "ExecutionError",
]
