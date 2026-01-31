"""E2B Sandbox Runtime for PTC.

This module provides direct E2B SDK integration for sandbox code execution.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from e2b_code_interpreter import AsyncSandbox, OutputMessage

from aip_agents.sandbox.defaults import DEFAULT_PTC_PACKAGES, DEFAULT_PTC_TEMPLATE
from aip_agents.sandbox.types import SandboxExecutionResult
from aip_agents.sandbox.validation import validate_package_names
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

SANDBOX_NOT_INITIALIZED_ERROR = "Sandbox not initialized"


class E2BSandboxRuntime:
    """E2B Sandbox runtime for executing code in isolated environments.

    This runtime manages per-run sandbox lifecycle:
    - Create sandbox on first execute
    - Reuse sandbox for subsequent executes
    - Destroy sandbox on cleanup

    Example:
        runtime = E2BSandboxRuntime()
        result = await runtime.execute(
            code="print('Hello')",
            timeout=60.0,
            files={"tools/mcp.py": "# MCP client code"},
        )
        await runtime.cleanup()
    """

    def __init__(
        self,
        template: str | None = None,
        ptc_packages: list[str] | None = None,
    ) -> None:
        """Initialize E2B sandbox runtime.

        Args:
            template: Optional E2B template ID for custom sandbox environments.
            ptc_packages: Packages to install in sandbox. If None or empty, skip install.
        """
        self._template = template
        self._ptc_packages = ptc_packages
        self._sandbox: AsyncSandbox | None = None
        self._sandbox_created_with_template = False

    async def execute(
        self,
        code: str,
        *,
        timeout: float = 300.0,
        files: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        template: str | None = None,
    ) -> SandboxExecutionResult:
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
        # Create sandbox if not exists
        if self._sandbox is None:
            await self._create_sandbox(template or self._template)

        # Upload files if provided
        if files:
            await self._upload_files(files)

        # Execute code
        return await self._run_code(code, timeout, env)

    async def cleanup(self) -> None:
        """Destroy the sandbox and release resources."""
        if self._sandbox is not None:
            try:
                logger.info("Destroying E2B sandbox")
                await self._sandbox.kill()
            except Exception as e:
                logger.warning(f"Error destroying sandbox: {e}")
            finally:
                self._sandbox = None

        self._reset_async_transport()

    @property
    def is_active(self) -> bool:
        """Check if a sandbox is currently active."""
        return self._sandbox is not None

    def _reset_async_transport(self) -> None:
        try:
            from e2b.api.client_async import AsyncTransportWithLogger

            AsyncTransportWithLogger.singleton = None
        except Exception:
            return

    def _should_skip_default_ptc_install(self, template: str | None) -> bool:
        if not self._sandbox_created_with_template:
            return False

        if template != DEFAULT_PTC_TEMPLATE:
            return False

        return self._ptc_packages == list(DEFAULT_PTC_PACKAGES)

    async def _create_sandbox(self, template: str | None = None) -> None:
        """Create a new E2B sandbox.

        Implements canonical runtime rules:
        - If template provided, try creating sandbox with template
        - On any error, fall back to default sandbox (without template)
        - Install ptc_packages regardless of template usage (even after fallback)

        Note: Package installation occurs after sandbox creation, so fallback
        to default sandbox does not skip package installation.

        Args:
            template: Optional template ID.
        """
        logger.info(f"Creating E2B sandbox (template={template})")

        async def create_default_sandbox() -> None:
            self._sandbox = await AsyncSandbox.create()
            logger.info(f"E2B sandbox created (default): {self._sandbox.sandbox_id}")

        if template:
            try:
                self._sandbox = await AsyncSandbox.create(template=template)
                self._sandbox_created_with_template = True
                logger.info(f"E2B sandbox created: {self._sandbox.sandbox_id}")
            except Exception as e:
                logger.warning(f"Template creation failed ({template}): {e}")
                logger.info("Falling back to default sandbox")
                self._sandbox_created_with_template = False
                await create_default_sandbox()
        else:
            self._sandbox_created_with_template = False
            await create_default_sandbox()

        # Install ptc_packages if non-empty
        if self._ptc_packages:
            if self._should_skip_default_ptc_install(template):
                logger.info("Skipping PTC package install (default template already includes defaults)")
            else:
                await self._install_ptc_packages()

    async def _install_ptc_packages(self) -> None:
        """Install PTC packages in the sandbox."""
        if self._sandbox is None:
            raise RuntimeError(SANDBOX_NOT_INITIALIZED_ERROR)

        # Validate all packages before constructing command
        validate_package_names(self._ptc_packages)

        # Note: packages_str is safe because ptc_packages is a controlled list from
        # configuration, not user input. E2B SDK's commands.run() only accepts str,
        # not list, so string joining is required.
        packages_str = " ".join(self._ptc_packages)
        logger.info(f"Installing PTC packages in sandbox: {packages_str}")

        try:
            result = await self._sandbox.commands.run(
                f"pip install -q {packages_str}",
                timeout=120,
            )
        except Exception as e:
            logger.error(f"Error installing PTC packages: {e}")
            raise

        if result.exit_code != 0:
            logger.error(f"Failed to install PTC packages: {result.stderr}")
            raise RuntimeError(f"Failed to install PTC packages: {result.stderr}")

        logger.info("PTC packages installed successfully")

    async def _upload_files(self, files: dict[str, str]) -> None:
        """Upload files to the sandbox.

        Args:
            files: Mapping of path -> content.
        """
        if self._sandbox is None:
            raise RuntimeError(SANDBOX_NOT_INITIALIZED_ERROR)

        for path, content in files.items():
            logger.debug(f"Uploading file to sandbox: {path}")
            await self._sandbox.files.write(path, content)

    async def _run_code(
        self,
        code: str,
        timeout: float,
        env: dict[str, str] | None = None,
    ) -> SandboxExecutionResult:
        """Run code in the sandbox.

        Args:
            code: Python code to execute.
            timeout: Execution timeout in seconds.
            env: Environment variables.

        Returns:
            SandboxExecutionResult with execution output.
        """
        if self._sandbox is None:
            raise RuntimeError(SANDBOX_NOT_INITIALIZED_ERROR)

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def on_stdout(msg: OutputMessage) -> None:
            if hasattr(msg, "line"):
                stdout_lines.append(msg.line)

        def on_stderr(msg: OutputMessage) -> None:
            if hasattr(msg, "line"):
                stderr_lines.append(msg.line)

        try:
            execution = await self._sandbox.run_code(
                code=code,
                language="python",
                on_stdout=on_stdout,
                on_stderr=on_stderr,
                envs=env,
                timeout=timeout,
            )

            # Determine exit code
            exit_code = 0
            if execution.error:
                exit_code = 1
                # Add error to stderr
                error_msg = f"{execution.error.name}: {execution.error.value}"
                if execution.error.traceback:
                    error_msg = f"{execution.error.traceback}\n{error_msg}"
                stderr_lines.append(error_msg)

            return SandboxExecutionResult(
                stdout="\n".join(stdout_lines),
                stderr="\n".join(stderr_lines),
                exit_code=exit_code,
            )

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return SandboxExecutionResult(
                stdout="",
                stderr=str(e),
                exit_code=1,
            )
