"""LangGraph Memory Enhancer Agent.

This module implements the ``LangGraphMemoryEnhancerAgent``, a dedicated LangGraph helper agent
that automatically augments user queries with relevant memories before the primary agent runs.
It replaces manual memory tool invocation with a consistent preprocessing layer.

Authors:
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

import json
import textwrap
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from aip_agents.agent.langgraph_react_agent import LangGraphReactAgent
from aip_agents.agent.system_instruction_context import get_current_date_context
from aip_agents.memory.guidance import MEM0_MEMORY_RECALL_GUIDANCE
from aip_agents.tools.memory_search_tool import (
    MEMORY_DELETE_TOOL_NAME,
    MEMORY_SEARCH_TOOL_NAME,
    LongTermMemorySearchTool,
    Mem0DeleteTool,
    Mem0SearchTool,
)
from aip_agents.utils.langgraph import (
    convert_langchain_messages_to_gllm_messages,
    convert_lm_output_to_langchain_message,
)
from aip_agents.utils.logger import get_logger

logger = get_logger(__name__)


class LangGraphMemoryEnhancerAgent(LangGraphReactAgent):
    """Simplified mini-agent for automatic memory retrieval or deletion and query enhancement.

    This agent has a simple 2-node LangGraph (agent + tools) and uses existing memory
    infrastructure to enhance user queries with relevant context. It acts as a
    preprocessing layer that automatically attempts memory retrieval for every query.

    Key features:
    - Uses runtime `memory_user_id` provided via call arguments (no static storage)
    - Uses simplified instruction reusing existing guidance
    - Standard 2-node LangGraph pattern (agent -> tools -> agent)
    - Automatically enhances queries with memory context when available
    - Returns original query unchanged if no relevant memories found
    """

    def __init__(self, memory, **kwargs) -> None:
        """Initialize the LangGraphMemoryEnhancerAgent with memory backend and configuration.

        Args:
            memory: Memory backend instance (Mem0Memory or compatible)
            **kwargs: Additional arguments passed to BaseLangGraphAgent, including:
                - memory_agent_id: Fallback user ID for memory operations
                - model: LLM model to use for memory decisions
                - Other BaseLangGraphAgent parameters
        """
        memory_search_tool: LongTermMemorySearchTool = Mem0SearchTool(
            memory=memory,
            default_user_id=kwargs.get("memory_agent_id"),
            user_id_provider=None,
        )
        memory_delete_tool: LongTermMemorySearchTool = Mem0DeleteTool(
            memory=memory,
            default_user_id=kwargs.get("memory_agent_id"),
            user_id_provider=None,
        )
        kwargs["save_interaction_to_memory"] = False
        super().__init__(
            name="LangGraphMemoryEnhancerAgent",
            instruction=self._build_simple_instruction(),
            tools=[memory_search_tool, memory_delete_tool],
            **kwargs,
        )

    def _build_simple_instruction(self) -> str:
        """Build simplified memory recall instruction reusing existing components.

        Returns:
            str: Complete instruction including date context and memory guidance
        """
        date_context = get_current_date_context()

        instruction = textwrap.dedent(f"""
        {date_context}

        You are a Memory Controller Agent that decides whether to retrieve or delete memory.

        Important: You WILL NOT see the tool results. The system will either append retrieved memory
        to the user input or return a memory action summary after your turn. Your sole responsibility
        is to trigger the correct tool calls with concise arguments based on the user's message.

        What to do:
        1. Read the user's message as-is (do not rephrase it).
        2. Decide which tool to call:
           - Use `built_in_mem0_search` to retrieve memory for answering questions.
           - Use `built_in_mem0_delete` when the user asks to forget/delete memories.
           Prefer a single call, but you MAY make multiple calls when clearly needed.
           - If the user implies a time frame (e.g., "yesterday", "last week"), set `start_date`/`end_date`.
           - If the user implies a precise range, set `start_date`/`end_date` (YYYY-MM-DD).
           - If the user mentions a topic, set a concise `query` (few words or at most a sentence).
           - Adjust `limit` to higher number to allow more memory to be retrieved if needed.
           - Default when uncertain: omit dates, set a concise `query` derived from the message,
             and set `limit=10`.
        3. Do NOT answer the user's question. Do NOT summarize. Do NOT format output. The system will handle it.

        Constraints:
        - Keep tool arguments succinct and precise; avoid verbose or speculative queries.
        - Never invent facts. If unsure about time ranges, prefer omitting dates rather than fabricating.
        - Do not include any preambles or explanations in your messages.
         - Make one or more tool calls as needed; avoid duplicates or redundant calls.

        Reference guidance:
        {MEM0_MEMORY_RECALL_GUIDANCE}
        """).strip()

        return instruction

    async def _memory_retrieval_node(self, state: dict, config: dict | None = None) -> dict:
        """Execute memory retrieval or deletion using explicit tool calls or synthesized defaults.

        Args:
            state: LangGraph state containing the conversation `messages` history.
            config: Optional LangGraph configuration forwarded to the memory tool.

        Returns:
            dict: State update whose `messages` list contains `ToolMessage` outputs.
        """
        messages = state.get("messages", [])
        tool_calls = self._extract_mem0_tool_calls(messages)

        if tool_calls:
            tool_messages = await self._execute_mem0_tool_calls(tool_calls, state, config)
            return {"messages": tool_messages}

        default_query = self._extract_last_human_query(messages)
        tool_messages = await self._execute_default_retrieval(default_query, state, config)
        return {"messages": tool_messages}

    def _extract_mem0_tool_calls(self, messages: list) -> list[dict[str, Any]]:
        """Return all Mem0 tool calls from the last message if present.

        Args:
            messages: Ordered list of LangChain message objects representing the state.

        Returns:
            List of tool call dictionaries filtered for the Mem0 search tool.
        """
        if not messages:
            return []

        last_message = messages[-1]
        tool_calls = getattr(last_message, "tool_calls", None)
        if not tool_calls:
            return []

        return [tc for tc in tool_calls if tc.get("name") in {MEMORY_SEARCH_TOOL_NAME, MEMORY_DELETE_TOOL_NAME}]

    async def _execute_mem0_tool_calls(
        self,
        tool_calls: list[dict[str, Any]],
        state: dict,
        config: dict | None,
    ) -> list[ToolMessage]:
        """Execute the provided Mem0 tool calls and return their messages.

        Args:
            tool_calls: Tool call dictionaries emitted by the LLM.
            state: LangGraph state containing messages and metadata.
            config: Optional runnable configuration forwarded to the tool.

        Returns:
            List of `ToolMessage` objects describing each execution result.
        """
        tool_messages: list[ToolMessage] = []
        delete_intent: dict[str, Any] | None = None
        user_query = self._extract_last_human_query(state.get("messages", [])) or self._fallback_query(
            state.get("messages", [])
        )
        for index, tool_call in enumerate(tool_calls):
            tool_name = tool_call.get("name") or MEMORY_SEARCH_TOOL_NAME
            args = dict(tool_call.get("args") or {})
            if "id" not in args and "id" in tool_call:
                args["id"] = tool_call["id"]
            log_args = self._redact_mem0_args(tool_name, args)
            logger.info("Executing memory tool call #%s name=%s args=%s", index, tool_name, log_args)
            if tool_name == MEMORY_DELETE_TOOL_NAME:
                delete_intent = delete_intent or await self._preprocess_delete_intent(user_query, state, config)
                if not self._is_delete_intent_confirmed(delete_intent):
                    tool_messages.append(self._build_delete_confirmation_message(tool_call, user_query))
                    continue
            tool_messages.append(await self._execute_mem0_call(tool_name, args, state, config))
        return tool_messages

    def _redact_mem0_args(self, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Redact sensitive fields from Mem0 tool args before logging."""
        if tool_name != MEMORY_DELETE_TOOL_NAME:
            return args

        redacted_args = dict(args)
        if "memory_ids" in redacted_args:
            memory_ids = redacted_args.pop("memory_ids")
            if isinstance(memory_ids, list):
                redacted_args["memory_ids_count"] = len(memory_ids)
            else:
                redacted_args["memory_ids_count"] = 0
        return redacted_args

    async def _execute_default_retrieval(
        self,
        default_query: str | None,
        state: dict,
        config: dict | None,
    ) -> list[ToolMessage]:
        """Perform a default retrieval when the LLM does not request tools.

        Args:
            default_query: Latest human utterance content or ``None`` if unavailable.
            state: LangGraph state with message history and metadata.
            config: Optional runnable configuration forwarded to the tool.

        Returns:
            Single-item list containing the resulting `ToolMessage`.
        """
        args = self._build_default_mem0_args(default_query)
        tool_message = await self._execute_mem0_call(MEMORY_SEARCH_TOOL_NAME, args, state, config)
        return [tool_message]

    def _build_default_mem0_args(self, query: str | None) -> dict[str, Any]:
        """Create safe default arguments for the Mem0 search tool.

        Args:
            query: Latest human utterance used to derive the search query.

        Returns:
            Dictionary of keyword arguments passed to the Mem0 search tool.
        """
        if query:
            trimmed_query = query[:128]
        else:
            trimmed_query = None

        return {"query": trimmed_query, "limit": 10}

    async def _execute_mem0_call(
        self,
        tool_name: str,
        args: dict[str, Any],
        state: dict,
        config: dict | None,
    ) -> ToolMessage:
        """Execute a single Mem0 tool call with metadata resolution.

        Args:
            tool_name: Name of the memory tool to invoke.
            args: Base arguments supplied by the LLM or synthesized defaults.
            state: LangGraph state that may include additional metadata.
            config: Optional runnable configuration forwarded to the tool.

        Returns:
            `ToolMessage` containing raw tool output or an error description.
        """
        args_with_metadata = self._merge_metadata(args, state, tool_name)
        tool_config = self._create_tool_config(config, state, tool_name=tool_name)
        try:
            mem0_tool = self._get_tool_by_name(tool_name)
            result = await mem0_tool.ainvoke(args_with_metadata, config=tool_config)
            content = str(result)
        except Exception as exc:
            content = f"Error executing memory tool '{tool_name}': {exc}"

        return ToolMessage(content=content, tool_call_id=args.get("id", ""))

    def _merge_metadata(self, args: dict[str, Any], state: dict, tool_name: str) -> dict[str, Any]:
        """Merge resolved metadata into tool arguments.

        Args:
            args: Tool arguments that may already include metadata.
            state: LangGraph state providing globally resolved metadata values.
            tool_name: Name of the tool requesting metadata (used to resolve tool-specific metadata).

        Returns:
            Copy of ``args`` containing merged metadata entries.
        """
        args_with_metadata = dict(args)
        effective_metadata = self._resolve_effective_metadata(state, tool_name)
        if not effective_metadata:
            return args_with_metadata

        existing_metadata = args_with_metadata.get("metadata")
        if isinstance(existing_metadata, dict):
            merged_metadata = {**effective_metadata, **existing_metadata}
        else:
            merged_metadata = effective_metadata

        args_with_metadata["metadata"] = merged_metadata
        return args_with_metadata

    def _resolve_effective_metadata(self, state: dict, tool_name: str) -> dict[str, Any] | None:
        """Resolve metadata for the Mem0 tool, swallowing resolution errors.

        Args:
            state: LangGraph state whose ``metadata`` key may include overrides.
            tool_name: Name of the tool whose metadata resolution strategy should be used.

        Returns:
            Resolved metadata dictionary or ``None`` if not available.
        """
        raw_metadata = state.get("metadata")
        if not isinstance(raw_metadata, dict):
            return None

        try:
            return self._resolve_tool_metadata(tool_name, raw_metadata)
        except Exception:
            return None

    def _extract_last_human_query(self, messages: list) -> str | None:
        """Return the content of the most recent `HumanMessage` if available.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            Text content of the last human message or ``None``.
        """
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                if isinstance(message.content, str):
                    return message.content
                return str(message.content)
        return None

    def _finalize_node(self, state: dict) -> dict:
        """Assemble the enhanced query returned by the memory recall agent.

        Collects raw memory results from all tool calls, deduplicates by memory ID,
        formats the unique memories, and combines with the original user query.

        Args:
            state: LangGraph state containing the original conversation messages and the
                tool outputs generated by `_memory_retrieval_node`.

        Returns:
            dict: State update with a single `AIMessage` that concatenates the original user
                query and any deduplicated memory context.
        """
        messages = state.get("messages", [])
        original_query = self._extract_last_human_query(messages) or self._fallback_query(messages)
        delete_action = self._extract_delete_action(messages)
        if delete_action:
            action_block = self._format_memory_action(delete_action)
            return {"messages": [AIMessage(content=action_block)]}

        delete_error = self._extract_delete_error(messages)
        if delete_error:
            action_block = self._format_memory_action_error(delete_error)
            return {"messages": [AIMessage(content=action_block)]}

        memories = self._collect_unique_memories(messages)
        tagged_memory = self._format_memories(memories)

        final_text = (f"{original_query}\n\n" + tagged_memory).strip()
        return {"messages": [AIMessage(content=final_text)]}

    def _fallback_query(self, messages: list) -> str:
        """Fallback to the last message content when no human message is present.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            The string representation of the last message content.
        """
        if not messages:
            return ""
        last_message = messages[-1]
        content = getattr(last_message, "content", "")
        return content if isinstance(content, str) else str(content)

    def _collect_unique_memories(self, messages: list) -> list[dict[str, Any]]:
        """Collect and deduplicate memory hits from tool messages.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            List of memory dictionaries with unique memory identifiers.
        """
        unique_memories: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for message in messages:
            for memory in self._extract_memories_from_message(message):
                memory_id = memory.get("id")
                if not memory_id or memory_id in seen_ids:
                    continue

                seen_ids.add(memory_id)
                unique_memories.append(memory)

        return unique_memories

    def _extract_memories_from_message(self, message: Any) -> list[dict[str, Any]]:
        """Return parsed memory dictionaries contained in a tool message.

        Args:
            message: Message instance that may contain memory tool output.

        Returns:
            List of memory dictionaries or an empty list when no memories are present.
        """
        if not isinstance(message, ToolMessage):
            return []

        raw_results = self._parse_tool_message_json(message)
        if isinstance(raw_results, list):
            return [memory for memory in raw_results if isinstance(memory, dict)]
        return []

    def _parse_tool_message_json(self, message: ToolMessage) -> Any:
        """Parse the JSON content of a tool message.

        Args:
            message: Tool message emitted by the memory search tool.

        Returns:
            List extracted from the tool message content or an empty list on failure.
        """
        try:
            raw_results = json.loads(message.content)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning(
                "Failed to parse tool result as JSON: %s, content: %s...",
                exc,
                message.content[:200],
            )
            return None

        return raw_results

    def _extract_delete_action(self, messages: list) -> dict[str, Any] | None:
        """Return delete action details if a delete tool message is present.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            Action dict or None when no delete action is detected.
        """
        for message in messages:
            if not isinstance(message, ToolMessage):
                continue
            raw_payload = self._parse_tool_message_json(message)
            if not isinstance(raw_payload, dict):
                continue
            status = raw_payload.get("status")
            if status == "success" and raw_payload.get("mode"):
                return raw_payload
            if status == "needs_confirmation":
                return raw_payload
        return None

    def _format_memory_action(self, action: dict[str, Any]) -> str:
        """Format a memory action block for delete results.

        Args:
            action: Parsed action payload from the delete tool.

        Returns:
            Formatted action block string.
        """
        status = action.get("status", "success")
        summary = action.get("summary")
        if status == "needs_confirmation":
            summary = summary or "Do you want me to delete the related memories?"
        else:
            mode = action.get("mode", "unknown")
            result = action.get("result")
            summary = summary or f"Deleted memories (mode: {mode})."
            if isinstance(result, dict):
                count = result.get("count") or result.get("deleted") or result.get("total")
                if count is not None:
                    summary = f"Deleted {count} memories (mode: {mode})."
        return "\n".join(
            [
                "<MEMORY_ACTION>",
                "action=delete",
                f"status={status}",
                f"summary={summary}",
                "</MEMORY_ACTION>",
            ]
        )

    def _extract_delete_error(self, messages: list) -> str | None:
        """Return delete error summary if delete tool failed.

        Args:
            messages: Ordered message history produced during the graph run.

        Returns:
            Error summary string or None when no delete error is detected.
        """
        for message in messages:
            if not isinstance(message, ToolMessage):
                continue
            content = message.content if isinstance(message.content, str) else str(message.content)
            if MEMORY_DELETE_TOOL_NAME in content and "Error" in content:
                return content[:200]
        return None

    def _format_memory_action_error(self, error_summary: str) -> str:
        """Format a memory action block for delete errors."""
        safe_summary = error_summary.replace("\n", " ").strip()
        return "\n".join(
            [
                "<MEMORY_ACTION>",
                "action=delete",
                "status=error",
                f"summary={safe_summary}",
                "</MEMORY_ACTION>",
            ]
        )

    def _get_tool_by_name(self, tool_name: str) -> Any:
        """Return the resolved tool instance by name."""
        for tool in self.resolved_tools:
            if tool.name == tool_name:
                return tool
        raise ValueError(f"Tool '{tool_name}' not found in resolved tools.")

    async def _preprocess_delete_intent(
        self,
        query: str | None,
        state: dict,
        config: dict | None,
    ) -> dict[str, Any]:
        """Run a pre-processing intent check for delete requests.

        Args:
            query: Latest user query.
            state: LangGraph state containing metadata for the request.
            config: Optional runnable configuration forwarded to the model.

        Returns:
            Normalized intent payload with intent/confidence/reason keys.
        """
        if not isinstance(query, str) or not query.strip():
            return {"intent": "unknown", "confidence": "low", "reason": "empty_query"}

        raw_response = await self._invoke_delete_intent_model(query, state, config)
        return self._parse_delete_intent_payload(raw_response)

    async def _invoke_delete_intent_model(
        self,
        query: str,
        state: dict,
        config: dict | None,
    ) -> str:
        """Invoke the configured model to classify delete intent.

        Args:
            query: User query to classify.
            state: LangGraph state containing request metadata.
            config: Optional runnable configuration forwarded to the model.

        Returns:
            Raw model output string, or empty string on failure.
        """
        instruction = self._build_delete_intent_instruction()
        effective_event_emitter = state.get("event_emitter") or self.event_emitter
        if self.lm_invoker is not None:
            return await self._invoke_delete_intent_with_invoker(query, instruction, effective_event_emitter)

        if isinstance(self.model, BaseChatModel):
            return await self._invoke_delete_intent_with_chat_model(query, instruction, config)

        logger.warning("Delete intent check skipped; no model configured.")
        return ""

    async def _invoke_delete_intent_with_invoker(
        self,
        query: str,
        instruction: str,
        event_emitter: Any,
    ) -> str:
        """Invoke delete intent check using an LM invoker."""
        messages = convert_langchain_messages_to_gllm_messages([HumanMessage(content=query)], instruction)
        restore_tools = self.resolved_tools if self.resolved_tools else None
        if restore_tools is not None:
            self.lm_invoker.set_tools([])
        try:
            lm_output = await self.lm_invoker.invoke(messages=messages, event_emitter=event_emitter)
        except Exception as exc:
            logger.warning("Delete intent check failed: %s", exc)
            return ""
        finally:
            if restore_tools is not None:
                self.lm_invoker.set_tools(restore_tools)

        ai_message = convert_lm_output_to_langchain_message(lm_output)
        return self._coerce_message_content(ai_message)

    async def _invoke_delete_intent_with_chat_model(
        self,
        query: str,
        instruction: str,
        config: dict | None,
    ) -> str:
        """Invoke delete intent check using a LangChain chat model."""
        prompt = [SystemMessage(content=instruction), HumanMessage(content=query)]
        try:
            ai_message = await self.model.ainvoke(prompt, config)
        except Exception as exc:
            logger.warning("Delete intent check failed: %s", exc)
            return ""
        return self._coerce_message_content(ai_message)

    def _parse_delete_intent_payload(self, content: str) -> dict[str, Any]:
        """Parse delete intent payload from model output."""
        default_payload = {"intent": "unknown", "confidence": "low", "reason": "unparsed"}
        if not isinstance(content, str) or not content.strip():
            return default_payload

        payload = self._extract_json_payload(content)
        if not isinstance(payload, dict):
            return default_payload

        return self._normalize_delete_intent_payload(payload, default_payload)

    def _extract_json_payload(self, content: str) -> dict[str, Any] | None:
        """Extract a JSON payload from a raw string."""
        raw_text = content.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.lower().startswith("json"):
                raw_text = raw_text[4:].strip()

        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                return json.loads(raw_text[start : end + 1])
            except json.JSONDecodeError:
                return None

    def _normalize_delete_intent_payload(
        self,
        payload: dict[str, Any],
        default_payload: dict[str, str],
    ) -> dict[str, Any]:
        """Normalize payload keys and guard against invalid values."""
        intent = str(payload.get("intent", "")).lower()
        confidence = str(payload.get("confidence", "")).lower()
        if intent not in {"delete", "retrieve", "unknown"}:
            intent = "unknown"
        if confidence not in {"high", "medium", "low"}:
            confidence = "low"

        reason = payload.get("reason")
        if not isinstance(reason, str):
            reason = default_payload["reason"]

        return {"intent": intent, "confidence": confidence, "reason": reason}

    @staticmethod
    def _coerce_message_content(message: AIMessage) -> str:
        """Normalize AI message content into a string."""
        content = message.content
        return content if isinstance(content, str) else str(content)

    def _build_delete_intent_instruction(self) -> str:
        """Return the system prompt for delete intent classification.

        Design rationale:
        - Require JSON-only output for deterministic parsing.
        - Use intent labels (delete|retrieve|unknown) to avoid keyword false positives.
        - Gate deletion on high confidence to keep ambiguous requests safe.

        Tuning guidance:
        - Add examples if delete intents are missed.
        - Adjust confidence thresholds if false negatives become frequent.
        """
        return (
            "You are a memory deletion intent checker. Determine whether the user is asking to "
            "delete/forget memories stored about them. Reply with JSON only: "
            '{"intent": "delete|retrieve|unknown", "confidence": "high|medium|low", '
            '"reason": "short"}. '
            "If unsure, respond with intent unknown and low confidence."
        )

    def _is_delete_intent_confirmed(self, decision: dict[str, Any] | None) -> bool:
        """Return True when delete intent is confirmed by pre-processing."""
        if not isinstance(decision, dict):
            logger.warning("Delete intent check failed: decision is not a dict.")
            return False
        intent = decision.get("intent")
        confidence = decision.get("confidence")
        reason = decision.get("reason", "unknown")
        if intent != "delete":
            logger.info("Delete intent not confirmed: intent=%s reason=%s.", intent, reason)
            return False
        if confidence != "high":
            logger.info("Delete intent not confirmed: confidence=%s reason=%s.", confidence, reason)
            return False
        return True

    def _build_delete_confirmation_message(self, tool_call: dict[str, Any], query: str | None) -> ToolMessage:
        """Return a ToolMessage asking for delete confirmation."""
        summary = "Do you want me to delete the related memories?"
        if isinstance(query, str) and query.strip():
            trimmed = query.strip()
            if len(trimmed) > 160:
                trimmed = f"{trimmed[:157]}..."
            summary = f"Do you want me to delete memories related to: '{trimmed}'?"
        payload = {"status": "needs_confirmation", "summary": summary}
        return ToolMessage(content=json.dumps(payload), tool_call_id=tool_call.get("id", ""))

    def _format_memories(self, memories: list[dict[str, Any]]) -> str:
        """Format memory hits using the underlying tool formatter.

        Args:
            memories: Deduplicated list of memory dictionaries.

        Returns:
            Tagged string representation of the relevant memories.
        """
        if not memories:
            return ""
        return self.resolved_tools[0].format_hits(memories, with_tag=True)

    def define_graph(self, graph_builder: StateGraph) -> CompiledStateGraph:
        """Define the 3-node memory recall LangGraph for this agent.

        This creates a streamlined ReAct-inspired structure that reuses
        `LangGraphReactAgent` helpers for robust LM invocation, token usage tracking,
        error handling, and tool execution.

        Args:
            graph_builder: LangGraph `StateGraph` builder instance used to register nodes and
                edges for compilation.

        Returns:
            CompiledStateGraph: The compiled memory recall graph ready for execution.
        """
        # Reuse parent's robust node implementations
        # Simple 3-step structure for single pass: agent -> memory_retrieval -> finalize -> END
        agent_node = self._create_agent_node()  # Handles LM invoker + LangChain + token usage
        graph_builder.add_node("agent", agent_node)
        graph_builder.add_node("memory_retrieval", self._memory_retrieval_node)
        graph_builder.add_node("finalize", self._finalize_node)
        graph_builder.add_edge("agent", "memory_retrieval")
        graph_builder.add_edge("memory_retrieval", "finalize")
        graph_builder.add_edge("finalize", END)
        graph_builder.set_entry_point("agent")

        return graph_builder.compile(checkpointer=self.checkpointer)
