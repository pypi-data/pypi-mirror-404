"""PTC (Programmatic Tool Calling) core module (MCP-only).

This module provides the core PTC functionality for MCP tools, including
executor, prompt builder, and sandbox bridge.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from aip_agents.ptc.exceptions import PTCError, PTCToolError
from aip_agents.ptc.prompt_builder import PromptConfig, build_ptc_prompt, compute_ptc_prompt_hash

__all__ = [
    # Exceptions
    "PTCError",
    "PTCToolError",
    # Executor
    "PTCSandboxConfig",
    "PTCSandboxExecutor",
    # Prompt builder
    "PromptConfig",
    "build_ptc_prompt",
    "compute_ptc_prompt_hash",
    # Sandbox bridge
    "build_sandbox_payload",
    "wrap_ptc_code",
]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == "PTCSandboxConfig":
        from aip_agents.ptc.executor import PTCSandboxConfig

        return PTCSandboxConfig
    elif name == "PTCSandboxExecutor":
        from aip_agents.ptc.executor import PTCSandboxExecutor

        return PTCSandboxExecutor
    elif name == "build_sandbox_payload":
        from aip_agents.ptc.sandbox_bridge import build_sandbox_payload

        return build_sandbox_payload
    elif name == "wrap_ptc_code":
        from aip_agents.ptc.sandbox_bridge import wrap_ptc_code

        return wrap_ptc_code
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
