from _typeshed import Incomplete
from aip_agents.tools.code_sandbox.constant import DATA_FILE_PATH as DATA_FILE_PATH
from aip_agents.utils.logger import get_logger as get_logger
from gllm_inference.schema import Attachment as Attachment
from gllm_tools.code_interpreter.code_sandbox.e2b_sandbox import E2BSandbox
from gllm_tools.code_interpreter.code_sandbox.models import ExecutionResult
from typing import Any

logger: Incomplete

class SandboxFileWatcher:
    """File watcher for monitoring file creation in sandbox environments."""
    sandbox: Incomplete
    def __init__(self, sandbox: Any) -> None:
        """Initialize the file watcher with a sandbox instance.

        Args:
            sandbox (Any): The sandbox instance to monitor.
        """
    def setup_monitoring(self) -> None:
        """Set up filesystem watchers for monitoring file creation.

        Note: /tmp/output is a sandbox-isolated directory, not a shared system /tmp.
        This directory is scoped to the E2B sandbox instance and is safe for use.
        """
    async def process_events(self) -> None:
        """Process filesystem events from watchers and update created files list."""
    def reset_created_files(self) -> None:
        """Reset the list of created files."""
    def get_created_files(self) -> list[str]:
        """Get the list of files created during monitoring.

        Returns:
            list[str]: List of file paths that were created.
        """

class MyE2BCloudSandbox(E2BSandbox):
    """Extended E2B sandbox with filesystem monitoring capabilities.

    Use `create()` in production to build a fully initialized sandbox wrapper.
    Direct construction is intentionally blocked to prevent partially initialized
    instances that lack the underlying E2B sandbox clients.
    """
    file_watcher: SandboxFileWatcher | None
    def __init__(self, language: str = 'python', *, _unsafe_allow_init: bool = False) -> None:
        """Initialize the sandbox wrapper.

        Args:
            language (str): Language to execute inside the sandbox.
            _unsafe_allow_init (bool): Escape hatch for tests/mocks only.

        Raises:
            RuntimeError: When instantiated directly without `create()`.
        """
    @classmethod
    async def create(cls, api_key: str, domain: str | None = None, template: str | None = None, language: str = 'python', additional_packages: list[str] | None = None, **kwargs: Any) -> MyE2BCloudSandbox:
        """Create a fully initialized sandbox wrapper.

        This is the supported construction path for production usage. It wires
        the E2B sandbox instance and its filesystem/command clients, then
        installs language dependencies.
        """
    async def execute_code(self, code: str, timeout: int = 30, files: list[Attachment] | None = None, **kwargs: Any) -> ExecutionResult:
        """Execute code in the E2B Cloud sandbox with filesystem monitoring.

        This override fixes the Pydantic validation error by ensuring execution.error
        is converted to string. Always enables filesystem monitoring to track
        created files.

        Args:
            code (str): The code to execute.
            timeout (int, optional): Maximum execution time in seconds. Defaults to 30.
            files (list[Attachment] | None, optional): List of Attachment objects with file details. Defaults to None.
            **kwargs (Any): Additional execution parameters.

        Returns:
            ExecutionResult: Structured result of the execution.

        Raises:
            RuntimeError: If sandbox is not initialized.
        """
    def get_created_files(self) -> list[str]:
        """Get the list of files created during the last monitored execution.

        Returns:
            list[str]: List of file paths that were created.
        """
    def download_file(self, file_path: str) -> bytes | None:
        """Download file content from the sandbox.

        Uses download_url when available to avoid binary corruption issues.
        Falls back to the filesystem API when download_url fails or is unavailable.

        Args:
            file_path (str): Path to the file in the sandbox.

        Returns:
            bytes | None: File content as bytes, or None if download fails.

        Raises:
            RuntimeError: If sandbox is not initialized.
        """
