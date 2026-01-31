# flake8: noqa: F401
"""Guardrails package for content filtering and safety checks.

This package provides modular guardrail engines and managers for filtering
harmful content in AI agent interactions. All components support lazy loading
to work with optional dependencies.

Example:
    Basic usage with a phrase matcher engine:

    .. code-block:: python

        from aip_agents.guardrails import GuardrailManager, GuardrailMiddleware
        from aip_agents.guardrails.engines import PhraseMatcherEngine
        from aip_agents.guardrails.schemas import GuardrailMode

        # Create a guardrail engine
        engine = PhraseMatcherEngine(
            banned_phrases=["spam", "inappropriate"]
        )

        # Create a manager
        manager = GuardrailManager(engines=[engine])

        # Create middleware for agent integration
        middleware = GuardrailMiddleware(guardrail_manager=manager)

        # Use with agent (components are lazy-loaded)
        from aip_agents.agent import LangGraphReactAgent
        agent = LangGraphReactAgent(
            name="my_agent",
            guardrail=manager,
            # ... other agent config
        )

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aip_agents.guardrails.exceptions import GuardrailViolationError
    from aip_agents.guardrails.manager import GuardrailManager
    from aip_agents.guardrails.middleware import GuardrailMiddleware
    from aip_agents.guardrails.schemas import (
        BaseGuardrailEngineConfig,
        GuardrailInput,
        GuardrailMode,
        GuardrailResult,
    )


_IMPORT_MAP = {
    "GuardrailViolationError": "aip_agents.guardrails.exceptions",
    "GuardrailManager": "aip_agents.guardrails.manager",
    "GuardrailMiddleware": "aip_agents.guardrails.middleware",
    "BaseGuardrailEngineConfig": "aip_agents.guardrails.schemas",
    "GuardrailMode": "aip_agents.guardrails.schemas",
    "GuardrailInput": "aip_agents.guardrails.schemas",
    "GuardrailResult": "aip_agents.guardrails.schemas",
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
            raise ImportError(f"Failed to import {name}. Optional dependencies may be missing: {e}") from e

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = list(_IMPORT_MAP.keys())
