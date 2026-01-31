from aip_agents.ptc.naming import sanitize_function_name as sanitize_function_name
from typing import Any

DOC_DESC_LIMIT: int
DOC_PARAM_DESC_LIMIT: int

def json_type_to_display(json_type: Any) -> str:
    """Convert JSON type to display string.

    Args:
        json_type: JSON schema type.

    Returns:
        Human-readable type string.
    """
def trim_text(text: str | None, limit: int) -> str:
    """Trim text to limit with ellipsis if needed.

    Args:
        text: Text to trim.
        limit: Maximum length before trimming.

    Returns:
        Trimmed text.
    """
def render_tool_doc(func_name: str, signature: str, description: str, schema: dict[str, Any], is_stub: bool = False, example_code: str | None = None, example_heading: str = '## Example') -> str:
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
