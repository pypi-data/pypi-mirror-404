"""PhraseMatcherEngine wrapper for GL SDK guardrails.

This module wraps the GL SDK's PhraseMatcherEngine to provide a consistent
interface for the aip-agents guardrails system.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from aip_agents.guardrails.engines.base import BaseGuardrailEngine
from aip_agents.guardrails.schemas import (
    BaseGuardrailEngineConfig,
    GuardrailResult,
)
from aip_agents.guardrails.utils import convert_guardrail_mode_to_gl_sdk


class PhraseMatcherEngine(BaseGuardrailEngine):
    """Wrapper for GL SDK PhraseMatcherEngine with aip-agents interface.

    This engine performs rule-based banned phrase detection using the
    GL SDK's PhraseMatcherEngine. It checks for exact phrase matches
    and blocks content containing banned phrases.

    Note: Import of gllm_guardrail is deferred to __init__ to support
    lazy loading when guardrails are optional dependency.
    """

    def __init__(
        self,
        config: BaseGuardrailEngineConfig | None = None,
        banned_phrases: list[str] | None = None,
    ) -> None:
        """Initialize the PhraseMatcherEngine.

        Args:
            config: Engine configuration. Uses defaults if None provided.
            banned_phrases: List of phrases that should trigger blocking.
                          Defaults to empty list if None provided.

        Raises:
            ImportError: If gllm-guardrail is not installed.
        """
        super().__init__(config)

        # Lazy import to support optional dependency and avoid import errors
        # when gllm-guardrail is not installed
        try:
            from gllm_guardrail import PhraseMatcherEngine as GLPhraseMatcherEngine
            from gllm_guardrail.engine.base_engine import BaseGuardrailEngineConfig as GLBaseGuardrailEngineConfig
        except ImportError as e:
            raise ImportError(
                "gllm-guardrail is required for guardrails. Install with: pip install 'aip-agents[guardrails]'"
            ) from e

        # Convert our GuardrailMode to GL SDK's GuardrailMode
        gl_mode = convert_guardrail_mode_to_gl_sdk(self.config.guardrail_mode)

        # Create GL SDK config
        gl_config = GLBaseGuardrailEngineConfig(guardrail_mode=gl_mode)

        # Initialize the underlying GL SDK engine
        self._engine = GLPhraseMatcherEngine(
            config=gl_config,
            banned_phrases=banned_phrases or [],
        )

    @property
    def banned_phrases(self) -> list[str]:
        """Get the list of banned phrases."""
        return self._engine.banned_phrases

    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content using wrapped GL SDK engine.

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
        """Check AI output content using wrapped GL SDK engine.

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
            "type": "phrase_matcher",
            "config": {
                **self.config.model_dump(),
                "banned_phrases": self.banned_phrases,
            },
        }
