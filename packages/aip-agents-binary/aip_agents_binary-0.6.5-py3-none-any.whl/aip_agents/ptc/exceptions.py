"""PTC-specific exceptions.

This module defines exceptions for Programmatic Tool Calling operations.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""


class PTCError(Exception):
    """Base exception for PTC errors."""

    pass


class PTCToolError(PTCError):
    """Error during tool execution.

    Attributes:
        server_name: The MCP server where the error occurred.
        tool_name: The tool that failed.
    """

    def __init__(
        self,
        message: str,
        server_name: str | None = None,
        tool_name: str | None = None,
    ) -> None:
        """Initialize PTCToolError.

        Args:
            message: Error message.
            server_name: The MCP server name (optional).
            tool_name: The tool name (optional).
        """
        super().__init__(message)
        self.server_name = server_name
        self.tool_name = tool_name
