# flake8: noqa: F401
"""Sandbox module for isolated code execution.

This module provides abstractions for running code in sandboxed environments.
All components support lazy loading to work with optional dependencies (e2b).

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aip_agents.sandbox.e2b_runtime import E2BSandboxRuntime
    from aip_agents.sandbox.template_builder import ensure_ptc_template
    from aip_agents.sandbox.types import SandboxExecutionResult

_IMPORT_MAP = {
    "E2BSandboxRuntime": "aip_agents.sandbox.e2b_runtime",
    "ensure_ptc_template": "aip_agents.sandbox.template_builder",
    "SandboxExecutionResult": "aip_agents.sandbox.types",
}

_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import components on first access."""
    if name in _cache:
        return _cache[name]

    if name in _IMPORT_MAP:
        try:
            module = __import__(_IMPORT_MAP[name], fromlist=[name])
            _cache[name] = getattr(module, name)
            return _cache[name]
        except ImportError as e:
            raise ImportError(f"Failed to import {name}. Install with: pip install aip-agents[local]") from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_IMPORT_MAP.keys())
