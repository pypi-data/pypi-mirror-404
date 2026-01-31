"""Sandbox Bridge for PTC.

This module generates the sandbox payload (config + tool modules) that allows
LLM-generated code to call MCP tools inside an E2B sandbox.

The payload includes:
- ptc_config.json: MCP server configs for the sandbox MCP client
- tools/__init__.py: Package init with server imports
- tools/<server>.py: Per-server module with sync tool functions
- tools/mcp_client.py: HTTP JSON-RPC client for MCP calls

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import json
from dataclasses import dataclass, field
from typing import Any

from aip_agents.mcp.client.base_mcp_client import BaseMCPClient
from aip_agents.ptc.doc_gen import (
    render_tool_doc,
)
from aip_agents.ptc.naming import (
    DEFAULT_EXAMPLE_PLACEHOLDER,
    example_value_from_schema,
    sanitize_function_name,
    sanitize_module_name_with_reserved,
    schema_to_params,
)
from aip_agents.ptc.payload import SandboxPayload
from aip_agents.ptc.ptc_helper import _generate_ptc_helper_module
from aip_agents.ptc.template_utils import render_template
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)

# Transport types supported in sandbox (HTTP-based only)
# Using normalized hyphenated format to align with connection_manager
SUPPORTED_TRANSPORTS = {"sse", "streamable-http"}

_TEMPLATE_PACKAGE = "aip_agents.ptc.mcp.templates"


@dataclass
class ServerConfig:
    """Extracted server configuration for sandbox payload.

    Attributes:
        name: Server name identifier.
        transport: Transport type (sse or streamable_http).
        url: Server URL.
        headers: HTTP headers for authentication.
        allowed_tools: List of allowed tool names, or None for all.
        tools: List of tool definitions from the server.
        timeout: Request timeout in seconds.
    """

    name: str
    transport: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    allowed_tools: list[str] | None = None
    tools: list[dict[str, Any]] = field(default_factory=list)
    timeout: float = 60.0


async def build_mcp_payload(
    mcp_client: BaseMCPClient,
    default_tool_timeout: float = 60.0,
) -> SandboxPayload:
    """Build MCP sandbox payload from MCP client configuration.

    Extracts server configs, tools, and generates the necessary files
    for the sandbox to execute PTC code.

    Args:
        mcp_client: The MCP client with configured servers.
        default_tool_timeout: Default timeout for tool calls in seconds.

    Returns:
        SandboxPayload containing files and env vars for the sandbox.
    """
    payload = SandboxPayload()

    # Extract server configs
    server_configs = await _extract_server_configs(mcp_client, default_tool_timeout)

    if not server_configs:
        logger.warning("No supported MCP servers found for sandbox payload")
        return payload

    # Generate ptc_config.json
    config_json = _generate_config_json(server_configs)
    payload.files["ptc_config.json"] = config_json

    # Generate tools/mcp_client.py
    payload.files["tools/mcp_client.py"] = _generate_mcp_client_module()

    # Generate tools/__init__.py
    server_names = [cfg.name for cfg in server_configs]
    payload.files["tools/__init__.py"] = _generate_tools_init(server_names)

    # Generate tools/<server>.py for each server (using reserved-aware sanitization)
    for server_cfg in server_configs:
        module_content = _generate_server_module(server_cfg)
        safe_name = sanitize_module_name_with_reserved(server_cfg.name)
        payload.files[f"tools/{safe_name}.py"] = module_content

    # Generate tools/ptc_helper.py for discovery
    payload.files["tools/ptc_helper.py"] = _generate_ptc_helper_module()

    # Generate tools/ptc_index.json for tool index
    payload.files["tools/ptc_index.json"] = _generate_ptc_index(server_configs)

    # Generate tools/docs/<package>/<tool>.md for each tool
    docs = _generate_all_docs(server_configs)
    payload.files.update(docs)

    logger.info(f"Built sandbox payload with {len(server_configs)} servers, {len(payload.files)} files")

    return payload


def _get_config_value(config: Any, key: str, default: Any = None) -> Any:
    """Extract value from config dict or object.

    Args:
        config: Configuration dict or object.
        key: Key to extract.
        default: Default value if key not found.

    Returns:
        Extracted value or default.
    """
    if isinstance(config, dict):
        return config.get(key, default)
    return getattr(config, key, default)


def _normalize_transport(transport: Any) -> str | None:
    """Normalize transport format.

    Args:
        transport: Raw transport value.

    Returns:
        Normalized transport string or None.
    """
    if not transport:
        return None
    return str(transport).lower().replace("_", "-")


def _extract_headers(config: Any) -> dict[str, str]:
    """Extract headers from config.

    Args:
        config: Configuration dict or object.

    Returns:
        Headers dictionary.
    """
    raw_headers = _get_config_value(config, "headers")
    if raw_headers and isinstance(raw_headers, dict):
        return dict(raw_headers)
    return {}


def _extract_timeout(config: Any, default_timeout: float) -> float:
    """Extract timeout from config.

    Args:
        config: Configuration dict or object.
        default_timeout: Default timeout value.

    Returns:
        Timeout in seconds.
    """
    raw_timeout = _get_config_value(config, "timeout")
    if raw_timeout is not None:
        return float(raw_timeout)
    return default_timeout


def _extract_allowed_tools(mcp_client: BaseMCPClient, server_name: str, config: Any) -> list[str] | None:
    """Extract allowed tools from session or config.

    Args:
        mcp_client: MCP client instance.
        server_name: Name of the server.
        config: Configuration dict or object.

    Returns:
        List of allowed tool names or None.
    """
    try:
        session = mcp_client.session_pool.get_session(server_name)
        if session.allowed_tools:
            return list(session.allowed_tools)
    except (KeyError, AttributeError):
        pass

    raw_allowed = _get_config_value(config, "allowed_tools")
    if raw_allowed and isinstance(raw_allowed, list):
        return list(raw_allowed)
    return None


async def _extract_tools(
    mcp_client: BaseMCPClient,
    server_name: str,
    allowed_tools: list[str] | None,
) -> list[dict[str, Any]]:
    """Extract tools from MCP client.

    When tools are not loaded but allowed_tools exists, returns stub tool entries.

    Args:
        mcp_client: MCP client instance.
        server_name: Name of the server.
        allowed_tools: List of allowed tool names or None.

    Returns:
        List of tool definitions. Stubs have minimal schema when tools not loaded.
    """
    tools: list[dict[str, Any]] = []
    try:
        raw_tools = await mcp_client.get_raw_mcp_tools(server_name)
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
    except Exception as e:
        logger.warning(f"Failed to get tools from server '{server_name}': {e}")
        # If tools not loaded but allowlist exists, create stub entries
        if allowed_tools:
            for tool_name in sorted(allowed_tools):
                tools.append(
                    {
                        "name": tool_name,
                        "description": "",
                        "input_schema": {"type": "object", "properties": {}},
                        "stub": True,
                    }
                )
    return tools


async def _extract_server_configs(
    mcp_client: BaseMCPClient,
    default_tool_timeout: float,
) -> list[ServerConfig]:
    """Extract server configurations from MCP client.

    Args:
        mcp_client: The MCP client with configured servers.
        default_tool_timeout: Default timeout for tool calls.

    Returns:
        List of ServerConfig objects for supported servers.
    """
    server_configs: list[ServerConfig] = []

    for server_name, config in mcp_client.servers.items():
        transport = _normalize_transport(_get_config_value(config, "transport"))

        if transport not in SUPPORTED_TRANSPORTS:
            logger.warning(
                f"Skipping server '{server_name}': transport '{transport}' not supported in sandbox "
                f"(supported: {SUPPORTED_TRANSPORTS})"
            )
            continue

        url = _get_config_value(config, "url")
        if not url:
            logger.warning(f"Skipping server '{server_name}': no URL configured")
            continue

        headers = _extract_headers(config)
        timeout = _extract_timeout(config, default_tool_timeout)
        allowed_tools = _extract_allowed_tools(mcp_client, server_name, config)
        tools = await _extract_tools(mcp_client, server_name, allowed_tools)

        server_configs.append(
            ServerConfig(
                name=server_name,
                transport=transport,
                url=url,
                headers=headers,
                allowed_tools=allowed_tools,
                tools=tools,
                timeout=timeout,
            )
        )

        logger.debug(f"Extracted config for server '{server_name}': {len(tools)} tools")

    return server_configs


def _generate_config_json(server_configs: list[ServerConfig]) -> str:
    """Generate ptc_config.json content.

    Args:
        server_configs: List of server configurations.

    Returns:
        JSON string of the config.
    """
    config = {
        "servers": {
            cfg.name: {
                "transport": cfg.transport,
                "url": cfg.url,
                "headers": cfg.headers,
                "timeout": cfg.timeout,
                "allowed_tools": cfg.allowed_tools,
            }
            for cfg in server_configs
        }
    }
    return json.dumps(config, indent=2)


def _generate_mcp_client_module() -> str:
    """Generate the tools/mcp_client.py module.

    This module uses the official MCP Python SDK to call MCP tools from the sandbox.
    It provides sync wrappers around the async MCP SDK for simpler LLM-generated code.

    Returns:
        Python source code for the MCP client module.
    """
    return render_template(_TEMPLATE_PACKAGE, "mcp_client.py.template")


def _generate_tools_init(server_names: list[str]) -> str:
    """Generate tools/__init__.py content.

    Args:
        server_names: List of server names.

    Returns:
        Python source code for the __init__.py module.
    """
    # Use reserved-safe sanitization and sort for deterministic output
    safe_names = sorted(sanitize_module_name_with_reserved(name) for name in server_names)

    imports = "\n".join(f"from tools import {name}" for name in safe_names)
    all_list = ", ".join(f'"{name}"' for name in safe_names)

    return f'''"""Generated tools package for PTC sandbox execution.

