"""Top-level PTC Sandbox Bridge (MCP-only).

This module provides the unified entry point for building sandbox payloads
for MCP tools.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from aip_agents.mcp.client.base_mcp_client import BaseMCPClient
from aip_agents.ptc.mcp.sandbox_bridge import build_mcp_payload
from aip_agents.ptc.payload import SandboxPayload


async def build_sandbox_payload(
    mcp_client: BaseMCPClient | None = None,
    default_tool_timeout: float = 60.0,
) -> SandboxPayload:
    """Build sandbox payload from MCP client configuration (MCP-only).

    Args:
        mcp_client: The MCP client with configured servers.
        default_tool_timeout: Default timeout for tool calls in seconds.

    Returns:
        SandboxPayload containing files and env vars for the sandbox.
    """
    # Build MCP payload
    if mcp_client:
        return await build_mcp_payload(mcp_client, default_tool_timeout)
    return SandboxPayload()


def wrap_ptc_code(code: str) -> str:
    """Wrap user PTC code with necessary imports and setup (MCP-only).

    This prepends sys.path setup to ensure the tools package is importable.

    Args:
        code: User-provided Python code.

    Returns:
        Wrapped code ready for sandbox execution.
    """
    preamble = """# PTC Code Wrapper - Auto-generated
import sys
import os

# Add tools package to path
_tools_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
if _tools_dir not in sys.path:
    sys.path.insert(0, _tools_dir)

# User code below
"""
    return preamble + code
