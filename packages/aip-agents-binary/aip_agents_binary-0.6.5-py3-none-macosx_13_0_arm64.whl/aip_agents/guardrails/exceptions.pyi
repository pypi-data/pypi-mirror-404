from _typeshed import Incomplete
from aip_agents.guardrails.schemas import GuardrailResult as GuardrailResult

class GuardrailViolationError(Exception):
    """Exception raised when unsafe content is detected by guardrails.

    This exception is raised by GuardrailMiddleware when content violates
    safety policies. It contains the GuardrailResult with details about
    why the content was blocked.

    Attributes:
        result: The GuardrailResult containing safety check details
        message: Human-readable error message
    """
    result: Incomplete
    message: Incomplete
    def __init__(self, result: GuardrailResult, message: str | None = None) -> None:
        """Initialize the exception.

        Args:
            result: The GuardrailResult from the failed safety check
            message: Optional custom error message
        """
