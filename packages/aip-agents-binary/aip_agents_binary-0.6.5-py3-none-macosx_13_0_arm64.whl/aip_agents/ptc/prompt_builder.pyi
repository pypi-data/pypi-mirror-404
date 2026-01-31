from _typeshed import Incomplete
from aip_agents.mcp.client.base_mcp_client import BaseMCPClient as BaseMCPClient
from aip_agents.ptc.naming import example_value_from_schema as example_value_from_schema, sanitize_function_name as sanitize_function_name, sanitize_module_name_with_reserved as sanitize_module_name_with_reserved, sanitize_param_name as sanitize_param_name, schema_to_params as schema_to_params
from aip_agents.utils.logger import get_logger as get_logger
from dataclasses import dataclass

logger: Incomplete
PromptMode: Incomplete
PYTHON_BLOCK_START: str

@dataclass
class PromptConfig:
    """Configuration for PTC prompt generation.

    Attributes:
        mode: Prompt mode - minimal, index, full, or auto.
        auto_threshold: Total tool count threshold for auto mode (default 10).
        include_example: Whether to include example code in prompt.
    """
    mode: PromptMode = ...
    auto_threshold: int = ...
    include_example: bool = ...

PTC_USAGE_RULES: str

def build_ptc_prompt(mcp_client: BaseMCPClient | None = None, config: PromptConfig | None = None) -> str:
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
def compute_ptc_prompt_hash(mcp_client: BaseMCPClient | None = None, config: PromptConfig | None = None) -> str:
    """Compute a hash of the MCP configuration for change detection.

    Includes PromptConfig fields and allowed_tools in hash computation
    so prompt updates re-sync correctly when configuration changes.

    Args:
        mcp_client: MCP client instance.
        config: Prompt configuration. If None, uses default PromptConfig.

    Returns:
        Hash string representing current configuration.
    """
