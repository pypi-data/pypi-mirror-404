"""PTC helper module generation utilities."""

from __future__ import annotations

from aip_agents.ptc.template_utils import render_template

_TEMPLATE_PACKAGE = "aip_agents.ptc.templates"


def _generate_ptc_helper_module() -> str:
    """Generate the tools/ptc_helper.py discovery module.

    Returns:
        Python source code for the PTC helper module.
    """
    return render_template(_TEMPLATE_PACKAGE, "ptc_helper.py.template")
