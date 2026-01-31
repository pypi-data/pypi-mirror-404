"""Validation utilities for sandbox operations.

This module provides validation functions for sandbox-related operations
such as package name validation.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import re

_PACKAGE_SPEC_PATTERN = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
    r"(?:\[[A-Za-z0-9._-]+(?:,[A-Za-z0-9._-]+)*\])?"
    r"(?:"
    r"(?:==|!=|<=|>=|~=|<|>)[0-9][A-Za-z0-9.*+!_-]*"
    r"(?:,(?:==|!=|<=|>=|~=|<|>)[0-9][A-Za-z0-9.*+!_-]*)*"
    r")?$"
)


def validate_package_name(package: str) -> bool:
    """Validate package name/specifier format for pip install.

    Allows standard pip formats: package, package==version, package[extra].

    Args:
        package: Package name or specifier to validate.

    Returns:
        True if package name is valid, False otherwise.
    """
    if not package:
        return False

    return bool(_PACKAGE_SPEC_PATTERN.fullmatch(package))


def validate_package_names(packages: list[str]) -> None:
    """Validate all package names in a list.

    Args:
        packages: List of package names or specifiers to validate.

    Raises:
        ValueError: If any package name is invalid.
    """
    for pkg in packages:
        if not validate_package_name(pkg):
            raise ValueError(f"Invalid package name format: {pkg}")
