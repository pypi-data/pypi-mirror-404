def validate_package_name(package: str) -> bool:
    """Validate package name/specifier format for pip install.

    Allows standard pip formats: package, package==version, package[extra].

    Args:
        package: Package name or specifier to validate.

    Returns:
        True if package name is valid, False otherwise.
    """
def validate_package_names(packages: list[str]) -> None:
    """Validate all package names in a list.

    Args:
        packages: List of package names or specifiers to validate.

    Raises:
        ValueError: If any package name is invalid.
    """
