# flake8: noqa: F401
"""Guardrail engines package with lazy loading support.

This package provides guardrail engines that wrap GL SDK implementations.
Engines are loaded lazily to support optional dependencies.

Example:
    Import and use guardrail engines:

    .. code-block:: python

        # Lazy import - works even if gllm-guardrail is not installed
        from aip_agents.guardrails.engines import PhraseMatcherEngine, NemoGuardrailEngine

        # Create a phrase matcher engine
        phrase_engine = PhraseMatcherEngine(
            banned_phrases=["spam", "inappropriate"]
        )

        # Create a NeMo guardrail engine (requires gllm-guardrail)
        nemo_engine = NemoGuardrailEngine(
            # NeMo-specific configuration
        )

        # Use with GuardrailManager
        from aip_agents.guardrails import GuardrailManager
        manager = GuardrailManager(engines=[phrase_engine, nemo_engine])

Note:
    All engines support lazy loading. If `gllm-guardrail` is not installed,
    importing these engines will raise an ImportError only when actually
    instantiated, not at import time.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aip_agents.guardrails.engines.nemo import NemoGuardrailEngine
    from aip_agents.guardrails.engines.phrase_matcher import PhraseMatcherEngine


_IMPORT_MAP = {
    "NemoGuardrailEngine": "aip_agents.guardrails.engines.nemo",
    "PhraseMatcherEngine": "aip_agents.guardrails.engines.phrase_matcher",
}

_cache: dict[str, Any] = {}


def __getattr__(name: str) -> Any:
    """Lazy import engines on first access."""
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
