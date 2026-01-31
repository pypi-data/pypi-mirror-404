"""Persistent MCP Session wrapper for connection reuse.

This module implements persistent MCP sessions that reuse connections across
multiple tool calls, avoiding the session recreation overhead.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from gllm_tools.mcp.client.config import MCPConfiguration
from mcp import ClientSession
from mcp.types import CallToolResult, Tool

from aip_agents.mcp.client.connection_manager import MCPConnectionManager
from aip_agents.mcp.utils.config_validator import validate_allowed_tools_list
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class PersistentMCPSession:
    """Persistent MCP session that reuses connections.

    This session wrapper manages the connection lifecycle and caches tools
    to avoid repeated initialization overhead. It provides automatic reconnection
    and thread-safe operations.

    Tool Filtering:
        When allowed_tools is configured, tools are filtered inline during list_tools()
        and permission checked in call_tool() using set lookup.
    """

    def __init__(
        self,
        server_name: str,
        config: MCPConfiguration,
        allowed_tools: list[str] | None = None,
    ):
        """Initialize persistent session.

        Args:
            server_name: Name of the MCP server
            config: MCP server configuration
            allowed_tools: Optional list of tool names to allow. None or empty means all tools allowed.
        """
        self.server_name = server_name
        self.config = config
        self.connection_manager = MCPConnectionManager(server_name, config)
        self.client_session: ClientSession | None = None
        self.tools: list[Tool] = []

        # Keep only the set for fast permission checks
        validated_allowed = validate_allowed_tools_list(allowed_tools, "'allowed_tools' parameter")
        self._allowed_tools_set: set[str] | None = set(validated_allowed) if validated_allowed else None
        self._warned_unknown_tools: set[str] = set()
        self._filtered_tools_cache: list[Tool] | None = None  # Cache for filtered tools

        # Log allowed tools configuration
        if self._allowed_tools_set:
            logger.info(
                f"Session for '{server_name}' configured with {len(self._allowed_tools_set)} allowed tool(s): "
                f"{', '.join(sorted(self._allowed_tools_set))}"
            )
        else:
            logger.debug(f"Session for '{server_name}' allows all tools (no restriction)")

        self._initialized = False
        self._lock = asyncio.Lock()
        self._owner_task: asyncio.Task | None = None
        self._owner_ready: asyncio.Event = asyncio.Event()
        self._owner_exception: Exception | None = None
        self._timeout = float(config.get("timeout", 30.0))
        self._request_queue: asyncio.Queue[
            tuple[Callable[..., Awaitable[Any]], tuple[Any, ...], asyncio.Future, bool]
        ] = asyncio.Queue()

    async def initialize(self) -> None:
        """Initialize session once and cache tools.

        This method is idempotent and can be called multiple times safely.

        Raises:
            Exception: If session initialization fails
        """
        if self._initialized:
            return

        async with self._lock:
            # Double-check pattern
            if self._initialized:
                return
            if self._owner_task is None or self._owner_task.done():
                self._owner_ready = asyncio.Event()
                self._owner_exception = None
                self._owner_task = asyncio.create_task(self._owner_loop())

        try:
            await asyncio.wait_for(self._owner_ready.wait(), timeout=self._timeout)
        except asyncio.CancelledError:
            if self._owner_task and not self._owner_task.done():
                self._owner_task.cancel()
            raise
        except TimeoutError as e:
            logger.error(f"Initialization timed out for {self.server_name} after {self._timeout}s")
            if self._owner_task and not self._owner_task.done():
                self._owner_task.cancel()
            self._owner_exception = ConnectionError(
                f"Initialization timed out for {self.server_name} after {self._timeout}s"
            )
            self._owner_ready.set()
            raise self._owner_exception from e
        if self._owner_exception:
            raise self._owner_exception

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Call MCP tool using persistent session.

        Args:
            name (str): Tool name
            arguments (dict[str, Any]): Tool arguments

        Returns:
            CallToolResult: Tool call result

        Raises:
            Exception: If tool call fails
        """
        return await self._run_in_owner(self._call_tool_impl, name, arguments)

    async def _call_tool_impl(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Call MCP tool using the owner task.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            CallToolResult: Tool call result.
        """
        await self._ensure_connected_impl()

        if self._allowed_tools_set and name not in self._allowed_tools_set:
            allowed_display = ", ".join(sorted(self._allowed_tools_set))
            error_msg = (
                f"Tool '{name}' is not allowed on server '{self.server_name}' (allowed tools: {allowed_display})"
            )
            logger.warning(f"[{self.server_name}] Tool '{name}' blocked: not in allowed_tools ({allowed_display})")
            raise PermissionError(error_msg)

        try:
            logger.debug(f"Calling tool '{name}' on {self.server_name} with args: {arguments}")
            result = await self.client_session.call_tool(name, arguments)
            logger.debug(f"Tool '{name}' completed successfully")
            return result
        except Exception as e:
            self._handle_connection_error(e, f"Tool call '{name}'")

    async def read_resource(self, uri: str) -> Any:
        """Read an MCP resource using persistent session.

        Args:
            uri (str): The URI of the resource to read

        Returns:
            Any: The resource content

        Raises:
            Exception: If resource reading fails
        """
        return await self._run_in_owner(self._execute_read_resource_impl, uri)

    async def _execute_read_resource_impl(self, uri: str) -> Any:
        """Execute the reading of an MCP resource.

        Args:
            uri (str): The URI of the resource to read

        Returns:
            Any: The resource content

        Raises:
            Exception: If resource reading fails
        """
        await self._ensure_connected_impl()
        try:
            logger.debug(f"Reading resource '{uri}' on {self.server_name}")
            result = await self.client_session.read_resource(uri)
            logger.debug(f"Resource '{uri}' read successfully")
            return result
        except Exception as e:
            self._handle_connection_error(e, f"Reading resource '{uri}'")

    async def list_tools(self) -> list[Tool]:
        """Get cached tools list with allowed tools filtering applied.

        Returns:
            list[Tool]: a copy of list of available tools, filtered to only allowed tools if configured
        """
        return await self._run_in_owner(self._list_tools_impl)

    async def _list_tools_impl(self) -> list[Tool]:
        """Return the cached tools list from the owner task.

        Returns:
            list[Tool]: Filtered tool list if allowed tools are configured, otherwise all tools.
        """
        await self._ensure_connected_impl()

        if not self._allowed_tools_set:
            return list(self.tools)

        if self._filtered_tools_cache is None:
            self._filtered_tools_cache = [tool for tool in self.tools if tool.name in self._allowed_tools_set]

        return list(self._filtered_tools_cache)

    def get_tools_count(self) -> int:
        """Get count of allowed tools.

        Returns:
            Count of allowed tools
        """
        if not self._allowed_tools_set:
            return len(self.tools)

        if self._filtered_tools_cache is not None:
            return len(self._filtered_tools_cache)

        return sum(1 for tool in self.tools if tool.name in self._allowed_tools_set)

    async def ensure_connected(self) -> None:
        """Ensure connection is healthy, reconnect if needed.

        This method provides automatic reconnection capability.

        Raises:
            Exception: If reconnection fails
        """
        await self._run_in_owner(self._ensure_connected_impl)

    async def _ensure_connected_impl(self) -> None:
        """Ensure the session is connected, reconnecting if needed."""
        if not self._initialized or not self.connection_manager.is_connected:
            logger.info(f"Reconnecting session for {self.server_name}")
            await self._initialize_impl()

    def _handle_connection_error(self, e: Exception, operation: str) -> None:
        """Handle connection-related errors with logging and reconnection marking.

        Args:
            e (Exception): The exception that occurred
            operation (str): The operation that failed
        """
        logger.error(f"{operation} failed on {self.server_name}: {e}")
        if not self.connection_manager.is_connected:
            logger.info(f"Connection lost for {self.server_name}, marking for reconnection")
            self._initialized = False
        raise ConnectionError(f"{operation} failed on {self.server_name}: {str(e)}") from e

    async def disconnect(self) -> None:
        """Disconnect session gracefully.

        This method cleans up all resources and connections.
        Always succeeds, even if the session was already in an error state.
        """
        logger.info(f"Disconnecting session for {self.server_name}")

        if self._owner_task is None or self._owner_task.done():
            await self._disconnect_impl()
            return

        try:
            await self._run_in_owner(self._disconnect_impl, shutdown=True, ensure_initialized=False)
        except ConnectionError:
            # Owner task already failed; just clean up directly
            logger.debug(f"Owner task already failed for {self.server_name}, cleaning up directly")
            await self._disconnect_impl()
        finally:
            await self._await_owner_shutdown()

    async def _await_owner_shutdown(self) -> None:
        """Wait for the owner task to exit, cancelling on timeout."""
        if not self._owner_task:
            return

        owner_task = self._owner_task
        try:
            await asyncio.wait_for(owner_task, timeout=self._timeout)
        except TimeoutError:
            logger.warning(f"Owner task for {self.server_name} did not exit within {self._timeout}s, cancelling")
            owner_task.cancel()
            try:
                await owner_task
            except (asyncio.CancelledError, Exception):
                pass
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            self._owner_task = None

    async def _cleanup_on_error(self) -> None:
        """Internal cleanup method for error scenarios."""
        try:
            if self.client_session:
                await self.client_session.__aexit__(None, None, None)
                self.client_session = None
        except Exception as e:
            logger.debug(f"Ignored cleanup error for client_session: {e}")

        try:
            await self.connection_manager.stop()
        except Exception as e:
            logger.debug(f"Ignored cleanup error for connection_manager: {e}")

        self._initialized = False
        self.tools.clear()
        self._filtered_tools_cache = None  # Clear cache on error cleanup

    @property
    def is_initialized(self) -> bool:
        """Check if session is initialized.

        Returns:
            bool: True if initialized and connected, False otherwise
        """
        return self._initialized and self.connection_manager.is_connected

    @property
    def allowed_tools(self) -> list[str] | None:
        """Return the configured allowed tools, sorted if present.

        Returns:
            Sorted list of allowed tool names, or None if unrestricted.
        """
        if not self._allowed_tools_set:
            return None
        return sorted(self._allowed_tools_set)

    def update_allowed_tools(self, allowed_tools: list[str] | None) -> bool:
        """Update the list of allowed tools for this session.

        Args:
            allowed_tools: New list of allowed tool names or None for no restriction.
                None and empty list both mean 'no restrictions, allow all tools'.

        Returns:
            bool: True if the configuration changed, False otherwise.

        Raises:
            ValueError: If allowed_tools contains invalid entries.
        """
        # Validate first - ensures consistent error handling regardless of current state
        validated = validate_allowed_tools_list(allowed_tools, f"Server '{self.server_name}'")
        new_set = set(validated) if validated else None

        # Check if actually changed
        if self._allowed_tools_set == new_set:
            logger.debug(f"Allowed tools unchanged for {self.server_name}")
            return False

        # Log and update
        old_display = sorted(self._allowed_tools_set) if self._allowed_tools_set else None
        self._allowed_tools_set = new_set
        self._filtered_tools_cache = None  # Invalidate cache when allowed_tools changes
        logger.debug(f"Updated allowed_tools for {self.server_name}: {old_display} -> {validated}")

        # Warn immediately if we already have cached tools
        if self.tools:
            self._warn_on_unknown_allowed_tools(validated, self.tools)
        return True

    def _warn_on_unknown_allowed_tools(self, allowed_tools: list[str] | None, available_tools: list[Tool]) -> None:
        """Emit warnings for allowed tool names that are not exposed by the server.

        Warnings are deduplicated - each unknown tool is only warned about once per session.

        Args:
            allowed_tools: Configured whitelist of tool names, or None for no restriction.
            available_tools: Tools currently exposed by the server.
        """
        if not allowed_tools or not available_tools:
            return

        available_names = {tool.name for tool in available_tools}
        unknown = [tool_name for tool_name in allowed_tools if tool_name not in available_names]
        for tool_name in unknown:
            # Only warn once per tool name
            if tool_name not in self._warned_unknown_tools:
                self._warned_unknown_tools.add(tool_name)
                logger.warning(
                    f"[{self.server_name}] Tool '{tool_name}' not found in available tools but specified in allowed_tools"
                )

    async def _owner_loop(self) -> None:
        """Run the owner task loop and process queued requests.

        Returns:
            None
        """
        shutdown_requested = False
        try:
            shutdown_requested = await self._initialize_owner()
            if shutdown_requested:
                return

            while True:
                func, args, future, shutdown = await self._request_queue.get()
                if await self._process_owner_request(func, args, future):
                    continue
                if shutdown:
                    shutdown_requested = True
                    break
        finally:
            # Drain and cancel any pending requests to avoid hanging callers
            await self._drain_pending_requests()
            if not shutdown_requested and (
                self._initialized or self.client_session or self.connection_manager.transport_type is not None
            ):
                await self._cleanup_on_error()
            self._owner_task = None

    async def _drain_pending_requests(self) -> None:
        """Cancel all pending requests in the queue.

        This prevents callers from hanging when the owner loop exits unexpectedly.
        """
        error = ConnectionError(f"Session for {self.server_name} is shutting down")
        while not self._request_queue.empty():
            try:
                _, _, future, _ = self._request_queue.get_nowait()
                if not future.done():
                    future.set_exception(error)
            except asyncio.QueueEmpty:
                break

    async def _initialize_owner(self) -> bool:
        """Initialize the owner task and signal readiness.

        Returns:
            bool: True when initialization fails and the loop should stop.
        """
        try:
            await self._initialize_impl()
        except Exception as e:
            self._owner_exception = e
            self._owner_ready.set()
            return True

        self._owner_ready.set()
        return False

    async def _process_owner_request(
        self,
        func: Callable[..., Awaitable[Any]],
        args: tuple[Any, ...],
        future: asyncio.Future,
    ) -> bool:
        """Process a single queued request.

        Args:
            func: Coroutine function to execute.
            args: Positional arguments for the function.
            future: Future to resolve with the result or exception.

        Returns:
            bool: True if the request was skipped due to cancellation.
        """
        if future.cancelled():
            return True

        try:
            result = await func(*args)
        except asyncio.CancelledError as e:
            # Owner task was cancelled - resolve future to prevent hanging caller
            if not future.cancelled():
                future.set_exception(e)
            raise
        except Exception as e:
            if not future.cancelled():
                future.set_exception(e)
        else:
            if not future.cancelled():
                future.set_result(result)
        return False

    async def _run_in_owner(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        shutdown: bool = False,
        ensure_initialized: bool = True,
    ) -> Any:
        """Execute a coroutine on the owner task.

        Args:
            func: Coroutine function to execute.
            *args: Positional arguments to pass to func.
            shutdown: Whether this request should shut down the owner loop.
            ensure_initialized: Whether to initialize the owner task if needed.

        Returns:
            Any: The result of the coroutine call.

        Raises:
            ConnectionError: If the owner task died or session is shutting down.
        """
        if ensure_initialized:
            await self.initialize()
        else:
            # For non-init calls (like disconnect), check if owner is alive
            if self._owner_task is None or self._owner_task.done():
                return await func(*args)
            try:
                await asyncio.wait_for(self._owner_ready.wait(), timeout=self._timeout)
            except TimeoutError as e:
                # Owner task is stuck, cancel it and raise
                if self._owner_task and not self._owner_task.done():
                    self._owner_task.cancel()
                raise ConnectionError(
                    f"Session for {self.server_name} initialization timed out after {self._timeout}s"
                ) from e
            if self._owner_exception:
                # Propagate the error instead of silently returning None
                raise ConnectionError(
                    f"Session for {self.server_name} failed: {self._owner_exception}"
                ) from self._owner_exception

        # Check if owner task died after initialization (race condition guard)
        if self._owner_task is None or self._owner_task.done():
            raise ConnectionError(f"Session for {self.server_name} is no longer active")

        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        await self._request_queue.put((func, args, future, shutdown))
        return await future

    async def _initialize_impl(self) -> None:
        """Initialize the underlying MCP session on the owner task."""
        if self._initialized:
            return

        try:
            logger.info(f"Initializing persistent session for {self.server_name}")

            # Start connection manager
            read_stream, write_stream = await self.connection_manager.start()

            # Create client session
            self.client_session = ClientSession(read_stream, write_stream)
            await self.client_session.__aenter__()

            # MCP handshake
            result = await self.client_session.initialize()
            logger.debug(f"MCP handshake complete for {self.server_name}: {result.capabilities}")

            # Discover and cache tools
            if result.capabilities.tools:
                tools_result = await self.client_session.list_tools()
                self.tools = tools_result.tools if tools_result else []
                self._filtered_tools_cache = None  # Invalidate cache when tools change
                logger.info(f"Cached {len(self.tools)} tools for {self.server_name}")
            else:
                logger.info(f"No tools available for {self.server_name}")

            # Warn once per initialization if allowed_tools references unknown names
            if self._allowed_tools_set:
                self._warn_on_unknown_allowed_tools(list(self._allowed_tools_set), self.tools)

            # Discover resources (for future use)
            if result.capabilities.resources:
                try:
                    resources_result = await self.client_session.list_resources()
                    if resources_result and resources_result.resources:
                        logger.debug(f"Found {len(resources_result.resources)} resources for {self.server_name}")
                except Exception:
                    logger.debug(f"Could not list resources for {self.server_name}, skipping")

            self._initialized = True
            logger.info(f"Session initialization complete for {self.server_name}")

        except Exception as e:
            logger.error(f"Failed to initialize session for {self.server_name}: {e}", exc_info=True)
            await self._cleanup_on_error()
            raise ConnectionError(f"Failed to initialize MCP session for {self.server_name}: {str(e)}") from e

    async def _disconnect_impl(self) -> None:
        """Disconnect the underlying MCP session on the owner task."""
        try:
            # Close client session
            if self.client_session:
                try:
                    await self.client_session.__aexit__(None, None, None)
                except Exception as e:
                    logger.warning(f"Error closing client session for {self.server_name}: {e}")
                self.client_session = None

            # Stop connection manager
            await self.connection_manager.stop()

        except Exception as e:
            logger.error(f"Error during disconnect for {self.server_name}: {e}")
        finally:
            self._initialized = False
            self.tools.clear()
            self._filtered_tools_cache = None  # Clear cache on disconnect
            logger.info(f"Session disconnected for {self.server_name}")
