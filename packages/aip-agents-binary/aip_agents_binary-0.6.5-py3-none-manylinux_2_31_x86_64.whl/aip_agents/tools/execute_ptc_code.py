"""Execute PTC Code Tool.

This module provides a LangChain tool for executing Python code with MCP tool access
inside an E2B sandbox. The tool is designed for LLM-generated code that needs to call
multiple MCP tools programmatically.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
import concurrent.futures
import json
from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from aip_agents.ptc.naming import sanitize_function_name
from aip_agents.tools.tool_config_injector import TOOL_CONFIGS_KEY
from aip_agents.utils.logger import get_logger

if TYPE_CHECKING:
    from aip_agents.mcp.client.base_mcp_client import BaseMCPClient
    from aip_agents.ptc.executor import PTCSandboxConfig, PTCSandboxExecutor
    from aip_agents.sandbox.e2b_runtime import E2BSandboxRuntime

logger = get_logger(__name__)


class PTCCodeInput(BaseModel):
    """Input schema for PTCCodeTool."""

    code: str = Field(
        ...,
        description=(
            "Python code to execute. Import MCP tools from the generated `tools` package, "
            "for example: `from tools.yfinance import get_stock_history`. "
            "The code runs in a sandboxed environment with access to all configured MCP tools. "
            "Use print() to output results. The tool returns JSON with keys: "
            "ok, stdout, stderr, exit_code."
        ),
    )


def _merge_config_layer(
    merged: dict[str, dict[str, Any]],
    source: dict[str, Any],
    skip_tool_configs_key: bool = True,
) -> None:
    """Merge a single layer of tool configs into the merged dict.

    Args:
        merged: Target dict to merge into (modified in place).
        source: Source dict containing tool configs.
        skip_tool_configs_key: Whether to skip the TOOL_CONFIGS_KEY entry.
    """
    for name, config in source.items():
        if skip_tool_configs_key and name == TOOL_CONFIGS_KEY:
            continue
        if not isinstance(config, dict):
            continue

        sanitized = sanitize_function_name(name)
        if sanitized in merged:
            merged[sanitized].update(config)
        else:
            merged[sanitized] = dict(config)


def merge_tool_configs(
    agent_configs: dict[str, Any] | None,
    runtime_configs: dict[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    """Merge agent-level and runtime tool configs with sanitized keys.

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
    """
    merged: dict[str, dict[str, Any]] = {}

    # Layer 1: Agent-level per-tool configs (direct keys)
    if agent_configs:
        _merge_config_layer(merged, agent_configs, skip_tool_configs_key=True)

    # Layer 2: Agent-level per-tool configs (nested tool_configs key)
    if agent_configs:
        nested_agent = agent_configs.get(TOOL_CONFIGS_KEY)
        if isinstance(nested_agent, dict):
            _merge_config_layer(merged, nested_agent, skip_tool_configs_key=False)

    # Layer 3: Runtime per-tool configs (direct keys, override agent defaults)
    if runtime_configs:
        _merge_config_layer(merged, runtime_configs, skip_tool_configs_key=True)

    # Layer 4: Runtime per-tool configs (nested tool_configs key, highest precedence)
    if runtime_configs:
        nested_runtime = runtime_configs.get(TOOL_CONFIGS_KEY)
        if isinstance(nested_runtime, dict):
            _merge_config_layer(merged, nested_runtime, skip_tool_configs_key=False)

    return merged


class PTCCodeTool(BaseTool):
    """Tool for executing Python code with MCP tool access in a sandbox.

    This tool uses BaseTool to properly access runtime config via run_manager.metadata.
    The config parameter is NOT exposed to the LLM schema - it's extracted from
    the callback manager during execution.
    """

    name: str = "execute_ptc_code"
    description: str = (
        "Execute Python code that can call MCP tools programmatically. "
        "Import tools from the generated `tools` package (e.g., `from tools.yfinance import get_stock`) "
        "and run normal Python code. Use print() to output results. "
        "Returns JSON with ok, stdout, stderr, and exit_code keys. "
        "This tool is useful for chaining multiple MCP tool calls with local data processing."
    )

    # Input schema for LangChain tool invocation
    args_schema: type[BaseModel] = PTCCodeInput

    # Internal attributes (not exposed to LLM)
    _ptc_executor: "PTCSandboxExecutor" = None  # type: ignore[assignment]
    _ptc_runtime: "E2BSandboxRuntime" = None  # type: ignore[assignment]
    _agent_tool_configs: dict[str, Any] | None = None

    def __init__(
        self,
        executor: "PTCSandboxExecutor",
        runtime: "E2BSandboxRuntime",
        agent_tool_configs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the PTC code tool.

        Args:
            executor: The PTC sandbox executor.
            runtime: The E2B sandbox runtime.
            agent_tool_configs: Optional agent-level tool configs.
            **kwargs: Additional keyword arguments passed to BaseTool.
        """
        super().__init__(**kwargs)
        # Store as private attributes to avoid Pydantic field issues
        object.__setattr__(self, "_ptc_executor", executor)
        object.__setattr__(self, "_ptc_runtime", runtime)
        object.__setattr__(self, "_agent_tool_configs", agent_tool_configs)

    def _run(
        self,
        code: str,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> str:
        """Execute code synchronously (wraps async version)."""
        # Extract runtime metadata from run_manager
        runtime_metadata = None
        if run_manager and hasattr(run_manager, "metadata"):
            runtime_metadata = run_manager.metadata

        # Run async version in sync context
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._execute(code, runtime_metadata))

        # Already in async context - run in thread
        def run_in_new_loop() -> str:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self._execute(code, runtime_metadata))
            finally:
                new_loop.close()

        with concurrent.futures.ThreadPoolExecutor() as executor_service:
            future = executor_service.submit(run_in_new_loop)
            return future.result()

    async def _arun(
        self,
        code: str,
        run_manager: AsyncCallbackManagerForToolRun | None = None,
    ) -> str:
        """Execute code asynchronously."""
        # Extract runtime metadata from run_manager
        runtime_metadata = None
        if run_manager and hasattr(run_manager, "metadata"):
            runtime_metadata = run_manager.metadata

        return await self._execute(code, runtime_metadata)

    async def _execute(
        self,
        code: str,
        runtime_metadata: dict[str, Any] | None,
    ) -> str:
        """Internal execution logic."""
        try:
            logger.info("Executing PTC code in sandbox")
            result = await self._ptc_executor.execute_code(code)

            if result.exit_code == 0:
                logger.info("PTC code execution completed successfully")
                payload = {
                    "ok": True,
                    "stdout": result.stdout,
                    "stderr": "",
                    "exit_code": 0,
                }
                return json.dumps(payload)

            logger.warning(f"PTC code execution failed with exit code {result.exit_code}")
            payload = {
                "ok": False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            }
            return json.dumps(payload)

        except Exception as e:
            logger.error(f"PTC code execution failed: {e}")
            payload = {
                "ok": False,
                "stdout": "",
                "stderr": f"Execution failed: {type(e).__name__}: {e}",
                "exit_code": 1,
            }
            return json.dumps(payload)

    async def cleanup(self) -> None:
        """Clean up the sandbox runtime."""
        await self._ptc_runtime.cleanup()


def create_execute_ptc_code_tool(
    mcp_client: "BaseMCPClient | None",
    config: "PTCSandboxConfig | None" = None,  # noqa: F821
    agent_tool_configs: dict[str, Any] | None = None,
) -> PTCCodeTool:
    r"""Create a tool that executes Python code with MCP tool access.

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
        result = await tool.ainvoke({"code": "from tools.yfinance import get_stock\\nprint(get_stock('AAPL'))"})
        ```
    """
    # Import here to avoid circular dependencies and allow lazy loading
    from aip_agents.ptc.executor import PTCSandboxConfig, PTCSandboxExecutor
    from aip_agents.sandbox.e2b_runtime import E2BSandboxRuntime

    # Use provided config or create default
    sandbox_config = config or PTCSandboxConfig()

    # Create runtime and executor
    runtime = E2BSandboxRuntime(
        template=sandbox_config.sandbox_template,
        ptc_packages=sandbox_config.ptc_packages,
    )
    executor = PTCSandboxExecutor(mcp_client, runtime, sandbox_config)

    return PTCCodeTool(
        executor=executor,
        runtime=runtime,
        agent_tool_configs=agent_tool_configs,
    )
