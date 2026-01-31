"""Naming utilities for PTC module.

Shared naming helpers for sanitizing module, function, and parameter names
used in sandbox code generation and prompt building.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import keyword
import re
from typing import Any

# Reserved module names that cannot be used for server packages.
RESERVED_MODULE_NAMES = frozenset({"ptc_helper", "mcp_client"})

# Default placeholder for example values.
DEFAULT_EXAMPLE_PLACEHOLDER = '"example"'


def sanitize_module_name(name: str) -> str:
    """Sanitize server name for use as Python module name.

    Args:
        name: Original server name.

    Returns:
        Valid Python module name (lowercase, underscored).
    """
    # Replace non-alphanumeric chars with underscore
    sanitized = re.sub(r"[^a-zA-Z0-9]", "_", name)
    # Remove leading digits
    sanitized = re.sub(r"^\d+", "", sanitized)
    # Remove consecutive underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Strip leading/trailing underscores
    sanitized = sanitized.strip("_")
    # Ensure not empty
    if not sanitized:
        sanitized = "server"
    sanitized = sanitized.lower()
    # Avoid Python keywords
    if keyword.iskeyword(sanitized):
        sanitized = f"{sanitized}_"
    return sanitized


def sanitize_module_name_with_reserved(name: str) -> str:
    """Sanitize server name, avoiding reserved module names.

    If the sanitized name collides with a reserved name (e.g., ptc_helper),
    appends '_mcp' suffix to avoid collision.

    Args:
        name: Original server name.

    Returns:
        Valid Python module name that does not collide with reserved names.
    """
    sanitized = sanitize_module_name(name)
    if sanitized in RESERVED_MODULE_NAMES:
        return f"{sanitized}_mcp"
    return sanitized


def sanitize_function_name(name: str) -> str:
    """Sanitize tool name for use as Python function name.

    Args:
        name: Original tool name.

    Returns:
        Valid Python function name (lowercase, underscored).
    """
    return sanitize_module_name(name)


def sanitize_param_name(name: str) -> str:
    """Sanitize parameter name for use as Python parameter.

    Args:
        name: Original parameter name (e.g., userId, user-id).

    Returns:
        Valid Python parameter name (lowercase, underscored).
    """
    return sanitize_module_name(name)


def json_type_to_python(json_type: str | list) -> str:
    """Convert JSON schema type to Python type hint.

    Args:
        json_type: JSON schema type.

    Returns:
        Python type hint string.
    """
    if isinstance(json_type, list):
        return "Any"

    type_map = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
        "null": "None",
    }
    return type_map.get(json_type, "Any")


def schema_to_params(schema: dict[str, Any]) -> str:
    """Convert JSON schema to Python function parameters.

    Args:
        schema: JSON schema for tool input.

    Returns:
        Function parameter string.
    """
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    if not properties:
        return "**kwargs: Any"

    params: list[str] = []
    optional_params: list[str] = []

    for prop_name, prop_schema in properties.items():
        safe_name = sanitize_param_name(prop_name)
        type_hint = json_type_to_python(prop_schema.get("type", "any"))

        if prop_name in required:
            params.append(f"{safe_name}: {type_hint}")
        else:
            optional_params.append(f"{safe_name}: {type_hint} | None = None")

    # Required params first, then optional
    all_params = params + optional_params
    return ", ".join(all_params) if all_params else "**kwargs: Any"


def example_value_from_schema(
    prop_schema: dict[str, Any],
    default_placeholder: str = DEFAULT_EXAMPLE_PLACEHOLDER,
) -> str:
    """Return an example value for a schema property.

    Prefers schema-provided examples, defaults, or enums, and falls back
    to type-based placeholders.

    Args:
        prop_schema: Property schema from JSON schema.
        default_placeholder: Placeholder value to use for unknown types.

    Returns:
        Example value as a Python literal string.
    """
    if prop_schema.get("examples"):
        return repr(prop_schema["examples"][0])
    if "default" in prop_schema:
        return repr(prop_schema["default"])
    if prop_schema.get("enum"):
        return repr(prop_schema["enum"][0])

    prop_type = prop_schema.get("type", "string")
    type_placeholders = {
        "integer": "1",
        "number": "1.0",
        "boolean": "True",
        "array": "[]",
        "object": "{}",
    }

    if prop_type in type_placeholders:
        return type_placeholders[prop_type]

    if prop_type == "string":
        return default_placeholder

    return default_placeholder
