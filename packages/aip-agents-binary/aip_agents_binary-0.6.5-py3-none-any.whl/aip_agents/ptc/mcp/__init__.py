"""Programmatic Tool Calling (PTC) module for MCP tools.

This module provides programmatic tool calling capabilities for MCP tools,
allowing code-based tool invocation instead of JSON tool calls.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from aip_agents.ptc.exceptions import PTCError, PTCToolError
from aip_agents.ptc.mcp.sandbox_bridge import (
    ServerConfig,
    build_mcp_payload,
)
from aip_agents.ptc.naming import (
    json_type_to_python,
    sanitize_function_name,
    sanitize_module_name,
    sanitize_param_name,
    schema_to_params,
)
from aip_agents.ptc.payload import SandboxPayload
from aip_agents.ptc.prompt_builder import (
    build_ptc_prompt,
    compute_ptc_prompt_hash,
)

__all__ = [
    # Exceptions
    "PTCError",
    "PTCToolError",
    # Naming utilities
    "json_type_to_python",
    "sanitize_function_name",
    "sanitize_module_name",
    "sanitize_param_name",
    "schema_to_params",
    # Prompt builder
    "build_ptc_prompt",
    "compute_ptc_prompt_hash",
    # Sandbox Bridge
    "SandboxPayload",
    "ServerConfig",
    "build_mcp_payload",
]
