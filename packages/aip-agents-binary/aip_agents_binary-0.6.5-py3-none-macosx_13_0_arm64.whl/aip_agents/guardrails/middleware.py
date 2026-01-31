"""GuardrailMiddleware for integrating guardrails into agent execution.

This module provides GuardrailMiddleware that hooks into the agent execution
flow to automatically check content before and after model invocations.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage, HumanMessage

from aip_agents.guardrails.exceptions import GuardrailViolationError
from aip_agents.guardrails.schemas import GuardrailInput
from aip_agents.middleware.base import AgentMiddleware, ModelRequest

if TYPE_CHECKING:
    from aip_agents.guardrails.manager import GuardrailManager


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

    def __init__(self, guardrail_manager: GuardrailManager) -> None:
        """Initialize the GuardrailMiddleware.

        Args:
            guardrail_manager: GuardrailManager instance to use for checking
        """
        self.guardrail_manager = guardrail_manager

    @property
    def tools(self) -> list:
        """Guardrails are passive filters and don't contribute tools."""
        return []

    @property
    def system_prompt_additions(self) -> str | None:
        """Guardrails are passive filters and don't modify system prompts."""
        return None

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
        # Extract last user message from state
        messages = state.get("messages", [])
        user_input = self._extract_last_user_message(messages)

        if user_input is not None:
            # Check input content
            result = await self.guardrail_manager.check_content(user_input)

            if not result.is_safe:
                raise GuardrailViolationError(result)

        return {}

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
        import asyncio

        user_input = self._extract_last_user_message(state.get("messages", []))
        if user_input is None:
            return {}

        # Check if we're in an async context with a running loop
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # We're in an async context with a running loop
                # Use nest_asyncio to allow nested event loops
                # This enables calling asyncio.run() from within a running loop
                import nest_asyncio

                nest_asyncio.apply()
                result = asyncio.run(self.guardrail_manager.check_content(user_input))
            else:
                # Loop exists but not running - safe to use asyncio.run()
                result = asyncio.run(self.guardrail_manager.check_content(user_input))
        except RuntimeError:
            # No running loop - safe to use asyncio.run()
            result = asyncio.run(self.guardrail_manager.check_content(user_input))

        if not result.is_safe:
            raise GuardrailViolationError(result)

        return {}

    def modify_model_request(self, request: ModelRequest, state: dict[str, Any]) -> ModelRequest:
        """Guardrails don't modify model requests."""
        return request

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
        # Extract last AI message from state
        messages = state.get("messages", [])
        ai_output = self._extract_last_ai_message(messages)

        if ai_output is not None:
            # Check output content
            result = await self.guardrail_manager.check_content(GuardrailInput(input=None, output=ai_output))

            if not result.is_safe:
                raise GuardrailViolationError(result)

        return {}

    def after_model(self, state: dict[str, Any]) -> dict[str, Any]:
        """Check AI output after model invocation (synchronous wrapper)."""
        return {}

    def _extract_last_user_message(self, messages: list) -> str | None:
        """Extract the last user message from a list of messages.

        Searches backwards through messages to find the most recent HumanMessage.

        Args:
            messages: List of message objects

        Returns:
            Content of the last user message, or None if not found
        """
        for message in reversed(messages):
            if isinstance(message, HumanMessage) and message.content:
                return str(message.content)
        return None

    def _extract_last_ai_message(self, messages: list) -> str | None:
        """Extract the last AI message from a list of messages.

        Searches backwards through messages to find the most recent AIMessage.

        Args:
            messages: List of message objects

        Returns:
            Content of the last AI message, or None if not found
        """
        for message in reversed(messages):
            if isinstance(message, AIMessage) and message.content:
                return str(message.content)
        return None
