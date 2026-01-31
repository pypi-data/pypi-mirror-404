"""NemoGuardrailEngine wrapper for GL SDK guardrails.

This module wraps the GL SDK's NemoGuardrailEngine to provide advanced
LLM-based content filtering capabilities.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from typing import Any

from aip_agents.guardrails.engines.base import BaseGuardrailEngine
from aip_agents.guardrails.schemas import (
    BaseGuardrailEngineConfig,
    GuardrailResult,
)
from aip_agents.guardrails.utils import convert_guardrail_mode_to_gl_sdk


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
        super().__init__(config)

        # Lazy import to support optional dependency and avoid import errors
        # when gllm-guardrail is not installed
        try:
            from gllm_guardrail import NemoGuardrailEngine as GLNemoGuardrailEngine
            from gllm_guardrail.engine.nemo_engine import NemoGuardrailEngineConfig as GLNemoGuardrailEngineConfig
        except ImportError as e:
            raise ImportError(
                "gllm-guardrail is required for guardrails. Install with: pip install 'aip-agents[guardrails]'"
            ) from e

        # Convert our GuardrailMode to GL SDK's GuardrailMode
        gl_mode = convert_guardrail_mode_to_gl_sdk(self.config.guardrail_mode)

        # Create GL SDK config with guardrail_mode and any additional NeMo config
        # NemoGuardrailEngineConfig accepts guardrail_mode and other NeMo-specific params directly
        gl_config = GLNemoGuardrailEngineConfig(guardrail_mode=gl_mode, **nemo_config)

        # Initialize the underlying GL SDK engine
        self._engine = GLNemoGuardrailEngine(config=gl_config)

    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content using wrapped GL SDK NeMo engine.

        Args:
            content: The user input content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
        gl_result = await self._engine.check_input(content)
        return GuardrailResult(
            is_safe=gl_result.is_safe,
            reason=gl_result.reason,
            filtered_content=gl_result.filtered_content,
        )

    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content using wrapped GL SDK NeMo engine.

        Args:
            content: The AI output content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
        gl_result = await self._engine.check_output(content)
        return GuardrailResult(
            is_safe=gl_result.is_safe,
            reason=gl_result.reason,
            filtered_content=gl_result.filtered_content,
        )

    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""
        return {
            "type": "nemo",
            "config": self._engine.config.model_dump(),
        }
