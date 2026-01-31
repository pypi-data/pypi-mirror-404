"""Exceptions raised by the guardrails system.

This module defines custom exceptions that are raised when guardrail
violations occur or when guardrail operations fail.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from aip_agents.guardrails.schemas import GuardrailResult


class GuardrailViolationError(Exception):
    """Exception raised when unsafe content is detected by guardrails.

    This exception is raised by GuardrailMiddleware when content violates
    safety policies. It contains the GuardrailResult with details about
    why the content was blocked.

    Attributes:
        result: The GuardrailResult containing safety check details
        message: Human-readable error message
    """

    def __init__(self, result: GuardrailResult, message: str | None = None) -> None:
        """Initialize the exception.

        Args:
            result: The GuardrailResult from the failed safety check
            message: Optional custom error message
        """
        self.result = result
        self.message = message or f"Content blocked by guardrails: {result.reason}"

        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of the exception."""
        return self.message
