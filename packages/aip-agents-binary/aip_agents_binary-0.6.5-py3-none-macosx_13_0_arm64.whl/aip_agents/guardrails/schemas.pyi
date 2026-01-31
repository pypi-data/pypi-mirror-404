from _typeshed import Incomplete
from enum import StrEnum
from pydantic import BaseModel

class GuardrailMode(StrEnum):
    """Modes determining what content an engine checks."""
    INPUT_ONLY: str
    OUTPUT_ONLY: str
    INPUT_OUTPUT: str
    DISABLED: str

class GuardrailInput(BaseModel):
    """Input schema for guardrail checks.

    Attributes:
        input: User input content to check (queries, prompts, context)
        output: AI output content to check (responses, generated text)
    """
    model_config: Incomplete
    input: str | None
    output: str | None

class GuardrailResult(BaseModel):
    """Result schema returned by guardrail engines and managers.

    Attributes:
        is_safe: Whether the content passed all checks
        reason: Explanation when content is blocked (None if safe)
        filtered_content: Cleaned/sanitized content if engine provides it
    """
    model_config: Incomplete
    is_safe: bool
    reason: str | None
    filtered_content: str | None

class BaseGuardrailEngineConfig(BaseModel):
    """Base configuration for guardrail engines.

    Attributes:
        guardrail_mode: What content this engine should check
    """
    model_config: Incomplete
    guardrail_mode: GuardrailMode
