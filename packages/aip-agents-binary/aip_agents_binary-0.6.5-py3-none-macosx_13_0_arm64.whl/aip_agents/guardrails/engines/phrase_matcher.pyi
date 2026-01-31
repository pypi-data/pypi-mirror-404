from aip_agents.guardrails.engines.base import BaseGuardrailEngine as BaseGuardrailEngine
from aip_agents.guardrails.schemas import BaseGuardrailEngineConfig as BaseGuardrailEngineConfig, GuardrailResult as GuardrailResult
from aip_agents.guardrails.utils import convert_guardrail_mode_to_gl_sdk as convert_guardrail_mode_to_gl_sdk

class PhraseMatcherEngine(BaseGuardrailEngine):
    """Wrapper for GL SDK PhraseMatcherEngine with aip-agents interface.

    This engine performs rule-based banned phrase detection using the
    GL SDK's PhraseMatcherEngine. It checks for exact phrase matches
    and blocks content containing banned phrases.

    Note: Import of gllm_guardrail is deferred to __init__ to support
    lazy loading when guardrails are optional dependency.
    """
    def __init__(self, config: BaseGuardrailEngineConfig | None = None, banned_phrases: list[str] | None = None) -> None:
        """Initialize the PhraseMatcherEngine.

        Args:
            config: Engine configuration. Uses defaults if None provided.
            banned_phrases: List of phrases that should trigger blocking.
                          Defaults to empty list if None provided.

        Raises:
            ImportError: If gllm-guardrail is not installed.
        """
    @property
    def banned_phrases(self) -> list[str]:
        """Get the list of banned phrases."""
    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content using wrapped GL SDK engine.

        Args:
            content: The user input content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content using wrapped GL SDK engine.

        Args:
            content: The AI output content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""
