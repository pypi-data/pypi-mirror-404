"""GuardrailManager for orchestrating multiple guardrail engines.

This module provides the GuardrailManager class that coordinates multiple
guardrail engines with fail-fast behavior.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aip_agents.guardrails.schemas import GuardrailInput, GuardrailMode, GuardrailResult

if TYPE_CHECKING:
    from aip_agents.guardrails.engines.base import GuardrailEngine


class GuardrailManager:
    """Orchestrates multiple guardrail engines with fail-fast behavior.

    The manager accepts one or more guardrail engines and runs them in sequence.
    If any engine reports unsafe content, execution stops immediately (fail-fast)
    and returns the violation result.

    Attributes:
        engines: List of guardrail engines to orchestrate
    """

    def __init__(
        self,
        engine: GuardrailEngine | list[GuardrailEngine] | None = None,
        engines: list[GuardrailEngine] | None = None,
    ) -> None:
        """Initialize the GuardrailManager.

        Args:
            engine: Single guardrail engine to use
            engines: List of guardrail engines to use

        Raises:
            ValueError: If both engine and engines are provided
        """
        self.enabled = True
        if engine is not None and engines is not None:
            raise ValueError("Cannot specify both 'engine' and 'engines'")

        if engine is not None:
            if isinstance(engine, list):
                self.engines = engine
            else:
                self.engines = [engine]
        elif engines is not None:
            self.engines = engines
        else:
            self.engines = []

    def model_dump(self) -> dict[str, Any]:
        """Serialize manager configuration into a JSON-compatible dictionary."""
        return {
            "enabled": self.enabled,
            "engines": [engine.model_dump() for engine in self.engines],
        }

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
        # Normalize input to GuardrailInput
        guardrail_input = self._normalize_content(content)

        # Execute engines in order (fail-fast on first unsafe result)
        for engine in self.engines:
            result = await self._check_engine(engine, guardrail_input)
            if result is not None:
                return result

        # All engines passed
        return GuardrailResult(is_safe=True, reason=None, filtered_content=None)

    @staticmethod
    def _normalize_content(content: str | GuardrailInput) -> GuardrailInput:
        """Normalize content input to GuardrailInput.

        Args:
            content: Content to normalize

        Returns:
            GuardrailInput object
        """
        if isinstance(content, str):
            return GuardrailInput(input=content, output=None)
        return content

    async def _check_engine(self, engine: GuardrailEngine, guardrail_input: GuardrailInput) -> GuardrailResult | None:
        """Check content against a single engine.

        Args:
            engine: The guardrail engine to check against
            guardrail_input: The content to check

        Returns:
            GuardrailResult if unsafe content detected, None if safe
        """
        engine_mode = engine.config.guardrail_mode

        # Skip disabled engines
        if engine_mode == GuardrailMode.DISABLED:
            return None

        if self._should_check_input(engine_mode, guardrail_input) and guardrail_input.input is not None:
            result = await engine.check_input(guardrail_input.input)
            if not result.is_safe:
                return result

        if self._should_check_output(engine_mode, guardrail_input) and guardrail_input.output is not None:
            result = await engine.check_output(guardrail_input.output)
            if not result.is_safe:
                return result

        return None

    @staticmethod
    def _should_check_input(engine_mode: GuardrailMode, guardrail_input: GuardrailInput) -> bool:
        """Determine if input should be checked based on engine mode.

        Args:
            engine_mode: The guardrail mode of the engine
            guardrail_input: The content to check

        Returns:
            True if input should be checked, False otherwise
        """
        return guardrail_input.input is not None and engine_mode in (
            GuardrailMode.INPUT_ONLY,
            GuardrailMode.INPUT_OUTPUT,
        )

    @staticmethod
    def _should_check_output(engine_mode: GuardrailMode, guardrail_input: GuardrailInput) -> bool:
        """Determine if output should be checked based on engine mode.

        Args:
            engine_mode: The guardrail mode of the engine
            guardrail_input: The content to check

        Returns:
            True if output should be checked, False otherwise
        """
        return guardrail_input.output is not None and engine_mode in (
            GuardrailMode.OUTPUT_ONLY,
            GuardrailMode.INPUT_OUTPUT,
        )
