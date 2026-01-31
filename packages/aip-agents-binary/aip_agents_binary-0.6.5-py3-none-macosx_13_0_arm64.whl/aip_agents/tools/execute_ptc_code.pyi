from _typeshed import Incomplete
from aip_agents.mcp.client.base_mcp_client import BaseMCPClient as BaseMCPClient
from aip_agents.ptc.executor import PTCSandboxConfig as PTCSandboxConfig, PTCSandboxExecutor as PTCSandboxExecutor
from aip_agents.ptc.naming import sanitize_function_name as sanitize_function_name
from aip_agents.sandbox.e2b_runtime import E2BSandboxRuntime as E2BSandboxRuntime
from aip_agents.tools.tool_config_injector import TOOL_CONFIGS_KEY as TOOL_CONFIGS_KEY
from aip_agents.utils.logger import get_logger as get_logger
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from typing import Any

logger: Incomplete

class PTCCodeInput(BaseModel):
    """Input schema for PTCCodeTool."""
    code: str

def merge_tool_configs(agent_configs: dict[str, Any] | None, runtime_configs: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    '''Merge agent-level and runtime tool configs with sanitized keys.

    Merges tool configurations from two sources:
    1. Agent-level defaults (from agent.tool_configs)
    2. Runtime overrides (from RunnableConfig.metadata["tool_configs"])

    Both sources support two formats (matching LangGraphReactAgent behavior):
    - Direct per-tool keys: {"time_tool": {"timezone": "UTC"}}
    - Nested structure: {"tool_configs": {"time_tool": {"timezone": "UTC"}}}

    The nested "tool_configs" key has higher precedence than direct keys.
    Tool names are sanitized to match sandbox expectations (e.g., "Time Tool" -> "time_tool").

    Args:
        agent_configs: Agent-level tool configs (may be None or contain nested dicts)
        runtime_configs: Runtime overrides from metadata (may be None)

    Returns:
        Merged dict with sanitized tool names as keys and config dicts as values.
        Only includes entries that are dicts (non-dict values are agent-wide defaults).
    '''

class PTCCodeTool(BaseTool):
    """Tool for executing Python code with MCP tool access in a sandbox.

    This tool uses BaseTool to properly access runtime config via run_manager.metadata.
    The config parameter is NOT exposed to the LLM schema - it's extracted from
    the callback manager during execution.
    """
    name: str
    description: str
    args_schema: type[BaseModel]
    def __init__(self, executor: PTCSandboxExecutor, runtime: E2BSandboxRuntime, agent_tool_configs: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Initialize the PTC code tool.

        Args:
            executor: The PTC sandbox executor.
            runtime: The E2B sandbox runtime.
            agent_tool_configs: Optional agent-level tool configs.
            **kwargs: Additional keyword arguments passed to BaseTool.
        """
    async def cleanup(self) -> None:
        """Clean up the sandbox runtime."""

def create_execute_ptc_code_tool(mcp_client: BaseMCPClient | None, config: PTCSandboxConfig | None = None, agent_tool_configs: dict[str, Any] | None = None) -> PTCCodeTool:
    '''Create a tool that executes Python code with MCP tool access.

    The code runs inside an E2B sandbox with access to generated MCP tool modules.
    This tool is designed for LLM-generated code that needs to call multiple tools
    programmatically in a single execution.

    Args:
        mcp_client: The MCP client with configured servers.
        config: Optional sandbox executor configuration.
        agent_tool_configs: Optional agent-level tool configs (from agent.tool_configs).
            These are merged with runtime overrides from RunnableConfig.metadata.

    Returns:
        PTCCodeTool configured for PTC code execution.

    Example:
        ```python
        from aip_agents.mcp.client import LangchainMCPClient
        from aip_agents.tools.execute_ptc_code import create_execute_ptc_code_tool

        mcp_client = LangchainMCPClient()
        await mcp_client.add_server("yfinance", {...})

        tool = create_execute_ptc_code_tool(mcp_client)
        result = await tool.ainvoke({"code": "from tools.yfinance import get_stock\\\\nprint(get_stock(\'AAPL\'))"})
        ```
    '''
