"""Transport base class for CLI communication."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class Transport(ABC):
    """Abstract transport layer for CLI communication."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to CLI."""

    @abstractmethod
    def read(self) -> AsyncIterator[str]:
        """Read messages from CLI as an async iterator."""

    @abstractmethod
    async def write(self, data: str) -> None:
        """Write data to CLI."""

    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""

    @property
    def sdk_mcp_server_names(self) -> list[str]:
        """Get the list of SDK MCP server names. Override in subclasses."""
        return []
