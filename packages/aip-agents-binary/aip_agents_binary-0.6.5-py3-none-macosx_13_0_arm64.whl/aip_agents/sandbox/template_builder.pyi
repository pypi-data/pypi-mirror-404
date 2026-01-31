from _typeshed import Incomplete
from aip_agents.sandbox.validation import validate_package_names as validate_package_names
from aip_agents.utils.logger import get_logger as get_logger
from e2b import Template

logger: Incomplete

def create_ptc_template(base_template: str, ptc_packages: list[str] | None) -> Template:
    '''Create a PTC template definition based on a base template.

    Args:
        base_template: Base template alias to build from (e.g., "code-interpreter-v1").
        ptc_packages: List of packages to install in the template.
            If None or empty, skips pip install step.

    Returns:
        Template: A configured template ready to be built.
    '''
def ensure_ptc_template(template_id: str, base_template: str, ptc_packages: list[str] | None, force_rebuild: bool = False) -> str | None:
    '''Ensure a PTC sandbox template exists, creating it if necessary.

    This is an explicit helper that apps can call at startup to ensure the
    template exists. It is never run implicitly by the SDK.

    Args:
        template_id: Unique alias for the template (e.g., "aip-agents-ptc-v1").
        base_template: Base template alias to build from
            (e.g., "code-interpreter-v1").
        ptc_packages: List of packages to install in the template.
            If None or empty, skips pip install step.
        force_rebuild: If True, rebuild even if alias exists.

    Returns:
        The template_id on success, None if creation failed.
        Never raises exceptions.
    '''
