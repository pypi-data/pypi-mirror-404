"""Tool for E2B Cloud Sandbox code execution.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
    Komang Elang Surya Prawira (komang.e.s.prawira@gdplabs.id)
"""

import asyncio
import time
from http import HTTPStatus
from typing import Any

import requests
from e2b_code_interpreter import Sandbox
from gllm_inference.schema import Attachment
from gllm_tools.code_interpreter.code_sandbox.e2b_sandbox import E2BSandbox
from gllm_tools.code_interpreter.code_sandbox.models import ExecutionResult, ExecutionStatus
from gllm_tools.code_interpreter.code_sandbox.utils import calculate_duration_ms

from aip_agents.tools.code_sandbox.constant import DATA_FILE_PATH
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class SandboxFileWatcher:
    """File watcher for monitoring file creation in sandbox environments."""

    def __init__(self, sandbox: Any):
        """Initialize the file watcher with a sandbox instance.

        Args:
            sandbox (Any): The sandbox instance to monitor.
        """
        self.sandbox = sandbox
        self._created_files: list[str] = []
        self._watchers_with_dirs: list[tuple[Any, str]] = []

    def setup_monitoring(self) -> None:
        """Set up filesystem watchers for monitoring file creation.

        Note: /tmp/output is a sandbox-isolated directory, not a shared system /tmp.
        This directory is scoped to the E2B sandbox instance and is safe for use.
        """
        output_dirs = [
            "/tmp/output",  # NOSONAR: python:S5443 - Sandbox-isolated directory, safe for temp outputs
        ]

        self._watchers_with_dirs = []

        for output_dir in output_dirs:
            try:
                # Create the directory if it doesn't exist
                # NOSONAR: python:S5443 - Sandbox-isolated directory, safe for use
                self.sandbox.files.make_dir(output_dir)

                # Watch the directory for new files
                watcher = self.sandbox.files.watch_dir(output_dir, recursive=True)
                self._watchers_with_dirs.append((watcher, output_dir))

                logger.debug(f"Set up file watcher for directory: {output_dir}")

            except Exception as e:
                logger.debug(f"Could not set up watcher for {output_dir}: {str(e)}")
                continue

    def _process_single_event(self, event: Any, output_dir: str) -> None:
        """Process a single filesystem event and add created files to the list.

        Args:
            event: The filesystem event to process.
            output_dir: The directory being watched.
        """
        if not (hasattr(event, "name") and hasattr(event, "type")):
            return

        if str(event.type) != "FilesystemEventType.CREATE":
            logger.debug(f"Ignored filesystem event: {event.type} - {event.name}")
            return

        # Construct full path by combining output_dir with filename
        full_path = f"{output_dir}/{event.name}".replace("//", "/")
        logger.info(f"New file created: {full_path}")
        if full_path not in self._created_files:
            self._created_files.append(full_path)

    def _process_watcher_events(self, watcher: Any, output_dir: str) -> None:
        """Process all events from a single watcher.

        Args:
            watcher: The filesystem watcher instance.
            output_dir: The directory being watched.
        """
        try:
            events = watcher.get_new_events()
            for event in events:
                logger.debug(f"Event: {event}")
                self._process_single_event(event, output_dir)
            watcher.stop()
        except Exception as e:
            logger.debug(f"Error processing watcher events: {str(e)}")

    async def process_events(self) -> None:
        """Process filesystem events from watchers and update created files list."""
        # Poll for file system events (allow time for events to be generated)
        await asyncio.sleep(0.5)

        for watcher, output_dir in self._watchers_with_dirs:
            self._process_watcher_events(watcher, output_dir)

    def reset_created_files(self) -> None:
        """Reset the list of created files."""
        self._created_files = []

    def get_created_files(self) -> list[str]:
        """Get the list of files created during monitoring.

        Returns:
            list[str]: List of file paths that were created.
        """
        return self._created_files.copy()


