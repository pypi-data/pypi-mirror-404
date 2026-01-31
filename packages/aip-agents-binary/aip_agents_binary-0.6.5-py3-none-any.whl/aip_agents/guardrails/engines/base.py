"""Base interfaces and protocols for guardrail engines.

This module defines the base protocol that all guardrail engines must implement,
providing a consistent interface for content safety checking.

Authors:
    Reinhart Linanda (reinhart.linanda@gdplabs.id)
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from abc import ABC, abstractmethod
from typing import Protocol

from aip_agents.guardrails.schemas import (
    BaseGuardrailEngineConfig,
    GuardrailResult,
)


class GuardrailEngine(Protocol):
    """Protocol defining the interface for guardrail engines.

    All guardrail engines must implement this protocol to be compatible
    with GuardrailManager. Engines check content for safety violations.

    Attributes:
        config: Configuration for this engine's behavior
    """

    config: BaseGuardrailEngineConfig

    @abstractmethod
    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content for safety violations.

        Args:
            content: The user input content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
        ...  # pragma: no cover

    @abstractmethod
    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content for safety violations.

        Args:
            content: The AI output content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
        ...  # pragma: no cover

    @abstractmethod
    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""
        ...  # pragma: no cover


class BaseGuardrailEngine(ABC):
    """Abstract base class for guardrail engines.

    Provides common functionality and ensures proper configuration handling.
    Concrete engines should inherit from this class.
    """

    def __init__(self, config: BaseGuardrailEngineConfig | None = None) -> None:
        """Initialize the engine with configuration.

        Args:
            config: Engine configuration. Uses defaults if None provided.
        """
        self.config = config or BaseGuardrailEngineConfig()

    @abstractmethod
    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content for safety violations."""
        ...  # pragma: no cover

    @abstractmethod
    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content for safety violations."""
        ...  # pragma: no cover

    @abstractmethod
    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""
        ...  # pragma: no cover
