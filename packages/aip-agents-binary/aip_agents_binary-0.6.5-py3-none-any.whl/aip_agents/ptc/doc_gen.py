"""Documentation generation utilities for PTC.

Shared constants and helpers for generating tool documentation in sandbox payloads.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from typing import Any

from aip_agents.ptc.naming import sanitize_function_name

# Documentation limits (fixed constants per plan)
DOC_DESC_LIMIT = 120  # Tool description trim limit
DOC_PARAM_DESC_LIMIT = 80  # Parameter description trim limit


def json_type_to_display(json_type: Any) -> str:
    """Convert JSON type to display string.

    Args:
        json_type: JSON schema type.

    Returns:
        Human-readable type string.
    """
    if isinstance(json_type, list):
        return "any"
    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
        "null": "None",
    }
    return type_map.get(str(json_type), "any")


def trim_text(text: str | None, limit: int) -> str:
    """Trim text to limit with ellipsis if needed.

    Args:
        text: Text to trim.
        limit: Maximum length before trimming.

    Returns:
        Trimmed text.
    """
    if not text:
        return ""
    if len(text) > limit:
        return text[:limit] + "..."
    return text


def render_tool_doc(
    func_name: str,
    signature: str,
    description: str,
    schema: dict[str, Any],
    is_stub: bool = False,
    example_code: str | None = None,
    example_heading: str = "## Example",
) -> str:
    """Render markdown documentation for a tool.

    Args:
        func_name: Sanitized function name.
        signature: Full function signature.
        description: Tool description.
        schema: Input schema for parameters.
        is_stub: Whether this is a stub documentation.
        example_code: Optional example code block content (without ```python).
        example_heading: Heading for the example section.

    Returns:
        Markdown documentation string.
    """
    if is_stub:
        desc = "Details unavailable because tool definitions are not loaded yet."
    else:
        desc = trim_text(description, DOC_DESC_LIMIT) or "No description available."

    lines = [
        f"# {func_name}",
        "",
        f"**Description:** {desc}",
        "",
        f"**Signature:** `{signature}`",
        "",
    ]

    # Add parameters section
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    if properties:
        lines.append("## Parameters")
        lines.append("")
        for prop_name, prop_schema in sorted(properties.items()):
            safe_param = sanitize_function_name(prop_name)
            prop_type = json_type_to_display(prop_schema.get("type", "any"))
            is_required = "required" if prop_name in required else "optional"

            # Trim param description
            raw_param_desc = prop_schema.get("description", "")
            param_desc = trim_text(raw_param_desc, DOC_PARAM_DESC_LIMIT)

            lines.append(f"- **{safe_param}** ({prop_type}, {is_required}): {param_desc}")
        lines.append("")

    # Add example section
    if example_code:
        lines.append(example_heading)
        lines.append("")
        lines.append("```python")
        lines.append(example_code)
        lines.append("```")

    return "\n".join(lines)
