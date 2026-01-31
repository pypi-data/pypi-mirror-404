"""Utility functions for guardrail mode conversion.

This module provides utilities for converting between aip-agents GuardrailMode
and gllm-guardrail GuardrailMode enums.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from typing import Any

from aip_agents.guardrails.schemas import GuardrailMode


def convert_guardrail_mode_to_gl_sdk(mode: GuardrailMode) -> Any:
    """Convert aip-agents GuardrailMode to gllm-guardrail GuardrailMode.

    This function performs lazy import of gllm-guardrail to support optional
    dependencies. The conversion is necessary because we maintain our own
    GuardrailMode enum for API consistency while wrapping the external library.

    Args:
        mode: The aip-agents GuardrailMode to convert

    Returns:
        The corresponding gllm-guardrail GuardrailMode enum value

    Raises:
        ImportError: If gllm-guardrail is not installed
    """
    try:
        from gllm_guardrail.constants import GuardrailMode as GLGuardrailMode  # pragma: no cover
    except ImportError as e:  # pragma: no cover
        raise ImportError(
            "gllm-guardrail is required for guardrails. Install with: pip install 'aip-agents[guardrails]'"
        ) from e  # pragma: no cover

    mode_mapping = {
        GuardrailMode.INPUT_ONLY: GLGuardrailMode.INPUT_ONLY,
        GuardrailMode.OUTPUT_ONLY: GLGuardrailMode.OUTPUT_ONLY,
        GuardrailMode.INPUT_OUTPUT: GLGuardrailMode.BOTH,
        GuardrailMode.DISABLED: GLGuardrailMode.DISABLED,
    }

    return mode_mapping[mode]
