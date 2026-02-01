"""LangGraph adapter for tool interception.

Intercepts LangGraph tool execution via langchain_core.tools.BaseTool.

LangGraph uses LangChain's tool infrastructure, so we patch BaseTool.invoke().
For approval workflows, LangGraph provides native support via:
- interrupt() for human-in-the-loop
- Checkpointing for state persistence

Architectural rules:
- Adapter is DUMB plumbing
- Adapter calls ONE SDK entrypoint: execute_governed_tool()
- SDK orchestrates everything
- No governance logic in adapter
- For approval: Use LangGraph's native interrupt() mechanism
"""

from typing import Any
import json

import structlog

from cortexhub.adapters.base import ToolAdapter
from cortexhub.pipeline import govern_execution

logger = structlog.get_logger(__name__)

# Attribute names for storing originals on class
_ORIGINAL_INVOKE_ATTR = "__cortexhub_original_invoke__"
_PATCHED_ATTR = "__cortexhub_patched__"
_ORIGINAL_CHAT_INVOKE_ATTR = "__cortexhub_original_chat_invoke__"
_ORIGINAL_CHAT_AINVOKE_ATTR = "__cortexhub_original_chat_ainvoke__"
_PATCHED_LLM_ATTR = "__cortexhub_llm_patched__"
_ORIGINAL_TOOLNODE_INIT_ATTR = "__cortexhub_original_toolnode_init__"
_PATCHED_TOOLNODE_ATTR = "__cortexhub_toolnode_patched__"
_ORIGINAL_GRAPH_INVOKE_ATTR = "__cortexhub_original_graph_invoke__"
_ORIGINAL_GRAPH_AINVOKE_ATTR = "__cortexhub_original_graph_ainvoke__"
_ORIGINAL_GRAPH_STREAM_ATTR = "__cortexhub_original_graph_stream__"
_ORIGINAL_GRAPH_ASTREAM_ATTR = "__cortexhub_original_graph_astream__"
_PATCHED_GRAPH_RUN_ATTR = "__cortexhub_graph_run_patched__"


