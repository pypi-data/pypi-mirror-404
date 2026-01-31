"""PTC Prompt Builder.

Generates usage guidance prompts for PTC that help the LLM correctly use
the execute_ptc_code tool with proper import patterns and parameter naming.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from aip_agents.ptc.naming import (
    example_value_from_schema,
    sanitize_function_name,
    sanitize_module_name_with_reserved,
    sanitize_param_name,
    schema_to_params,
)
from aip_agents.utils.logger import get_logger

if TYPE_CHECKING:
    from aip_agents.mcp.client.base_mcp_client import BaseMCPClient

logger = get_logger(__name__)

# Prompt mode type alias
PromptMode = Literal["minimal", "index", "full", "auto"]

# Markdown constants
PYTHON_BLOCK_START = "```python"


@dataclass
class PromptConfig:
    """Configuration for PTC prompt generation.

    Attributes:
        mode: Prompt mode - minimal, index, full, or auto.
        auto_threshold: Total tool count threshold for auto mode (default 10).
        include_example: Whether to include example code in prompt.
    """

    mode: PromptMode = "auto"
    auto_threshold: int = 10
    include_example: bool = True


# Shared PTC usage rules block (DRY: used in both placeholder and full prompts)
PTC_USAGE_RULES = """## PTC (Programmatic Tool Calling) Usage

When using `execute_ptc_code`, follow these rules:

1. **Import pattern**: `from tools.<server> import <tool_name>`
2. **Output**: Only `print()` output is returned to you. Always print results.
3. **Parameter names**: All parameters are lowercase with underscores.
   - Example: `userId` becomes `userid`, `user-id` becomes `user_id`
