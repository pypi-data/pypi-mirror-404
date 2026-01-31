from _typeshed import Incomplete
from aip_agents.mcp.client.base_mcp_client import BaseMCPClient as BaseMCPClient
from aip_agents.ptc.doc_gen import render_tool_doc as render_tool_doc
from aip_agents.ptc.naming import DEFAULT_EXAMPLE_PLACEHOLDER as DEFAULT_EXAMPLE_PLACEHOLDER, example_value_from_schema as example_value_from_schema, sanitize_function_name as sanitize_function_name, sanitize_module_name_with_reserved as sanitize_module_name_with_reserved, schema_to_params as schema_to_params
from aip_agents.ptc.payload import SandboxPayload as SandboxPayload
from aip_agents.ptc.template_utils import render_template as render_template
from aip_agents.utils.logger import get_logger as get_logger
from dataclasses import dataclass, field
from typing import Any

logger: Incomplete
SUPPORTED_TRANSPORTS: Incomplete

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
    allowed_tools: list[str] | None = ...
    tools: list[dict[str, Any]] = field(default_factory=list)
    timeout: float = ...

async def build_mcp_payload(mcp_client: BaseMCPClient, default_tool_timeout: float = 60.0) -> SandboxPayload:
    """Build MCP sandbox payload from MCP client configuration.

    Extracts server configs, tools, and generates the necessary files
    for the sandbox to execute PTC code.

    Args:
        mcp_client: The MCP client with configured servers.
        default_tool_timeout: Default timeout for tool calls in seconds.

    Returns:
        SandboxPayload containing files and env vars for the sandbox.
    """