class MyE2BCloudSandbox(E2BSandbox):
    """Extended E2B sandbox with filesystem monitoring capabilities.

    Use `create()` in production to build a fully initialized sandbox wrapper.
    Direct construction is intentionally blocked to prevent partially initialized
    instances that lack the underlying E2B sandbox clients.
    """

    def __init__(self, language: str = "python", *, _unsafe_allow_init: bool = False) -> None:
        """Initialize the sandbox wrapper.

        Args:
            language (str): Language to execute inside the sandbox.
            _unsafe_allow_init (bool): Escape hatch for tests/mocks only.

        Raises:
            RuntimeError: When instantiated directly without `create()`.
        """
        if not _unsafe_allow_init:
            raise RuntimeError("Use MyE2BCloudSandbox.create(...) to initialize a sandbox instance.")
        super().__init__(language=language)
        self.file_watcher: SandboxFileWatcher | None = None

    @classmethod
    async def create(
        cls,
        api_key: str,
        domain: str | None = None,
        template: str | None = None,
        language: str = "python",
        additional_packages: list[str] | None = None,
        **kwargs: Any,
    ) -> "MyE2BCloudSandbox":
        """Create a fully initialized sandbox wrapper.

        This is the supported construction path for production usage. It wires
        the E2B sandbox instance and its filesystem/command clients, then
        installs language dependencies.
        """
        sandbox = Sandbox.create(api_key=api_key, domain=domain, template=template, **kwargs)

        instance = cls(language=language, _unsafe_allow_init=True)
        instance.sandbox = sandbox
        instance.files = sandbox.files
        instance.commands = sandbox.commands
        instance.additional_packages = additional_packages or []

        instance._install_language_dependencies()

        return instance

    async def execute_code(
        self,
        code: str,
        timeout: int = 30,
        files: list[Attachment] | None = None,
        **kwargs: Any,
    ) -> ExecutionResult:
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
        if not self.sandbox or not self.files or not self.commands:
            raise RuntimeError("Sandbox is not initialized")

        start_time = time.time()
        try:
            # Initialize filesystem monitoring
            self.file_watcher = SandboxFileWatcher(self.sandbox)
            self.file_watcher.reset_created_files()
            self.file_watcher.setup_monitoring()

            self._upload_files(files)
            # Pre-populate the variable `df` for direct use in the code
            if files:
                logger.info("Pre-populating the variable `df` with the data from the file.")
                self.sandbox.run_code(
                    f"import pandas as pd; df = pd.read_csv('{DATA_FILE_PATH}')",
                    language=self.language,
                    timeout=timeout,
                )
            execution = self.sandbox.run_code(code, language=self.language, timeout=timeout)
            duration_ms = calculate_duration_ms(start_time)
            status = ExecutionStatus.ERROR if execution.error else ExecutionStatus.SUCCESS

            # Process filesystem events
            if self.file_watcher:
                await self.file_watcher.process_events()
                created_files_count = len(self.file_watcher.get_created_files())
                logger.info(f"File monitoring detected {created_files_count} newly created files")

            # Fix: Convert execution.error to string
            return ExecutionResult.create(
                status=status,
                code=code,
                stdout=("\n".join(execution.logs.stdout) if execution.logs and execution.logs.stdout else ""),
                stderr=("\n".join(execution.logs.stderr) if execution.logs and execution.logs.stderr else ""),
                error=(str(execution.error) if execution.error else ""),  # Convert to string here
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.warning(f"Error executing code in {self.language} sandbox: {str(e)}")
            return ExecutionResult.create(
                status=ExecutionStatus.ERROR,
                code=code,
                error=str(e),
                duration_ms=calculate_duration_ms(start_time),
            )

    def get_created_files(self) -> list[str]:
        """Get the list of files created during the last monitored execution.

        Returns:
            list[str]: List of file paths that were created.
        """
        if self.file_watcher:
            return self.file_watcher.get_created_files()
        return []

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
        if not self.sandbox:
            raise RuntimeError("Sandbox is not initialized")

        try:
            if hasattr(self.sandbox, "download_url"):
                logger.info(f"Downloading {file_path} via download_url method")

                try:
                    url = self.sandbox.download_url(file_path)
                except Exception as e:
                    logger.warning(f"Failed to get download URL: {str(e)}")
                else:
                    logger.debug(f"Got download URL: {url}")

                    try:
                        response = requests.get(url, timeout=30)
                    except Exception as e:
                        logger.warning(f"URL download failed with error: {str(e)}")
                    else:
                        if response.status_code == HTTPStatus.OK:
                            content = response.content
                            logger.info(f"Successfully downloaded {len(content)} bytes via URL")
                            return content
                        logger.warning(f"URL download failed with status {response.status_code}")

            if self.files:
                logger.info(f"Downloading {file_path} via filesystem API")
                content = self.files.read(file_path, format="bytes")
                return bytes(content)

            return None

        except Exception as e:
            logger.warning(f"Failed to download file {file_path}: {str(e)}")
            return None
