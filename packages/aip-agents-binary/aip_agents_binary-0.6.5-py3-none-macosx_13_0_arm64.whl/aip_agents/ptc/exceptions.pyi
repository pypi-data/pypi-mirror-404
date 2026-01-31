from _typeshed import Incomplete

class PTCError(Exception):
    """Base exception for PTC errors."""

class PTCToolError(PTCError):
    """Error during tool execution.

    Attributes:
        server_name: The MCP server where the error occurred.
        tool_name: The tool that failed.
    """
    server_name: Incomplete
    tool_name: Incomplete
    def __init__(self, message: str, server_name: str | None = None, tool_name: str | None = None) -> None:
        """Initialize PTCToolError.

        Args:
            message: Error message.
            server_name: The MCP server name (optional).
            tool_name: The tool name (optional).
        """
