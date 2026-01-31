"""Template builder for PTC sandbox templates.

This module provides utilities for creating and managing E2B sandbox templates
for programmatic tool calling (PTC) environments.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from e2b import Template, default_build_logger

from aip_agents.sandbox.validation import validate_package_names
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


def create_ptc_template(base_template: str, ptc_packages: list[str] | None) -> Template:
    """Create a PTC template definition based on a base template.

    Args:
        base_template: Base template alias to build from (e.g., "code-interpreter-v1").
        ptc_packages: List of packages to install in the template.
            If None or empty, skips pip install step.

    Returns:
        Template: A configured template ready to be built.
    """
    logger.info(f"Creating template from base: {base_template}")
    template = Template().from_template(base_template)

    if ptc_packages:
        # Validate all packages before constructing command
        validate_package_names(ptc_packages)

        # Note: packages_str is safe because ptc_packages is a controlled list from
        # configuration, not user input. Template.run_cmd() only accepts str.
        packages_str = " ".join(ptc_packages)
        logger.info(f"Installing packages: {packages_str}")
        template.run_cmd(f"pip install -q {packages_str}")

    return template


def _template_exists(template_id: str) -> bool:
    """Check if a template alias exists.

    Args:
        template_id: The template alias to check.

    Returns:
        bool: True if alias exists, False otherwise.
    """
    try:
        return Template.alias_exists(template_id)
    except Exception:
        logger.warning(f"Template alias check failed for: {template_id}")
        return False


def _build_template(template: Template, template_id: str) -> bool:
    """Build a template with the given alias.

    Args:
        template: The template to build.
        template_id: The alias to assign to the built template.

    Returns:
        bool: True if build succeeded, False otherwise.
    """
    try:
        logger.info(f"Building template: {template_id}")
        Template.build(
            template,
            alias=template_id,
            on_build_logs=default_build_logger(),
        )
        logger.info(f"Template built successfully: {template_id}")
        return True
    except Exception as e:
        logger.warning(f"Template build failed for {template_id}: {e}")
        return False


def ensure_ptc_template(
    template_id: str,
    base_template: str,
    ptc_packages: list[str] | None,
    force_rebuild: bool = False,
) -> str | None:
    """Ensure a PTC sandbox template exists, creating it if necessary.

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
    """
    # Fast path: template already exists and we're not forcing rebuild
    if not force_rebuild and _template_exists(template_id):
        logger.info(f"Template already exists: {template_id}")
        return template_id

    # Create and build the template
    try:
        template = create_ptc_template(base_template, ptc_packages)
    except Exception as e:
        logger.warning(f"Template creation failed for {template_id}: {e}")
        return None

    # Build the template
    is_success = _build_template(template, template_id)
    if is_success:
        return template_id

    # Build failed. Check if template exists anyway (race condition: another
    # process may have built it while we were trying)
    if _template_exists(template_id):
        logger.info(f"Template already exists after failed build: {template_id}")
        return template_id

    return None