This package provides access to MCP tools configured for this agent.
Import tools from specific server modules:

    from tools.server_name import tool_name
"""

{imports}

__all__ = [{all_list}]
'''


def _generate_server_module(server_cfg: ServerConfig) -> str:
    """Generate tools/<server>.py module content.

    Args:
        server_cfg: Server configuration with tools.

    Returns:
        Python source code for the server module.
    """
    functions: list[str] = []
    function_names: list[str] = []

    for tool in server_cfg.tools:
        func_name = sanitize_function_name(tool["name"])
        function_names.append(func_name)

        # Build function signature from input_schema
        schema = tool.get("input_schema", {})
        params = schema_to_params(schema)
        doc = _build_docstring(tool)

        func_code = f'''
def {func_name}({params}) -> Any:
    """{doc}"""
    arguments = {_build_arguments_dict(schema)}
    return call_tool("{server_cfg.name}", "{tool["name"]}", arguments)
'''
        functions.append(func_code)

    all_list = ", ".join(f'"{name}"' for name in function_names)
    functions_code = "\n".join(functions)

    return f'''"""Generated module for MCP server: {server_cfg.name}

This module provides Python functions for each tool exposed by the MCP server.
"""

from typing import Any

from tools.mcp_client import call_tool

__all__ = [{all_list}]

{functions_code}
'''


# Note: sanitize_module_name, sanitize_function_name, schema_to_params, and
# json_type_to_python are imported from aip_agents.ptc.naming


def _build_arguments_dict(schema: dict[str, Any]) -> str:
    """Build arguments dict code from schema.

    Args:
        schema: JSON schema for tool input.

    Returns:
        Python code for building arguments dict.
    """
    properties = schema.get("properties", {})

    if not properties:
        return "kwargs"

    items: list[str] = []
    for prop_name in properties:
        safe_name = sanitize_function_name(prop_name)
        items.append(f'"{prop_name}": {safe_name}')

    return "{" + ", ".join(items) + "}"


def _build_docstring(tool: dict[str, Any]) -> str:
    """Build docstring for a tool function.

    Args:
        tool: Tool definition with name, description, input_schema.

    Returns:
        Docstring content.
    """
    desc = tool.get("description", f"Call {tool['name']} tool.")
    # Escape triple quotes in description
    desc = desc.replace('"""', '\\"\\"\\"')
    return desc


