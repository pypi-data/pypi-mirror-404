from aip_agents.mcp.client.base_mcp_client import BaseMCPClient as BaseMCPClient
from aip_agents.ptc.mcp.sandbox_bridge import build_mcp_payload as build_mcp_payload
from aip_agents.ptc.payload import SandboxPayload as SandboxPayload

async def build_sandbox_payload(mcp_client: BaseMCPClient | None = None, default_tool_timeout: float = 60.0) -> SandboxPayload:
    """Build sandbox payload from MCP client configuration (MCP-only).

    Args:
        mcp_client: The MCP client with configured servers.
        default_tool_timeout: Default timeout for tool calls in seconds.

    Returns:
        SandboxPayload containing files and env vars for the sandbox.
    """
def wrap_ptc_code(code: str) -> str:
    """Wrap user PTC code with necessary imports and setup (MCP-only).

    This prepends sys.path setup to ensure the tools package is importable.

    Args:
        code: User-provided Python code.

    Returns:
        Wrapped code ready for sandbox execution.
    """
