from dataclasses import dataclass

@dataclass
class SandboxExecutionResult:
    """Result of a sandbox code execution.

    Attributes:
        stdout: Standard output from the execution.
        stderr: Standard error from the execution.
        exit_code: Exit code (0 for success, non-zero for failure).
    """
    stdout: str
    stderr: str
    exit_code: int