"""


def build_ptc_prompt(
    mcp_client: BaseMCPClient | None = None,
    config: PromptConfig | None = None,
) -> str:
    """Build PTC usage guidance prompt from MCP configuration.

    Generates a short usage block that includes:
    - The import pattern: MCP (`from tools.<server> import <tool>`)
    - Rule: use `print()`; only printed output returns
    - Rule: parameter names are sanitized to lowercase/underscored
    - Prompt mode content (minimal/index/full)
    - Examples based on the resolved prompt mode

    Args:
        mcp_client: The MCP client with configured servers.
        config: Prompt configuration. If None, uses default PromptConfig.

    Returns:
        PTC usage guidance prompt string.
    """
    if config is None:
        config = PromptConfig()

    # Collect MCP server info (sorted for deterministic output)
    server_infos: list[dict[str, Any]] = []
    if mcp_client and mcp_client.servers:
        for server_name in sorted(mcp_client.servers.keys()):
            tools = _get_server_tools(mcp_client, server_name)
            server_infos.append({"name": server_name, "tools": tools})

    # Check if we have any tools
    if not server_infos:
        return _build_placeholder_prompt()

    # Resolve mode and build appropriate prompt
    resolved_mode = _resolve_mode(config, server_infos)

    if resolved_mode == "minimal":
        return _build_minimal_prompt(server_infos, config.include_example)
    elif resolved_mode == "index":
        return _build_index_prompt(server_infos, config.include_example)
    else:  # full
        return _build_full_prompt(server_infos, config.include_example)


def _get_server_tools(
    mcp_client: BaseMCPClient,
    server_name: str,
) -> list[dict[str, Any]]:
    """Get tool definitions for a server.

    When tools are not loaded but allowed_tools exists, returns stub tool entries.

    Args:
        mcp_client: MCP client instance.
        server_name: Name of the server.

    Returns:
        List of tool definitions with name, description, and input_schema.
        Stubs have empty description and minimal schema when tools not loaded.
    """
    tools: list[dict[str, Any]] = []
    allowed_tools: list[str] | None = None
    raw_tools: list[Any] = []
    try:
        # Try to get cached tools from session pool
        session = mcp_client.session_pool.get_session(server_name)
        allowed_tools = session.allowed_tools if session.allowed_tools else None

        # Get tools from session (public attribute on PersistentMCPSession)
        raw_tools = list(getattr(session, "tools", []))
    except (KeyError, AttributeError) as e:
        logger.debug(f"Could not get tools for server '{server_name}': {e}")

    if allowed_tools is None:
        allowed_tools = _get_allowed_tools_from_config(mcp_client, server_name)

    if not raw_tools and allowed_tools:
        # Tools not loaded but allowlist exists - return stub entries
        for tool_name in sorted(allowed_tools):
            tools.append(
                {
                    "name": tool_name,
                    "description": "",
                    "input_schema": {"type": "object", "properties": {}},
                    "stub": True,
                }
            )
    elif raw_tools:
        # Tools loaded - return actual tool definitions
        for tool in raw_tools:
            if allowed_tools and tool.name not in allowed_tools:
                continue
            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema,
                    "stub": False,
                }
            )
    return tools


def _get_allowed_tools_from_config(mcp_client: BaseMCPClient, server_name: str) -> list[str] | None:
    """Extract allowed_tools from MCP client server config.

    Args:
        mcp_client: MCP client instance.
        server_name: Server name to look up.

    Returns:
        List of allowed tools or None.
    """
    if not mcp_client or not mcp_client.servers:
        return None

    config = mcp_client.servers.get(server_name)
    if not config:
        return None

    raw_allowed = config.get("allowed_tools") if isinstance(config, dict) else getattr(config, "allowed_tools", None)
    if raw_allowed and isinstance(raw_allowed, list):
        return list(raw_allowed)
    return None


def _count_total_tools(
    server_infos: list[dict[str, Any]],
) -> int:
    """Count total tools across all servers.

    Args:
        server_infos: List of server info dicts with name and tools.

    Returns:
        Total tool count.
    """
    return sum(len(info.get("tools", [])) for info in server_infos)


def _resolve_mode(
    config: PromptConfig,
    server_infos: list[dict[str, Any]],
) -> PromptMode:
    """Resolve auto mode to concrete mode based on tool count.

    Args:
        config: Prompt configuration.
        server_infos: List of server info dicts.

    Returns:
        Resolved mode (minimal, index, or full).
    """
    if config.mode != "auto":
        return config.mode

    total_tools = _count_total_tools(server_infos)
    if total_tools == 0 or total_tools > config.auto_threshold:
        return "minimal"
    return "full"


def _build_discovery_example() -> str:
    """Build discovery example using ptc_helper module.

    Returns:
        Discovery example code string.
    """
    return """from tools.ptc_helper import list_tools, describe_tool

# List available tools in a package
tools = list_tools("package_name")
print([tool["name"] for tool in tools])

