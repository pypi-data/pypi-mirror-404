"""MCP Client.

This module provides a adapter client for interacting with MCP servers.

Authors:
    Fachriza Dian Adhiatma (fachriza.d.adhiatma@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aip_agents.mcp.client.base_mcp_client import BaseMCPClient

if TYPE_CHECKING:
    from aip_agents.mcp.client.google_adk.client import GoogleADKMCPClient
    from aip_agents.mcp.client.langchain.client import LangchainMCPClient

__all__ = ["GoogleADKMCPClient", "LangchainMCPClient", "BaseMCPClient"]


def __getattr__(name: str) -> Any:
    """Lazy import of MCP client implementations.

    This avoids importing heavy dependencies (Google ADK, Vertex AI, etc.)
    when they are not needed.

    Args:
        name: Attribute name to import.

    Returns:
        The requested class.

    Raises:
        AttributeError: If attribute is not found.
    """
    if name == "GoogleADKMCPClient":
        from aip_agents.mcp.client.google_adk.client import (
            GoogleADKMCPClient as _GoogleADKMCPClient,
        )

        return _GoogleADKMCPClient
    elif name == "LangchainMCPClient":
        from aip_agents.mcp.client.langchain.client import (
            LangchainMCPClient as _LangchainMCPClient,
        )

        return _LangchainMCPClient
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