class LangGraphAdapter(ToolAdapter):
    """Adapter for LangGraph framework.

    LangGraph uses LangChain's tool infrastructure, so we patch BaseTool.invoke().

    For approval workflows (require_approval policy effect):
    - We detect if checkpointer is configured
    - If yes: Use LangGraph's native interrupt() mechanism
    - If no: Raise clear error asking developer to add checkpointer

    Key properties:
    - Adapter is dumb plumbing
    - Calls SDK entrypoint, doesn't implement governance
    - Original stored on class, not global
    - Leverages LangGraph's native human-in-the-loop support
    """

    @property
    def framework_name(self) -> str:
        return "langgraph"

    def __init__(self, cortex_hub: Any):
        super().__init__(cortex_hub)
        self._discovered_tools: dict[str, dict[str, Any]] = {}

    def _get_framework_modules(self) -> list[str]:
        return ["langgraph", "langchain_core", "langchain_core.tools"]

    def patch(self) -> None:
        """Patch LangGraph/LangChain BaseTool.invoke method."""
        try:
            from langchain_core.tools import BaseTool

            # Check if already patched
            if getattr(BaseTool, _PATCHED_ATTR, False):
                logger.info("LangGraph already patched")
                return

            # Store original on class
            if not hasattr(BaseTool, _ORIGINAL_INVOKE_ATTR):
                setattr(BaseTool, _ORIGINAL_INVOKE_ATTR, BaseTool.invoke)

            tool_original_invoke = getattr(BaseTool, _ORIGINAL_INVOKE_ATTR)
            cortex_hub = self.cortex_hub
            adapter = self
            tools = self._discover_tools()
            if tools:
                self._register_tools(tools)

            def patched_invoke(self, input, config=None, **kwargs):
                """Governed tool invocation."""
                tool_name = getattr(self, "name", "unknown_tool")
                tool_description = getattr(self, "description", None)
                parameters_schema = adapter._extract_parameters_schema(self)

                # Extract args - preserve structure without rewriting
                if isinstance(input, dict):
                    args = input
                elif hasattr(input, "model_dump"):
                    args = input.model_dump()
                elif hasattr(input, "dict"):
                    args = input.dict()
                else:
                    args = {"_raw": input}
                policy_args = adapter._normalize_policy_args(self, args)

                tool_metadata = {
                    "name": tool_name,
                    "description": tool_description,
                    "framework": "langgraph",
                    "parameters_schema": parameters_schema,
                }
                governed_fn = govern_execution(
                    tool_fn=lambda *a, **kw: tool_original_invoke(
                        self, input, config=config, **kwargs
                    ),
                    tool_metadata=tool_metadata,
                    cortex_hub=cortex_hub,
                )
                return governed_fn(**policy_args)

            # Apply patch
            BaseTool.invoke = patched_invoke
            setattr(BaseTool, _PATCHED_ATTR, True)

            logger.info("LangGraph adapter patched successfully")

            # Patch ToolNode to discover tools (best-effort)
            self._patch_tool_node()

            # Patch LLM invoke for LLM call governance
            self._patch_llm_invoke(cortex_hub)

            # Patch graph execution for run completion events
            self._patch_run_completion(cortex_hub)

        except ImportError:
            logger.debug("LangGraph/LangChain not available, skipping adapter")
        except Exception as e:
            logger.error("Failed to patch LangGraph", error=str(e))

    def _patch_llm_invoke(self, cortex_hub) -> None:
        """Patch LangChain chat model invoke for LLM call governance."""
        try:
            from langchain_core.language_models.chat_models import BaseChatModel

            if getattr(BaseChatModel, _PATCHED_LLM_ATTR, False):
                return

            if not hasattr(BaseChatModel, _ORIGINAL_CHAT_INVOKE_ATTR):
                setattr(BaseChatModel, _ORIGINAL_CHAT_INVOKE_ATTR, BaseChatModel.invoke)
            chat_original_invoke = getattr(BaseChatModel, _ORIGINAL_CHAT_INVOKE_ATTR)

            def patched_chat_invoke(self, input, config=None, **kwargs):
                model_name = (
                    getattr(self, "model_name", None) or getattr(self, "model", None) or "unknown"
                )
                prompt = input

                def call_original(prompt_override):
                    return chat_original_invoke(self, prompt_override, config=config, **kwargs)

                llm_metadata = {
                    "kind": "llm",
                    "framework": "langgraph",
                    "model": model_name,
                    "prompt": prompt,
                    "call_original": call_original,
                }

                governed = govern_execution(
                    tool_fn=lambda *a, **kw: chat_original_invoke(
                        self, input, config=config, **kwargs
                    ),
                    tool_metadata=llm_metadata,
                    cortex_hub=cortex_hub,
                )
                return governed()

            BaseChatModel.invoke = patched_chat_invoke

            # Patch async version too
            if hasattr(BaseChatModel, "ainvoke"):
                if not hasattr(BaseChatModel, _ORIGINAL_CHAT_AINVOKE_ATTR):
                    setattr(BaseChatModel, _ORIGINAL_CHAT_AINVOKE_ATTR, BaseChatModel.ainvoke)
                chat_original_ainvoke = getattr(BaseChatModel, _ORIGINAL_CHAT_AINVOKE_ATTR)

                async def patched_chat_ainvoke(self, input, config=None, **kwargs):
                    model_name = (
                        getattr(self, "model_name", None)
                        or getattr(self, "model", None)
                        or "unknown"
                    )
                    prompt = input

                    async def call_original(prompt_override):
                        return await chat_original_ainvoke(
                            self, prompt_override, config=config, **kwargs
                        )

                    llm_metadata = {
                        "kind": "llm",
                        "framework": "langgraph",
                        "model": model_name,
                        "prompt": prompt,
                        "call_original": call_original,
                    }

                    governed = govern_execution(
                        tool_fn=lambda *a, **kw: chat_original_ainvoke(
                            self, input, config=config, **kwargs
                        ),
                        tool_metadata=llm_metadata,
                        cortex_hub=cortex_hub,
                    )
                    return await governed()

                BaseChatModel.ainvoke = patched_chat_ainvoke

            setattr(BaseChatModel, _PATCHED_LLM_ATTR, True)
            logger.info("LangGraph LLM interception patched successfully")

        except Exception as e:
            logger.debug("LangGraph LLM interception skipped", reason=str(e))

    def _patch_tool_node(self) -> None:
        """Patch LangGraph ToolNode to capture tool inventory."""
        try:
            from langgraph.prebuilt import ToolNode

            if getattr(ToolNode, _PATCHED_TOOLNODE_ATTR, False):
                return

            if not hasattr(ToolNode, _ORIGINAL_TOOLNODE_INIT_ATTR):
                setattr(ToolNode, _ORIGINAL_TOOLNODE_INIT_ATTR, ToolNode.__init__)
            original_init = getattr(ToolNode, _ORIGINAL_TOOLNODE_INIT_ATTR)
            adapter = self

            def patched_init(self, tools, *args, **kwargs):
                original_init(self, tools, *args, **kwargs)
                try:
                    adapter._register_tools(adapter._normalize_tools(tools))
                except Exception as e:
                    logger.debug("ToolNode tool discovery failed", reason=str(e))

            ToolNode.__init__ = patched_init
            setattr(ToolNode, _PATCHED_TOOLNODE_ATTR, True)
            logger.info("LangGraph ToolNode patched for tool discovery")
        except Exception as e:
            logger.debug("LangGraph ToolNode patch skipped", reason=str(e))

    def _patch_run_completion(self, cortex_hub) -> None:
        """Patch LangGraph compiled graph execution to emit run completion."""
        try:
            from langgraph.graph.state import CompiledStateGraph

            if getattr(CompiledStateGraph, _PATCHED_GRAPH_RUN_ATTR, False):
                return

            if not hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_INVOKE_ATTR):
                setattr(CompiledStateGraph, _ORIGINAL_GRAPH_INVOKE_ATTR, CompiledStateGraph.invoke)
            if not hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_AINVOKE_ATTR):
                setattr(CompiledStateGraph, _ORIGINAL_GRAPH_AINVOKE_ATTR, CompiledStateGraph.ainvoke)
            if not hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_STREAM_ATTR):
                setattr(CompiledStateGraph, _ORIGINAL_GRAPH_STREAM_ATTR, CompiledStateGraph.stream)
            if not hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_ASTREAM_ATTR):
                setattr(CompiledStateGraph, _ORIGINAL_GRAPH_ASTREAM_ATTR, CompiledStateGraph.astream)

            original_invoke = getattr(CompiledStateGraph, _ORIGINAL_GRAPH_INVOKE_ATTR)
            original_ainvoke = getattr(CompiledStateGraph, _ORIGINAL_GRAPH_AINVOKE_ATTR)
            original_stream = getattr(CompiledStateGraph, _ORIGINAL_GRAPH_STREAM_ATTR)
            original_astream = getattr(CompiledStateGraph, _ORIGINAL_GRAPH_ASTREAM_ATTR)

            def patched_invoke(self, *args, **kwargs):
                status = "completed"
                cortex_hub.start_run(framework="langgraph")
                try:
                    return original_invoke(self, *args, **kwargs)
                except Exception:
                    status = "failed"
                    raise
                finally:
                    cortex_hub.finish_run(framework="langgraph", status=status)

            async def patched_ainvoke(self, *args, **kwargs):
                status = "completed"
                cortex_hub.start_run(framework="langgraph")
                try:
                    return await original_ainvoke(self, *args, **kwargs)
                except Exception:
                    status = "failed"
                    raise
                finally:
                    cortex_hub.finish_run(framework="langgraph", status=status)

            def patched_stream(self, *args, **kwargs):
                completed = False
                failed = False
                cortex_hub.start_run(framework="langgraph")
                stream_iter = original_stream(self, *args, **kwargs)
                try:
                    for item in stream_iter:
                        yield item
                    completed = True
                except Exception:
                    failed = True
                    completed = True
                    raise
                finally:
                    if completed:
                        status = "failed" if failed else "completed"
                        cortex_hub.finish_run(framework="langgraph", status=status)

            async def patched_astream(self, *args, **kwargs):
                completed = False
                failed = False
                cortex_hub.start_run(framework="langgraph")
                stream_iter = original_astream(self, *args, **kwargs)
                try:
                    async for item in stream_iter:
                        yield item
                    completed = True
                except Exception:
                    failed = True
                    completed = True
                    raise
                finally:
                    if completed:
                        status = "failed" if failed else "completed"
                        cortex_hub.finish_run(framework="langgraph", status=status)

            CompiledStateGraph.invoke = patched_invoke
            CompiledStateGraph.ainvoke = patched_ainvoke
            CompiledStateGraph.stream = patched_stream
            CompiledStateGraph.astream = patched_astream
            setattr(CompiledStateGraph, _PATCHED_GRAPH_RUN_ATTR, True)
            logger.info("LangGraph run completion patched successfully")
        except Exception as e:
            logger.debug("LangGraph run completion patch skipped", reason=str(e))

    def unpatch(self) -> None:
        """Restore original methods."""
        try:
            from langchain_core.tools import BaseTool

            if hasattr(BaseTool, _ORIGINAL_INVOKE_ATTR):
                BaseTool.invoke = getattr(BaseTool, _ORIGINAL_INVOKE_ATTR)
                setattr(BaseTool, _PATCHED_ATTR, False)
                logger.info("LangGraph adapter unpatched")

            # Restore LLM interception
            try:
                from langchain_core.language_models.chat_models import BaseChatModel

                if hasattr(BaseChatModel, _ORIGINAL_CHAT_INVOKE_ATTR):
                    BaseChatModel.invoke = getattr(BaseChatModel, _ORIGINAL_CHAT_INVOKE_ATTR)
                if hasattr(BaseChatModel, _ORIGINAL_CHAT_AINVOKE_ATTR):
                    BaseChatModel.ainvoke = getattr(BaseChatModel, _ORIGINAL_CHAT_AINVOKE_ATTR)
                setattr(BaseChatModel, _PATCHED_LLM_ATTR, False)
            except ImportError:
                pass

            # Restore ToolNode init
            try:
                from langgraph.prebuilt import ToolNode

                if hasattr(ToolNode, _ORIGINAL_TOOLNODE_INIT_ATTR):
                    ToolNode.__init__ = getattr(ToolNode, _ORIGINAL_TOOLNODE_INIT_ATTR)
                setattr(ToolNode, _PATCHED_TOOLNODE_ATTR, False)
            except ImportError:
                pass

            # Restore graph execution methods
            try:
                from langgraph.graph.state import CompiledStateGraph

                if hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_INVOKE_ATTR):
                    CompiledStateGraph.invoke = getattr(CompiledStateGraph, _ORIGINAL_GRAPH_INVOKE_ATTR)
                if hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_AINVOKE_ATTR):
                    CompiledStateGraph.ainvoke = getattr(
                        CompiledStateGraph, _ORIGINAL_GRAPH_AINVOKE_ATTR
                    )
                if hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_STREAM_ATTR):
                    CompiledStateGraph.stream = getattr(
                        CompiledStateGraph, _ORIGINAL_GRAPH_STREAM_ATTR
                    )
                if hasattr(CompiledStateGraph, _ORIGINAL_GRAPH_ASTREAM_ATTR):
                    CompiledStateGraph.astream = getattr(
                        CompiledStateGraph, _ORIGINAL_GRAPH_ASTREAM_ATTR
                    )
                setattr(CompiledStateGraph, _PATCHED_GRAPH_RUN_ATTR, False)
            except ImportError:
                pass
        except ImportError:
            pass

    def intercept(self, tool_fn, tool_name, args, **kwargs):
        """Not used - governance happens via SDK entrypoint."""
        raise NotImplementedError("Use execute_governed_tool via patched invoke")

    def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools from LangGraph (best-effort)."""
        return list(self._discovered_tools.values())

    def _register_tools(self, tools: list[dict[str, Any]]) -> None:
        """Register tools with backend, merging by name."""
        if not tools:
            return

        for tool in tools:
            name = tool.get("name") or "unknown_tool"
            self._discovered_tools[name] = tool

    def _normalize_tools(self, tools: Any) -> list[dict[str, Any]]:
        """Convert tool objects to inventory payloads."""
        normalized: list[dict[str, Any]] = []

        if not tools:
            return normalized

        tool_list = tools if isinstance(tools, list) else [tools]

        for tool in tool_list:
            name = getattr(tool, "name", None) or getattr(tool, "__name__", None) or "unknown_tool"
            description = getattr(tool, "description", None) or getattr(tool, "__doc__", None)
            parameters_schema = self._extract_parameters_schema(tool)

            normalized.append(
                {
                    "name": name,
                    "description": description.strip() if isinstance(description, str) else None,
                    "parameters_schema": parameters_schema,
                    "source": "framework",
                }
            )

        return normalized

    def _normalize_policy_args(self, tool: Any, raw_args: dict[str, Any]) -> dict[str, Any]:
        """Best-effort normalize tool args for policy evaluation."""
        args = raw_args
        if isinstance(args, dict) and isinstance(args.get("args"), dict):
            args = args["args"]

        if isinstance(args, str):
            try:
                parsed = json.loads(args)
                if isinstance(parsed, dict):
                    args = parsed
            except json.JSONDecodeError:
                pass

        args_schema = getattr(tool, "args_schema", None)
        if args_schema and isinstance(args, dict):
            try:
                if hasattr(args_schema, "model_validate"):
                    parsed = args_schema.model_validate(args)
                elif hasattr(args_schema, "parse_obj"):
                    parsed = args_schema.parse_obj(args)
                else:
                    parsed = None
                if parsed is not None:
                    if hasattr(parsed, "model_dump"):
                        args = parsed.model_dump()
                    elif hasattr(parsed, "dict"):
                        args = parsed.dict()
            except Exception:
                pass

        return args if isinstance(args, dict) else {"_raw": args}

    def _extract_parameters_schema(self, tool: Any) -> dict[str, Any] | None:
        """Best-effort JSON schema extraction for tool parameters."""
        schema = None
        args_schema = getattr(tool, "args_schema", None)

        if args_schema is not None:
            if hasattr(args_schema, "model_json_schema"):
                schema = args_schema.model_json_schema()
            elif hasattr(args_schema, "schema"):
                schema = args_schema.schema()

        if schema is None:
            args = getattr(tool, "args", None)
            if isinstance(args, dict):
                schema = {
                    "type": "object",
                    "properties": args,
                    "required": list(args.keys()),
                }

        if not isinstance(schema, dict):
            return None

        return {
            "type": schema.get("type", "object"),
            "properties": schema.get("properties", {}) or {},
            "required": schema.get("required", []) or [],
        }
