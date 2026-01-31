from _typeshed import Incomplete
from abc import ABC, abstractmethod
from aip_agents.guardrails.schemas import BaseGuardrailEngineConfig as BaseGuardrailEngineConfig, GuardrailResult as GuardrailResult
from typing import Protocol

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
    @abstractmethod
    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content for safety violations.

        Args:
            content: The AI output content to check

        Returns:
            GuardrailResult indicating if content is safe
        """
    @abstractmethod
    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""

class BaseGuardrailEngine(ABC):
    """Abstract base class for guardrail engines.

    Provides common functionality and ensures proper configuration handling.
    Concrete engines should inherit from this class.
    """
    config: Incomplete
    def __init__(self, config: BaseGuardrailEngineConfig | None = None) -> None:
        """Initialize the engine with configuration.

        Args:
            config: Engine configuration. Uses defaults if None provided.
        """
    @abstractmethod
    async def check_input(self, content: str) -> GuardrailResult:
        """Check user input content for safety violations."""
    @abstractmethod
    async def check_output(self, content: str) -> GuardrailResult:
        """Check AI output content for safety violations."""
    @abstractmethod
    def model_dump(self) -> dict:
        """Serialize engine configuration into a JSON-compatible dictionary."""
