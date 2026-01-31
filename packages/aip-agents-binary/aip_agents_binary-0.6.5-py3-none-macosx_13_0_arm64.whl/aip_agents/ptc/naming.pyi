from _typeshed import Incomplete
from typing import Any

RESERVED_MODULE_NAMES: Incomplete
DEFAULT_EXAMPLE_PLACEHOLDER: str

def sanitize_module_name(name: str) -> str:
    """Sanitize server name for use as Python module name.

    Args:
        name: Original server name.

    Returns:
        Valid Python module name (lowercase, underscored).
    """
def sanitize_module_name_with_reserved(name: str) -> str:
    """Sanitize server name, avoiding reserved module names.

    If the sanitized name collides with a reserved name (e.g., ptc_helper),
    appends '_mcp' suffix to avoid collision.

    Args:
        name: Original server name.

    Returns:
        Valid Python module name that does not collide with reserved names.
    """
def sanitize_function_name(name: str) -> str:
    """Sanitize tool name for use as Python function name.

    Args:
        name: Original tool name.

    Returns:
        Valid Python function name (lowercase, underscored).
    """
def sanitize_param_name(name: str) -> str:
    """Sanitize parameter name for use as Python parameter.

    Args:
        name: Original parameter name (e.g., userId, user-id).

    Returns:
        Valid Python parameter name (lowercase, underscored).
    """
def json_type_to_python(json_type: str | list) -> str:
    """Convert JSON schema type to Python type hint.

    Args:
        json_type: JSON schema type.

    Returns:
        Python type hint string.
    """
def schema_to_params(schema: dict[str, Any]) -> str:
    """Convert JSON schema to Python function parameters.

    Args:
        schema: JSON schema for tool input.

    Returns:
        Function parameter string.
    """
def example_value_from_schema(prop_schema: dict[str, Any], default_placeholder: str = ...) -> str:
    """Return an example value for a schema property.

    Prefers schema-provided examples, defaults, or enums, and falls back
    to type-based placeholders.

    Args:
        prop_schema: Property schema from JSON schema.
        default_placeholder: Placeholder value to use for unknown types.

    Returns:
        Example value as a Python literal string.
    """
