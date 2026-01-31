"""Schemas for guardrail input, output, and configuration.

This module defines the data structures used throughout the guardrails system,
including input/output schemas and configuration objects.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class GuardrailMode(StrEnum):
    """Modes determining what content an engine checks."""

    INPUT_ONLY = "input_only"
    OUTPUT_ONLY = "output_only"
    INPUT_OUTPUT = "input_output"
    DISABLED = "disabled"


class GuardrailInput(BaseModel):
    """Input schema for guardrail checks.

    Attributes:
        input: User input content to check (queries, prompts, context)
        output: AI output content to check (responses, generated text)
    """

    model_config = ConfigDict(extra="forbid")

    input: str | None = None
    output: str | None = None


class GuardrailResult(BaseModel):
    """Result schema returned by guardrail engines and managers.

    Attributes:
        is_safe: Whether the content passed all checks
        reason: Explanation when content is blocked (None if safe)
        filtered_content: Cleaned/sanitized content if engine provides it
    """

    model_config = ConfigDict(extra="forbid")

    is_safe: bool
    reason: str | None = None
    filtered_content: str | None = None


class BaseGuardrailEngineConfig(BaseModel):
    """Base configuration for guardrail engines.

    Attributes:
        guardrail_mode: What content this engine should check
    """

    model_config = ConfigDict(extra="forbid")

    guardrail_mode: GuardrailMode = GuardrailMode.INPUT_OUTPUT
