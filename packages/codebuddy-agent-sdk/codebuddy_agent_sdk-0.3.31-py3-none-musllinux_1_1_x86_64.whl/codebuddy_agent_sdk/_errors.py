"""Error definitions for CodeBuddy Agent SDK."""

from __future__ import annotations


class CodeBuddySDKError(Exception):
    """Base exception for CodeBuddy SDK errors."""

    pass


class CLIConnectionError(CodeBuddySDKError):
    """Raised when connection to CLI fails or is not established."""

    pass


class CLINotFoundError(CodeBuddySDKError):
    """Raised when CLI executable is not found."""

    def __init__(
        self,
        message: str,
        platform: str | None = None,
        arch: str | None = None,
    ):
        super().__init__(message)
        self.platform = platform
        self.arch = arch


class CLIJSONDecodeError(CodeBuddySDKError):
    """Raised when JSON decoding from CLI output fails."""

    pass


class ProcessError(CodeBuddySDKError):
    """Raised when CLI process encounters an error."""

    pass


class ExecutionError(CodeBuddySDKError):
    """Raised when execution fails (e.g., authentication error, API error).

    Contains the errors array from the ResultMessage.
    """

    def __init__(self, errors: list[str], subtype: str):
        message = errors[0] if errors else "Execution failed"
        super().__init__(message)
        self.errors = errors
        self.subtype = subtype
