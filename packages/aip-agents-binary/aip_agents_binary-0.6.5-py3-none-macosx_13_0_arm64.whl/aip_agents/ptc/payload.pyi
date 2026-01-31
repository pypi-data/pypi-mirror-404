from dataclasses import dataclass, field

@dataclass
class SandboxPayload:
    """Payload to upload to the sandbox for PTC execution.

    Attributes:
        files: Mapping of file path -> content to upload (static bundle).
        per_run_files: Mapping of file path -> content to upload on every run.
            These files are always re-uploaded, even when the static bundle is cached.
        env: Environment variables to set in the sandbox.
    """
    files: dict[str, str] = field(default_factory=dict)
    per_run_files: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
