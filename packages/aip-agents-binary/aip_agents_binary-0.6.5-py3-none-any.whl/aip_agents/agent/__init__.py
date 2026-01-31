"""This module initializes the agent package.

Exposes the core agent classes and interfaces.

Author:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aip_agents.agent.base_agent import BaseAgent

if TYPE_CHECKING:
    from aip_agents.agent.google_adk_agent import GoogleADKAgent
    from aip_agents.agent.langflow_agent import LangflowAgent
from aip_agents.agent.base_langgraph_agent import BaseLangGraphAgent
from aip_agents.agent.interface import AgentInterface
from aip_agents.agent.langgraph_memory_enhancer_agent import (
    LangGraphMemoryEnhancerAgent,
)
from aip_agents.agent.langgraph_react_agent import (
    LangChainAgent,
    LangGraphAgent,
    LangGraphReactAgent,
)

__all__ = [
    "AgentInterface",
    "BaseAgent",
    "BaseLangGraphAgent",
    "LangGraphReactAgent",
    "GoogleADKAgent",
    "LangGraphAgent",
    "LangChainAgent",
    "LangflowAgent",
    "LangGraphMemoryEnhancerAgent",
]


def __getattr__(name: str) -> Any:
    """Lazy import of heavy agent implementations.

    This avoids importing heavy dependencies (Google ADK, etc.)
    when they are not needed.

    Args:
        name: Attribute name to import.

    Returns:
        The requested class.

    Raises:
        AttributeError: If attribute is not found.
    """
    if name == "GoogleADKAgent":
        from aip_agents.agent.google_adk_agent import (
            GoogleADKAgent as _GoogleADKAgent,
        )

        return _GoogleADKAgent
    elif name == "LangflowAgent":
        from aip_agents.agent.langflow_agent import LangflowAgent as _LangflowAgent

        return _LangflowAgent
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
