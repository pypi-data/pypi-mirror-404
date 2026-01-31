from _typeshed import Incomplete
from aip_agents.guardrails.exceptions import GuardrailViolationError as GuardrailViolationError
from aip_agents.guardrails.manager import GuardrailManager as GuardrailManager
from aip_agents.guardrails.schemas import GuardrailInput as GuardrailInput
from aip_agents.middleware.base import AgentMiddleware as AgentMiddleware, ModelRequest as ModelRequest
from typing import Any

class GuardrailMiddleware(AgentMiddleware):
    """Middleware that integrates guardrails into agent execution.

    This middleware wraps a GuardrailManager and automatically checks content
    at appropriate points during agent execution:

    - Before model invocation: checks user input from messages
    - After model invocation: checks AI output from messages

    If unsafe content is detected, raises GuardrailViolationError to stop execution.

    Attributes:
        guardrail_manager: The GuardrailManager to use for content checking
    """
    guardrail_manager: Incomplete
    def __init__(self, guardrail_manager: GuardrailManager) -> None:
        """Initialize the GuardrailMiddleware.

        Args:
            guardrail_manager: GuardrailManager instance to use for checking
        """
    @property
    def tools(self) -> list:
        """Guardrails are passive filters and don't contribute tools."""
    @property
    def system_prompt_additions(self) -> str | None:
        """Guardrails are passive filters and don't modify system prompts."""
    async def abefore_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Asynchronously check user input before model invocation.

        Extracts the last user message from state and checks it with guardrails.
        If unsafe, raises GuardrailViolationError to stop execution.

        Args:
            state: Current agent state containing messages and context

        Returns:
            Empty dict (no state modifications needed)

        Raises:
            GuardrailViolationError: If user input violates safety policies
        """
    def before_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check user input before model invocation (synchronous wrapper).

        Note:
            This is a synchronous wrapper for the async `abefore_model()` method.
            LangGraph agents primarily use `abefore_model()` in async contexts.
            This method should rarely be called directly. If called from an async
            context with a running event loop, it will attempt to handle it,
            but `abefore_model()` should be preferred.

        Args:
            state: Current agent state containing messages and context

        Returns:
            Empty dict (no state modifications needed)

        Raises:
            GuardrailViolationError: If user input violates safety policies
        """
    def modify_model_request(self, request: ModelRequest, state: dict[str, Any]) -> ModelRequest:
        """Guardrails don't modify model requests."""
    async def aafter_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Asynchronously check AI output after model invocation.

        Extracts the last AI message from state and checks it with guardrails.
        If unsafe, raises GuardrailViolationError to stop execution.

        Args:
            state: Current agent state after model invocation

        Returns:
            Empty dict (no state modifications needed)

        Raises:
            GuardrailViolationError: If AI output violates safety policies
        """
    def after_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check AI output after model invocation (synchronous wrapper)."""
