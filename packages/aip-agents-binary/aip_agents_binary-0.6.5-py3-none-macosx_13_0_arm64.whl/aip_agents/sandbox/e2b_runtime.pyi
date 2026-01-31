from _typeshed import Incomplete
from aip_agents.sandbox.defaults import DEFAULT_PTC_PACKAGES as DEFAULT_PTC_PACKAGES, DEFAULT_PTC_TEMPLATE as DEFAULT_PTC_TEMPLATE
from aip_agents.sandbox.types import SandboxExecutionResult as SandboxExecutionResult
from aip_agents.sandbox.validation import validate_package_names as validate_package_names
from aip_agents.utils.logger import get_logger as get_logger

logger: Incomplete
SANDBOX_NOT_INITIALIZED_ERROR: str

class E2BSandboxRuntime:
    '''E2B Sandbox runtime for executing code in isolated environments.

    This runtime manages per-run sandbox lifecycle:
    - Create sandbox on first execute
    - Reuse sandbox for subsequent executes
    - Destroy sandbox on cleanup

    Example:
        runtime = E2BSandboxRuntime()
        result = await runtime.execute(
            code="print(\'Hello\')",
            timeout=60.0,
            files={"tools/mcp.py": "# MCP client code"},
        )
        await runtime.cleanup()
    '''
    def __init__(self, template: str | None = None, ptc_packages: list[str] | None = None) -> None:
        """Initialize E2B sandbox runtime.

        Args:
            template: Optional E2B template ID for custom sandbox environments.
            ptc_packages: Packages to install in sandbox. If None or empty, skip install.
        """
    async def execute(self, code: str, *, timeout: float = 300.0, files: dict[str, str] | None = None, env: dict[str, str] | None = None, template: str | None = None) -> SandboxExecutionResult:
        """Execute code inside the sandbox.

        Args:
            code: Python code to execute.
            timeout: Execution timeout in seconds.
            files: Files to upload to the sandbox (path -> content).
            env: Environment variables to set.
            template: Optional template override for this execution.

        Returns:
            SandboxExecutionResult with stdout, stderr, and exit_code.
        """
    async def cleanup(self) -> None:
        """Destroy the sandbox and release resources."""
    @property
    def is_active(self) -> bool:
        """Check if a sandbox is currently active."""