# Get details for a specific tool
doc = describe_tool("package_name", tools[0]["name"])
print(doc["doc"])"""


def _build_minimal_prompt(
    server_infos: list[dict[str, Any]],
    include_example: bool,
) -> str:
    """Build minimal prompt with rules and package list only.

    Args:
        server_infos: List of server info dicts with name and tools.
        include_example: Whether to include discovery example.

    Returns:
        Minimal PTC usage prompt.
    """
    lines = [
        PTC_USAGE_RULES.rstrip(),
        "",
        "### Available Packages",
        "",
    ]

    # List MCP packages (sorted reserved-safe sanitized names)
    package_names = sorted(sanitize_module_name_with_reserved(info["name"]) for info in server_infos)
    for pkg in package_names:
        lines.append(f"- `tools.{pkg}`")

    lines.append("")
    lines.append("Use `tools.ptc_helper` to discover available tools and their signatures.")

    if include_example:
        lines.extend(
            [
                "",
                "### Discovery Example",
                "",
                PYTHON_BLOCK_START,
                _build_discovery_example(),
                "```",
            ]
        )

    return "\n".join(lines)


def _build_index_prompt(
    server_infos: list[dict[str, Any]],
    include_example: bool,
) -> str:
    """Build index prompt with rules, package list, and tool names.

    Args:
        server_infos: List of server info dicts with name and tools.
        include_example: Whether to include discovery example.

    Returns:
        Index PTC usage prompt.
    """
    lines = [
        PTC_USAGE_RULES.rstrip(),
        "",
        "### Available Tools",
        "",
    ]

    # Sort server infos by reserved-safe sanitized name for deterministic output
    sorted_infos = sorted(server_infos, key=lambda x: sanitize_module_name_with_reserved(x["name"]))

    for server_info in sorted_infos:
        safe_server = sanitize_module_name_with_reserved(server_info["name"])
        lines.append(f"**`tools.{safe_server}`**")

        # Sort tools by sanitized name
        sorted_tools = sorted(server_info["tools"], key=lambda t: sanitize_function_name(t["name"]))
        tool_names = [sanitize_function_name(t["name"]) for t in sorted_tools]
        lines.append(f"  Tools: {', '.join(tool_names)}")
        lines.append("")

    lines.append("Use `tools.ptc_helper` to get tool signatures and descriptions.")

    if include_example:
        lines.extend(
            [
                "",
                "### Discovery Example",
                "",
                PYTHON_BLOCK_START,
                _build_discovery_example(),
                "```",
            ]
        )

    return "\n".join(lines)


def _build_full_prompt(
    server_infos: list[dict[str, Any]],
    include_example: bool,
) -> str:
    """Build full prompt with rules, signatures, and descriptions.

    Args:
        server_infos: List of server info dicts with name and tools.
        include_example: Whether to include real tool example.

    Returns:
        Full PTC usage prompt.
    """
    lines = [
        PTC_USAGE_RULES.rstrip(),
        "",
        "### Available Tools",
        "",
    ]

    # Sort server infos by reserved-safe sanitized name for deterministic output
    sorted_infos = sorted(server_infos, key=lambda x: sanitize_module_name_with_reserved(x["name"]))

    for server_info in sorted_infos:
        safe_server = sanitize_module_name_with_reserved(server_info["name"])
        lines.append(f"**Server: `{safe_server}`** (from `tools.{safe_server}`)")
        lines.append("")

        # Sort tools by sanitized name
        sorted_tools = sorted(server_info["tools"], key=lambda t: sanitize_function_name(t["name"]))

        for tool in sorted_tools:
            func_name = sanitize_function_name(tool["name"])
            schema = tool.get("input_schema", {})
            params = schema_to_params(schema)
            raw_desc = tool.get("description", "")
            desc = raw_desc[:120]
            if raw_desc and len(raw_desc) > 120:
                desc += "..."

            lines.append(f"- `{func_name}({params})`: {desc}")

        lines.append("")

    if include_example:
        example = _build_example(server_infos)
        lines.extend(
            [
                "### Example",
                "",
                PYTHON_BLOCK_START,
                example,
                "```",
            ]
        )

    return "\n".join(lines)


def _build_prompt_from_servers(server_infos: list[dict[str, Any]]) -> str:
    """Build prompt from collected server information (legacy, uses full mode).

    Args:
        server_infos: List of server info dicts with name and tools.

    Returns:
        Formatted PTC usage prompt.
    """
    return _build_full_prompt(server_infos, include_example=True)


def _build_example(
    server_infos: list[dict[str, Any]],
) -> str:
    """Build an example code snippet using the first available tool.

    Args:
        server_infos: List of server info dicts.

    Returns:
        Example code string.
    """
    if server_infos:
        sorted_servers = sorted(server_infos, key=lambda info: sanitize_module_name_with_reserved(info["name"]))
        for server in sorted_servers:
            tools = server.get("tools", [])
            if tools:
                sorted_tools = sorted(tools, key=lambda t: sanitize_function_name(t["name"]))
                tool = sorted_tools[0]
                safe_server = sanitize_module_name_with_reserved(server["name"])
                func_name = sanitize_function_name(tool["name"])
                args_str = _build_example_args_from_schema(tool.get("input_schema", {}))
                return f"""from tools.{safe_server} import {func_name}

