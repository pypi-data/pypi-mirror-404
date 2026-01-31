from _typeshed import Incomplete
from aip_agents.mcp.client.base_mcp_client import BaseMCPClient as BaseMCPClient
from aip_agents.ptc.exceptions import PTCToolError as PTCToolError
from aip_agents.ptc.prompt_builder import PromptConfig as PromptConfig
from aip_agents.ptc.sandbox_bridge import build_sandbox_payload as build_sandbox_payload, wrap_ptc_code as wrap_ptc_code
from aip_agents.sandbox.defaults import DEFAULT_PTC_PACKAGES as DEFAULT_PTC_PACKAGES, DEFAULT_PTC_TEMPLATE as DEFAULT_PTC_TEMPLATE
from aip_agents.sandbox.e2b_runtime import E2BSandboxRuntime as E2BSandboxRuntime
from aip_agents.sandbox.types import SandboxExecutionResult as SandboxExecutionResult
from aip_agents.utils.logger import get_logger as get_logger
from dataclasses import dataclass, field

logger: Incomplete

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
    enabled: bool = ...
    default_tool_timeout: float = ...
    sandbox_template: str | None = ...
    sandbox_timeout: float = ...
    ptc_packages: list[str] | None = field(default_factory=Incomplete)
    prompt: PromptConfig = field(default_factory=PromptConfig)

class PTCSandboxExecutor:
    '''Executes PTC code inside an E2B sandbox (MCP-only).

    This executor is used for LLM-generated code that requires sandboxing.
    It builds a sandbox payload (MCP server config + generated tool modules)
    and executes the code using the E2B runtime.

    Example:
        runtime = E2BSandboxRuntime()
        executor = PTCSandboxExecutor(mcp_client, runtime)
        result = await executor.execute_code("from tools.yfinance import get_stock\\nprint(get_stock(\'AAPL\'))")
    '''
    def __init__(self, mcp_client: BaseMCPClient, runtime: E2BSandboxRuntime, config: PTCSandboxConfig | None = None) -> None:
        """Initialize PTCSandboxExecutor.

        Args:
            mcp_client: The MCP client with configured servers.
            runtime: The E2B sandbox runtime instance.
            config: Optional sandbox executor configuration.

        Raises:
            ImportError: If sandbox dependencies are not available.
        """
    async def execute_code(self, code: str) -> SandboxExecutionResult:
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
