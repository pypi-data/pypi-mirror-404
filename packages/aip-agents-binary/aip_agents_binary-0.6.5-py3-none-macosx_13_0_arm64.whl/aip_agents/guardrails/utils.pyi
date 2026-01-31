from aip_agents.guardrails.schemas import GuardrailMode as GuardrailMode
from typing import Any

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
