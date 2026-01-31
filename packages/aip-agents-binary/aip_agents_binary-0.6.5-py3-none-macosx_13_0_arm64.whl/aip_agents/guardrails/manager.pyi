from _typeshed import Incomplete
from aip_agents.guardrails.engines.base import GuardrailEngine as GuardrailEngine
from aip_agents.guardrails.schemas import GuardrailInput as GuardrailInput, GuardrailMode as GuardrailMode, GuardrailResult as GuardrailResult
from typing import Any

class GuardrailManager:
    """Orchestrates multiple guardrail engines with fail-fast behavior.

    The manager accepts one or more guardrail engines and runs them in sequence.
    If any engine reports unsafe content, execution stops immediately (fail-fast)
    and returns the violation result.

    Attributes:
        engines: List of guardrail engines to orchestrate
    """
    enabled: bool
    engines: Incomplete
    def __init__(self, engine: GuardrailEngine | list[GuardrailEngine] | None = None, engines: list[GuardrailEngine] | None = None) -> None:
        """Initialize the GuardrailManager.

        Args:
            engine: Single guardrail engine to use
            engines: List of guardrail engines to use

        Raises:
            ValueError: If both engine and engines are provided
        """
    def model_dump(self) -> dict[str, Any]:
        """Serialize manager configuration into a JSON-compatible dictionary."""
    async def check_content(self, content: str | GuardrailInput) -> GuardrailResult:
        """Check content against all registered engines.

        Executes engines in order with fail-fast behavior. If any engine
        reports unsafe content, returns immediately with that result.

        Args:
            content: Content to check. Can be a string (treated as input-only)
                    or GuardrailInput with input/output fields.

        Returns:
            GuardrailResult indicating if content passed all checks
        """
