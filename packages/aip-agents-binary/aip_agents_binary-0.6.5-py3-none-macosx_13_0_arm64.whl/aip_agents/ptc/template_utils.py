"""Template rendering helpers for PTC payloads.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Mapping
from importlib import resources
from string import Template


def render_template(
    package: str,
    template_name: str,
    values: Mapping[str, str] | None = None,
) -> str:
    """Render a template from package resources with optional substitutions.

    Args:
        package: Package path containing the template.
        template_name: Template filename.
        values: Optional mapping of template variables.

    Returns:
        Rendered template content.
    """
    template_file = resources.files(package).joinpath(template_name)
    template_text = template_file.read_text(encoding="utf-8")
    if not values:
        return template_text
    return Template(template_text).substitute(values)
