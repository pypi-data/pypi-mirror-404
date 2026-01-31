from aip_agents.guardrails.engines.base import BaseGuardrailEngine as BaseGuardrailEngine
from aip_agents.guardrails.schemas import BaseGuardrailEngineConfig as BaseGuardrailEngineConfig, GuardrailResult as GuardrailResult
from aip_agents.guardrails.utils import convert_guardrail_mode_to_gl_sdk as convert_guardrail_mode_to_gl_sdk
from typing import Any

class NemoGuardrailEngine(BaseGuardrailEngine):
    """Wrapper for GL SDK NemoGuardrailEngine with aip-agents interface.

    This engine provides advanced LLM-based content filtering using NVIDIA's
    NeMo Guardrails. It can detect more complex safety violations beyond
    simple phrase matching.

    Note: Import of gllm_guardrail is deferred to __init__ to support
    lazy loading when guardrails are optional dependency.
    """
    def __init__(self, config: BaseGuardrailEngineConfig | None = None, **nemo_config: dict[str, Any]) -> None:
        """Initialize the NemoGuardrailEngine.

        Args:
            config: Engine configuration. Uses defaults if None provided.
            **nemo_config: Additional configuration passed to the underlying
                          NeMo engine (e.g., model paths, thresholds, etc.)

        Raises:
            ImportError: If gllm-guardrail is not installed.
        """
    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content using wrapped GL SDK NeMo engine.

        Args:
            content: The user input content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content using wrapped GL SDK NeMo engine.

        Args:
            content: The AI output content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""