def _generate_tool_doc(
    tool: dict[str, Any],
) -> str:
    """Generate markdown documentation for a single tool.

    Args:
        tool: Tool definition with name, description, input_schema, optional stub flag.

    Returns:
        Markdown documentation string.
    """
    func_name = sanitize_function_name(tool["name"])
    schema = tool.get("input_schema", {})

    # Use schema_to_params for consistent signatures (stubs and loaded tools)
    params = schema_to_params(schema)
    signature = f"{func_name}({params})"

    # Add example section
    example_args, uses_placeholder = _build_example_args_with_placeholder(schema)
    if tool.get("stub"):
        uses_placeholder = True
    example_heading = "## Example (placeholder)" if uses_placeholder else "## Example"
    example_code = f"{func_name}({example_args})"

    return render_tool_doc(
        func_name=func_name,
        signature=signature,
        description=tool.get("description", ""),
        schema=schema,
        is_stub=tool.get("stub", False),
        example_code=example_code,
        example_heading=example_heading,
    )


def _build_example_args(schema: dict[str, Any]) -> str:
    """Build example argument string for a tool call.

    Uses schema defaults, enums, or examples when available.
    Falls back to neutral placeholders. Required params come first.

    Args:
        schema: Tool input schema.

    Returns:
        Example arguments string.
    """
    args, _ = _build_example_args_with_placeholder(schema)
    return args