result = {func_name}({args_str})
print(result)"""

    return _build_generic_example()


def _build_example_args_from_schema(schema: dict[str, Any]) -> str:
    """Build example arguments string from a JSON schema.

    Args:
        schema: JSON schema for tool input.

    Returns:
        Example arguments string.
    """
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    args: list[str] = []
    for prop_name in sorted(required):
        if prop_name not in properties:
            continue
        safe_name = sanitize_param_name(prop_name)
        prop_schema = properties[prop_name]
        example_value = _get_example_value(prop_schema, prop_name)
        args.append(f"{safe_name}={example_value}")

    for prop_name in sorted(properties.keys()):
        if prop_name in required:
            continue
        if len(args) >= 2:
            break
        safe_name = sanitize_param_name(prop_name)
        prop_schema = properties[prop_name]
        example_value = _get_example_value(prop_schema, prop_name)
        args.append(f"{safe_name}={example_value}")

    return ", ".join(args) if args else ""


def _get_example_value(prop_schema: dict[str, Any], prop_name: str) -> str:
    """Generate an example value for a parameter.

    Prefers schema-provided examples, defaults, or enums.
    Falls back to type-based placeholders.

    Args:
        prop_schema: Property schema from JSON schema.
        prop_name: Original property name.

    Returns:
        Example value as a Python literal string.
    """
    return example_value_from_schema(prop_schema)


def _build_generic_example() -> str:
    """Build a generic example when no tools are available.

    Returns:
        Generic example code string.
    """
    return """from tools.server_name import tool_name

result = tool_name(param="value")
print(result)"""


def _build_placeholder_prompt() -> str:
    """Build a placeholder prompt when no MCP servers are configured.

    Returns:
        Placeholder PTC usage prompt.
    """
    return PTC_USAGE_RULES + "\n*No MCP servers configured yet. Tools will be available after MCP setup.*\n"


def _build_server_hash_part(mcp_client: BaseMCPClient, server_name: str) -> str:
    """Build hash part for a single MCP server.

    Args:
        mcp_client: MCP client instance.
        server_name: Name of the server.

    Returns:
        Hash part string for the server.
    """
    try:
        session = mcp_client.session_pool.get_session(server_name)
        tools = list(getattr(session, "tools", []))
        tool_names = sorted(t.name for t in tools)

        allowed = session.allowed_tools if hasattr(session, "allowed_tools") else None
        if not allowed:
            allowed = _get_allowed_tools_from_config(mcp_client, server_name)
        allowed_str = ",".join(sorted(allowed)) if allowed else "*"

        return f"{server_name}:{','.join(tool_names)}|allowed={allowed_str}"
    except (KeyError, AttributeError):
        allowed = _get_allowed_tools_from_config(mcp_client, server_name)
        allowed_str = ",".join(sorted(allowed)) if allowed else "*"
        return f"{server_name}:|allowed={allowed_str}"


def compute_ptc_prompt_hash(
    mcp_client: BaseMCPClient | None = None,
    config: PromptConfig | None = None,
) -> str:
    """Compute a hash of the MCP configuration for change detection.

    Includes PromptConfig fields and allowed_tools in hash computation
    so prompt updates re-sync correctly when configuration changes.

    Args:
        mcp_client: MCP client instance.
        config: Prompt configuration. If None, uses default PromptConfig.

    Returns:
        Hash string representing current configuration.
    """
    import hashlib

    if config is None:
        config = PromptConfig()

    # Include config fields in hash
    config_part = f"mode={config.mode}|threshold={config.auto_threshold}|example={config.include_example}"

    # Create hash from server names, tool names, and allowed_tools
    parts: list[str] = [config_part]

    # Add MCP server parts
    if mcp_client and mcp_client.servers:
        for server_name in sorted(mcp_client.servers.keys()):
            parts.append(_build_server_hash_part(mcp_client, server_name))

    # Return empty hash if no tools configured
    if len(parts) == 1:
        return ""

    content = "|".join(parts)
    return hashlib.sha256(content.encode()).hexdigest()[:16]
