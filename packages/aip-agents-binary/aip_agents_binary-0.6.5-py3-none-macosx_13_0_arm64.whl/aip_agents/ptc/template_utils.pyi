from collections.abc import Mapping

def render_template(package: str, template_name: str, values: Mapping[str, str] | None = None) -> str:
    """Render a template from package resources with optional substitutions.

    Args:
        package: Package path containing the template.
        template_name: Template filename.
        values: Optional mapping of template variables.

    Returns:
        Rendered template content.
    """