def _is_placeholder(prop_schema: dict[str, Any]) -> bool:
    """Check if a property schema uses a placeholder value.

    Args:
        prop_schema: Property schema dict.

    Returns:
        True if the schema doesn't have examples, default, or enum values.
    """
    return not (prop_schema.get("examples") or "default" in prop_schema or prop_schema.get("enum"))


def _process_property_args(
    properties: dict[str, Any],
    required: set[str],
    filter_required: bool,
) -> tuple[list[str], bool]:
    """Process properties and generate argument strings.

    Args:
        properties: Schema properties dict.
        required: Set of required property names.
        filter_required: If True, process only required params; if False, only optional.

    Returns:
        Tuple of (list of arg strings, uses_placeholder flag).
    """
    args: list[str] = []
    uses_placeholder = False

    for prop_name in sorted(properties.keys()):
        is_required = prop_name in required
        if (filter_required and not is_required) or (not filter_required and is_required):
            continue

        prop_schema = properties[prop_name]
        safe_name = sanitize_function_name(prop_name)
        example_value = _get_doc_example_value(prop_schema, prop_name)
        args.append(f"{safe_name}={example_value}")

        if _is_placeholder(prop_schema):
            uses_placeholder = True

    return args, uses_placeholder


def _build_example_args_with_placeholder(schema: dict[str, Any]) -> tuple[str, bool]:
    """Build example arguments with placeholder tracking.

    Args:
        schema: Tool input schema.

    Returns:
        Tuple of (arguments string, uses_placeholder flag).
    """
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    if not properties:
        return "", False

    # Process required params first
    required_args, required_has_placeholder = _process_property_args(properties, required, filter_required=True)

    # Then add optional params
    optional_args, optional_has_placeholder = _process_property_args(properties, required, filter_required=False)

    all_args = required_args + optional_args
    uses_placeholder = required_has_placeholder or optional_has_placeholder

    return ", ".join(all_args), uses_placeholder


def _get_doc_example_value(prop_schema: dict[str, Any], prop_name: str) -> str:
    """Get example value for documentation.

    Prefers schema-provided examples, defaults, or enums.
    Falls back to neutral placeholders.

    Args:
        prop_schema: Property schema.
        prop_name: Property name.

    Returns:
        Example value as Python literal string.
    """
    return example_value_from_schema(prop_schema, default_placeholder=DEFAULT_EXAMPLE_PLACEHOLDER)


def _generate_all_docs(server_configs: list[ServerConfig]) -> dict[str, str]:
    """Generate all tool documentation files.

    Args:
        server_configs: List of server configurations.

    Returns:
        Dict mapping file path to content.
    """
    docs: dict[str, str] = {}

    sorted_configs = sorted(server_configs, key=lambda cfg: sanitize_module_name_with_reserved(cfg.name))

    for cfg in sorted_configs:
        safe_name = sanitize_module_name_with_reserved(cfg.name)
        sorted_tools = sorted(cfg.tools, key=lambda tool: sanitize_function_name(tool["name"]))

        for tool in sorted_tools:
            func_name = sanitize_function_name(tool["name"])
            doc_path = f"tools/docs/{safe_name}/{func_name}.md"
            doc_content = _generate_tool_doc(tool)
            docs[doc_path] = doc_content

    return docs


def _generate_ptc_index(server_configs: list[ServerConfig]) -> str:
    """Generate the tools/ptc_index.json tool index.

    Args:
        server_configs: List of server configurations with tools.

    Returns:
        JSON string of the tool index.
    """
    packages: dict[str, Any] = {}

    # Sort server configs by sanitized name for deterministic output
    sorted_configs = sorted(server_configs, key=lambda c: sanitize_module_name_with_reserved(c.name))

    for cfg in sorted_configs:
        safe_name = sanitize_module_name_with_reserved(cfg.name)

        # Sort tools by sanitized name
        sorted_tools = sorted(cfg.tools, key=lambda t: sanitize_function_name(t["name"]))

        tool_entries = []
        for tool in sorted_tools:
            func_name = sanitize_function_name(tool["name"])
            schema = tool.get("input_schema", {})

            # Use schema_to_params for consistent signatures (stubs and loaded tools)
            signature = f"{func_name}({schema_to_params(schema)})"

            tool_entries.append(
                {
                    "name": func_name,
                    "signature": signature,
                    "doc_path": f"tools/docs/{safe_name}/{func_name}.md",
                }
            )

        packages[safe_name] = {"tools": tool_entries}

    index = {"packages": packages}
    return json.dumps(index, indent=2, sort_keys=True)
