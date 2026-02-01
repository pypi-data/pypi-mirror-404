"""Type definitions for CodeBuddy Agent SDK."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from .mcp.types import SdkMcpServer

# ============= AskUserQuestion Types =============


@dataclass
class AskUserQuestionOption:
    """Option for AskUserQuestion tool."""

    label: str
    description: str


@dataclass
class AskUserQuestionQuestion:
    """Question for AskUserQuestion tool."""

    question: str
    header: str
    options: list[AskUserQuestionOption]
    multi_select: bool


@dataclass
class AskUserQuestionInput:
    """Input for AskUserQuestion tool."""

    questions: list[AskUserQuestionQuestion]
    answers: dict[str, str] | None = None


# ============= Permission Types =============


@dataclass
class CanUseToolOptions:
    """Options passed to canUseTool callback."""

    tool_use_id: str
    signal: Any | None = None
    agent_id: str | None = None
    suggestions: list[dict[str, Any]] | None = None
    blocked_path: str | None = None
    decision_reason: str | None = None


@dataclass
class PermissionResultAllow:
    """Allow permission result."""

    updated_input: dict[str, Any]
    behavior: Literal["allow"] = "allow"
    updated_permissions: list[dict[str, Any]] | None = None


@dataclass
class PermissionResultDeny:
    """Deny permission result."""

    message: str
    behavior: Literal["deny"] = "deny"
    interrupt: bool = False


PermissionResult = PermissionResultAllow | PermissionResultDeny

# CanUseTool callback type
CanUseTool = Callable[
    [str, dict[str, Any], CanUseToolOptions],
    Awaitable[PermissionResult],
]


# Permission modes
PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]

# Hook events
HookEvent = (
    Literal["PreToolUse"]
    | Literal["PostToolUse"]
    | Literal["UserPromptSubmit"]
    | Literal["Stop"]
    | Literal["SubagentStop"]
    | Literal["PreCompact"]
    | Literal["unstable_Checkpoint"]
)


# ============= Checkpoint Types =============


@dataclass
class FileVersion:
    """File version information for checkpoint snapshots."""

    file_path: str
    """Absolute path to the file."""

    version: int
    """Version number of this snapshot."""

    backup_time: int
    """Timestamp when the backup was created."""

    backup_file_name: str | None = None
    """Backup file name in the checkpoint storage."""


@dataclass
class CheckpointFileChangeStats:
    """Statistics about file changes in a checkpoint."""

    files: list[str]
    """List of changed file paths."""

    additions: int
    """Total lines added."""

    deletions: int
    """Total lines deleted."""


@dataclass
class Checkpoint:
    """Checkpoint data structure containing file snapshots and change statistics."""

    file_snapshots: dict[str, FileVersion]
    """Map of file paths to their version information."""

    id: str | None = None
    """Unique identifier for this checkpoint."""

    parent_id: str | None = None
    """Parent checkpoint ID (for checkpoint chain)."""

    logical_parent_id: str | None = None
    """Logical parent ID (used after compaction)."""

    label: str | None = None
    """Human-readable label (usually the user's prompt)."""

    created_at: int | None = None
    """Timestamp when the checkpoint was created."""

    file_change_stats: CheckpointFileChangeStats | None = None
    """File change statistics for this checkpoint."""


# Setting sources
SettingSource = Literal["user", "project", "local"]


# Agent definition
@dataclass
class AgentDefinition:
    """Agent definition configuration."""

    description: str
    prompt: str
    tools: list[str] | None = None
    disallowed_tools: list[str] | None = None
    model: str | None = None


# Content block types
@dataclass
class TextBlock:
    """Text content block."""

    text: str


@dataclass
class ThinkingBlock:
    """Thinking content block."""

    thinking: str
    signature: str


@dataclass
class ToolUseBlock:
    """Tool use content block."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultBlock:
    """Tool result content block."""

    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None


ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock


# Message types
@dataclass
class UserMessage:
    """User message."""

    content: str | list[ContentBlock]
    uuid: str | None = None
    parent_tool_use_id: str | None = None


@dataclass
class AssistantMessage:
    """Assistant message with content blocks."""

    content: list[ContentBlock]
    model: str
    parent_tool_use_id: str | None = None
    error: str | None = None


@dataclass
class SystemMessage:
    """System message with metadata."""

    subtype: str
    data: dict[str, Any]


@dataclass
class ResultMessage:
    """Result message with cost and usage information."""

    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    errors: list[str] | None = None


@dataclass
class StreamEvent:
    """Stream event for partial message updates during streaming."""

    uuid: str
    session_id: str
    event: dict[str, Any]
    parent_tool_use_id: str | None = None


@dataclass
class ErrorMessage:
    """Error message from CLI."""

    error: str
    session_id: str | None = None


Message = (
    UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent | ErrorMessage
)


# Hook types
class HookContext(TypedDict):
    """Context information for hook callbacks."""

    signal: Any | None


class SyncHookJSONOutput(TypedDict):
    """Synchronous hook output with control and decision fields."""

    continue_: NotRequired[bool]
    suppressOutput: NotRequired[bool]
    stopReason: NotRequired[str]
    decision: NotRequired[Literal["block"]]
    reason: NotRequired[str]


HookJSONOutput = SyncHookJSONOutput

HookCallback = Callable[
    [Any, str | None, HookContext],
    Awaitable[HookJSONOutput],
]


@dataclass
class HookMatcher:
    """Hook matcher configuration."""

    matcher: str | None = None
    hooks: list[HookCallback] = field(default_factory=list)
    timeout: float | None = None


# MCP Server config
class McpStdioServerConfig(TypedDict):
    """MCP stdio server configuration."""

    type: NotRequired[Literal["stdio"]]
    command: str
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]


class McpSdkServerConfig(TypedDict):
    """
    SDK MCP Server configuration - for servers running within the SDK process.
    Created via create_sdk_mcp_server().
    """

    type: Literal["sdk"]
    name: str
    server: SdkMcpServer


McpServerConfig = McpStdioServerConfig | McpSdkServerConfig


# System prompt configuration
@dataclass
class AppendSystemPrompt:
    """Append to the default system prompt."""

    append: str


# Main configuration
@dataclass
class CodeBuddyAgentOptions:
    """Query options for CodeBuddy Agent SDK."""

    session_id: str | None = None
    """Custom session ID for the conversation."""

    allowed_tools: list[str] = field(default_factory=list)
    """
    List of tool names that are auto-allowed without prompting for permission.
    These tools will execute automatically without asking the user for approval.
    """

    disallowed_tools: list[str] = field(default_factory=list)
    """
    List of tool names that are disallowed. When the model attempts to use
    these tools, the request will be denied. MCP tools matching this list
    are also filtered from the model's context.
    """

    tools: list[str] | None = None
    """
    Restrict which built-in tools CodeBuddy can use (whitelist).
    - None (default): Use all available built-in tools
    - []: Disable all built-in tools
    - ["Bash", "Read"]: Only specified built-in tools are available
    """

    system_prompt: str | AppendSystemPrompt | None = None
    """
    System prompt configuration.

    - `str`: Override the entire system prompt
    - `AppendSystemPrompt`: Append to the default system prompt
    """

    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    model: str | None = None
    fallback_model: str | None = None
    cwd: str | Path | None = None
    codebuddy_code_path: str | Path | None = None
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    stderr: Callable[[str], None] | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
    can_use_tool: CanUseTool | None = None
    """
    Custom permission handler callback.
    Called when a tool requires permission approval.
    """
