"""
SDK Control Server Transport

Custom transport implementation that bridges SDK MCP servers to CLI process.
This transport forwards MCP messages through the control protocol.
"""

from __future__ import annotations

from collections.abc import Callable

from .types import JSONRPCMessage

# Callback function type for sending MCP messages to CLI
SendMcpMessageCallback = Callable[[JSONRPCMessage], None]


class SdkControlServerTransport:
    """
    SdkControlServerTransport - bridges MCP servers to CLI via control messages.

    This transport implements a simple interface for forwarding MCP messages
    between the SDK MCP server and the CLI via the control protocol.
    """

    def __init__(self, send_mcp_message: SendMcpMessageCallback):
        """
        Create a new SDK Control Server Transport.

        Args:
            send_mcp_message: Callback function to forward MCP messages to CLI
        """
        self._send_mcp_message = send_mcp_message
        self._is_closed = False
        self._on_message: Callable[[JSONRPCMessage], None] | None = None
        self._on_close: Callable[[], None] | None = None
        self._on_error: Callable[[Exception], None] | None = None

    @property
    def closed(self) -> bool:
        """Check if the transport is closed."""
        return self._is_closed

    def set_on_message(self, callback: Callable[[JSONRPCMessage], None] | None) -> None:
        """Set the message callback."""
        self._on_message = callback

    def set_on_close(self, callback: Callable[[], None] | None) -> None:
        """Set the close callback."""
        self._on_close = callback

    def set_on_error(self, callback: Callable[[Exception], None] | None) -> None:
        """Set the error callback."""
        self._on_error = callback

    async def start(self) -> None:
        """
        Start the transport.
        No-op since connection is already established via stdio.
        """
        pass

    async def send(self, message: JSONRPCMessage) -> None:
        """
        Send a message to the CLI via control_request.

        Args:
            message: The JSON-RPC message to send
        """
        if self._is_closed:
            raise RuntimeError("Transport is closed")
        # Forward message to CLI via control_request
        self._send_mcp_message(message)

    async def close(self) -> None:
        """Close the transport."""
        if self._is_closed:
            return

        self._is_closed = True
        if self._on_close:
            self._on_close()

    def handle_incoming_message(self, message: JSONRPCMessage) -> None:
        """
        Handle incoming message from CLI.
        This method should be called when the CLI sends a message to this server.

        Args:
            message: The JSON-RPC message from CLI
        """
        if self._is_closed:
            return
        if self._on_message:
            self._on_message(message)
