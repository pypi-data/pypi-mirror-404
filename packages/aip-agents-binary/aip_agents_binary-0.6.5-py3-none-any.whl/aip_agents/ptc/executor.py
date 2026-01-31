"""PTC Executor implementations (MCP-only).

This module provides the sandboxed executor for Programmatic Tool Calling
with MCP tools.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aip_agents.mcp.client.base_mcp_client import BaseMCPClient
from aip_agents.ptc.exceptions import PTCToolError
from aip_agents.ptc.prompt_builder import PromptConfig
from aip_agents.sandbox.defaults import DEFAULT_PTC_PACKAGES, DEFAULT_PTC_TEMPLATE
from aip_agents.utils.logger import get_logger

# Lazy import to avoid circular dependencies
# These are only needed for PTCSandboxExecutor
try:
    from aip_agents.ptc.sandbox_bridge import build_sandbox_payload, wrap_ptc_code
    from aip_agents.sandbox.e2b_runtime import E2BSandboxRuntime
    from aip_agents.sandbox.types import SandboxExecutionResult

    _SANDBOX_DEPS_AVAILABLE = True
except ImportError:
    _SANDBOX_DEPS_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class PTCSandboxConfig:
    """Configuration for PTC sandbox executor (MCP-only).

    Attributes:
        enabled: Whether PTC is enabled. When False, PTC is disabled.
        default_tool_timeout: Default timeout per tool call in seconds.
        sandbox_template: Optional E2B sandbox template ID.
        sandbox_timeout: Sandbox execution timeout in seconds (hard cap/TTL).
        ptc_packages: List of packages to install in sandbox. None or empty list skips install.
        prompt: Prompt configuration for PTC usage guidance.
    """

    enabled: bool = False
    default_tool_timeout: float = 60.0
    sandbox_template: str | None = DEFAULT_PTC_TEMPLATE
    sandbox_timeout: float = 300.0
    ptc_packages: list[str] | None = field(default_factory=lambda: list(DEFAULT_PTC_PACKAGES))
    prompt: PromptConfig = field(default_factory=PromptConfig)


class PTCSandboxExecutor:
    r"""Executes PTC code inside an E2B sandbox (MCP-only).

    This executor is used for LLM-generated code that requires sandboxing.
    It builds a sandbox payload (MCP server config + generated tool modules)
    and executes the code using the E2B runtime.

    Example:
        runtime = E2BSandboxRuntime()
        executor = PTCSandboxExecutor(mcp_client, runtime)
        result = await executor.execute_code("from tools.yfinance import get_stock\nprint(get_stock('AAPL'))")
    """

    def __init__(
        self,
        mcp_client: BaseMCPClient,
        runtime: E2BSandboxRuntime,
        config: PTCSandboxConfig | None = None,
    ) -> None:
        """Initialize PTCSandboxExecutor.

        Args:
            mcp_client: The MCP client with configured servers.
            runtime: The E2B sandbox runtime instance.
            config: Optional sandbox executor configuration.

        Raises:
            ImportError: If sandbox dependencies are not available.
        """
        if not _SANDBOX_DEPS_AVAILABLE:
            raise ImportError(
                "Sandbox dependencies not available. "
                "PTCSandboxExecutor requires sandbox_bridge and e2b_runtime modules."
            )

        self._mcp_client = mcp_client
        self._runtime = runtime
        self._config = config or PTCSandboxConfig()

    async def execute_code(
        self,
        code: str,
    ) -> SandboxExecutionResult:
        """Execute code inside the sandbox with MCP access.

        This method:
        1. Builds the sandbox payload (MCP config + generated tool modules)
        2. Wraps the user code with necessary imports and setup
        3. Executes the code in the E2B sandbox
        4. Returns the execution result (stdout/stderr/exit_code)

        Args:
            code: Python code to execute in the sandbox.

        Returns:
            SandboxExecutionResult with stdout, stderr, and exit_code.

        Raises:
            PTCToolError: If sandbox execution fails.
        """
        try:
            logger.info("Building sandbox payload")
            payload = await build_sandbox_payload(
                self._mcp_client,
                self._config.default_tool_timeout,
            )

            logger.info("Wrapping PTC code")
            wrapped_code = wrap_ptc_code(code)

            logger.info(f"Executing code in sandbox (timeout: {self._config.sandbox_timeout}s)")
            result = await self._runtime.execute(
                code=wrapped_code,
                timeout=self._config.sandbox_timeout,
                files=payload.files if payload.files else None,
                env=payload.env,
                template=self._config.sandbox_template,
            )

            if result.exit_code == 0:
                logger.info("Sandbox execution completed successfully")
            else:
                logger.warning(f"Sandbox execution failed with exit code {result.exit_code}")

            return result

        except Exception as exc:
            logger.error(f"Sandbox execution failed: {exc}")
            raise PTCToolError(f"Sandbox execution failed: {exc}") from exc
