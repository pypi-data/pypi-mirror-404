"""OpenAI Agents SDK adapter for tool interception.

Intercepts tool execution by wrapping the function_tool decorator.

Architectural rules:
- Adapter is DUMB plumbing
- Adapter calls ONE SDK entrypoint: govern_execution()
- SDK orchestrates everything
- No governance logic in adapter
"""

import json
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

import structlog

from cortexhub.adapters.base import ToolAdapter
from cortexhub.pipeline import govern_execution

if TYPE_CHECKING:
    from cortexhub.client import CortexHub

logger = structlog.get_logger(__name__)

# Attribute names for storing originals
_ORIGINAL_FUNCTION_TOOL_ATTR = "__cortexhub_original_function_tool__"
_PATCHED_ATTR = "__cortexhub_patched__"
_ORIGINAL_RUN_ATTR = "__cortexhub_original_run__"
_ORIGINAL_RUN_SYNC_ATTR = "__cortexhub_original_run_sync__"
_ORIGINAL_RUN_STREAMED_ATTR = "__cortexhub_original_run_streamed__"
_PATCHED_RUN_ATTR = "__cortexhub_run_patched__"
_ORIGINAL_RESPONSES_FETCH_ATTR = "__cortexhub_original_responses_fetch__"
_ORIGINAL_CHAT_FETCH_ATTR = "__cortexhub_original_chat_fetch__"
_PATCHED_LLM_ATTR = "__cortexhub_llm_patched__"


class OpenAIAgentsAdapter(ToolAdapter):
    """Adapter for OpenAI Agents SDK.
    
    Wraps the function_tool decorator to intercept tool creation
    and wrap the on_invoke_tool method for governance.
    
    Key properties:
    - Adapter is dumb plumbing
    - Calls SDK entrypoint, doesn't implement governance
    - Wraps decorator to intercept all tools
    - Async-safe via SDK
    """
    
    @property
    def framework_name(self) -> str:
        return "openai_agents"
    
    def _get_framework_modules(self) -> list[str]:
        return ["agents", "openai_agents"]
    
    def patch(self) -> None:
        """Patch OpenAI Agents by wrapping the function_tool decorator."""
        try:
            import agents
            import agents.tool as tool_module
            
            # Check if already patched
            if getattr(tool_module, _PATCHED_ATTR, False):
                logger.info("OpenAI Agents already patched")
                return

            cortex_hub = self.cortex_hub
            
            # Store original function_tool decorator
            if not hasattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR):
                setattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR, tool_module.function_tool)
            
            original_function_tool = getattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR)

            def patched_function_tool(
                func: Callable | None = None,
                *,
                name_override: str | None = None,
                description_override: str | None = None,
                use_docstring_info: bool = True,
                failure_error_function: Callable | None = None,
                strict_mode: bool = True,
                is_enabled: bool | Callable = True,
            ):
                """Wrapped function_tool that adds CortexHub governance."""
                
                def decorator(fn: Callable) -> Any:
                    # Create the original FunctionTool
                    tool = original_function_tool(
                        fn,
                        name_override=name_override,
                        description_override=description_override,
                        use_docstring_info=use_docstring_info,
                        failure_error_function=failure_error_function,
                        strict_mode=strict_mode,
                        is_enabled=is_enabled,
                    )
                    
                    # Wrap on_invoke_tool with governance
                    original_invoke = tool.on_invoke_tool
                    tool_name = tool.name
                    tool_description = tool.description
                    parameters_schema = tool.params_json_schema or tool.strict_json_schema
                    
                    async def governed_invoke(ctx, input_json: str) -> Any:
                        """Governed tool invocation."""
                        try:
                            args = json.loads(input_json) if input_json else {}
                        except json.JSONDecodeError:
                            args = {"_raw": input_json}
                        
                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "openai_agents",
                            "parameters_schema": parameters_schema,
                        }
                        
                        # Create governed function
                        governed_fn = govern_execution(
                            tool_fn=lambda **kw: original_invoke(ctx, input_json),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )
                        
                        # Execute with governance
                        result = governed_fn(**args)
                        # Handle async
                        if hasattr(result, '__await__'):
                            result = await result
                        return result
                    
                    # Replace on_invoke_tool with governed version
                    # FunctionTool is a dataclass, so we need to create a new instance
                    from dataclasses import fields
                    from agents.tool import FunctionTool

                    field_names = {field.name for field in fields(FunctionTool)}
                    tool_kwargs = {
                        "name": tool.name,
                        "description": tool.description,
                        "params_json_schema": tool.params_json_schema,
                        "on_invoke_tool": governed_invoke,
                        "strict_json_schema": tool.strict_json_schema,
                        "is_enabled": tool.is_enabled,
                    }
                    if "tool_input_guardrails" in field_names:
                        tool_kwargs["tool_input_guardrails"] = getattr(
                            tool, "tool_input_guardrails", None
                        )
                    if "tool_output_guardrails" in field_names:
                        tool_kwargs["tool_output_guardrails"] = getattr(
                            tool, "tool_output_guardrails", None
                        )

                    governed_tool = FunctionTool(**tool_kwargs)
                    
                    return governed_tool
                
                # Handle @function_tool vs @function_tool()
                if func is not None:
                    return decorator(func)
                return decorator

            # Apply patch
            tool_module.function_tool = patched_function_tool
            agents.function_tool = patched_function_tool
            setattr(tool_module, _PATCHED_ATTR, True)

            logger.info("OpenAI Agents adapter patched successfully")

            self._patch_run_completion(cortex_hub)
            self._patch_llm_calls(cortex_hub)
            
        except ImportError:
            logger.debug("OpenAI Agents SDK not installed, skipping")
        except Exception as e:
            logger.error("Failed to patch OpenAI Agents", error=str(e))
    
    def unpatch(self) -> None:
        """Restore original function_tool decorator."""
        try:
            import agents
            import agents.tool as tool_module
            
            if not hasattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR):
                logger.debug("OpenAI Agents not patched, nothing to restore")
                return
            
            original = getattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR)
            tool_module.function_tool = original
            agents.function_tool = original
            setattr(tool_module, _PATCHED_ATTR, False)
            
            logger.info("OpenAI Agents adapter unpatched")

            try:
                from agents.run import Runner

                if hasattr(Runner, _ORIGINAL_RUN_ATTR):
                    Runner.run = getattr(Runner, _ORIGINAL_RUN_ATTR)
                if hasattr(Runner, _ORIGINAL_RUN_SYNC_ATTR):
                    Runner.run_sync = getattr(Runner, _ORIGINAL_RUN_SYNC_ATTR)
                if hasattr(Runner, _ORIGINAL_RUN_STREAMED_ATTR):
                    Runner.run_streamed = getattr(Runner, _ORIGINAL_RUN_STREAMED_ATTR)
                setattr(Runner, _PATCHED_RUN_ATTR, False)
            except ImportError:
                pass
            try:
                from agents.models.openai_responses import OpenAIResponsesModel
                from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

                if hasattr(OpenAIResponsesModel, _ORIGINAL_RESPONSES_FETCH_ATTR):
                    OpenAIResponsesModel._fetch_response = getattr(
                        OpenAIResponsesModel, _ORIGINAL_RESPONSES_FETCH_ATTR
                    )
                if hasattr(OpenAIChatCompletionsModel, _ORIGINAL_CHAT_FETCH_ATTR):
                    OpenAIChatCompletionsModel._fetch_response = getattr(
                        OpenAIChatCompletionsModel, _ORIGINAL_CHAT_FETCH_ATTR
                    )
                setattr(OpenAIResponsesModel, _PATCHED_LLM_ATTR, False)
                setattr(OpenAIChatCompletionsModel, _PATCHED_LLM_ATTR, False)
            except ImportError:
                pass
        except ImportError:
            pass
    
    def intercept(self, tool_fn, tool_name, args, **kwargs):
        """Not used - governance happens via wrapped decorator."""
        raise NotImplementedError("Use govern_execution via wrapped decorator")

    def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools from OpenAI Agents SDK (best-effort)."""
        return []

    def _patch_run_completion(self, cortex_hub) -> None:
        """Patch Runner run methods to emit run completion."""
        try:
            from agents.run import Runner

            if getattr(Runner, _PATCHED_RUN_ATTR, False):
                return

            if not hasattr(Runner, _ORIGINAL_RUN_ATTR):
                setattr(Runner, _ORIGINAL_RUN_ATTR, Runner.__dict__.get("run", Runner.run))
            if not hasattr(Runner, _ORIGINAL_RUN_SYNC_ATTR):
                setattr(Runner, _ORIGINAL_RUN_SYNC_ATTR, Runner.__dict__.get("run_sync", Runner.run_sync))
            if not hasattr(Runner, _ORIGINAL_RUN_STREAMED_ATTR):
                setattr(
                    Runner,
                    _ORIGINAL_RUN_STREAMED_ATTR,
                    Runner.__dict__.get("run_streamed", Runner.run_streamed),
                )

            original_run_descriptor = getattr(Runner, _ORIGINAL_RUN_ATTR)
            original_run_sync_descriptor = getattr(Runner, _ORIGINAL_RUN_SYNC_ATTR)
            original_run_streamed_descriptor = getattr(Runner, _ORIGINAL_RUN_STREAMED_ATTR)
            original_run = (
                original_run_descriptor.__get__(None, Runner)
                if hasattr(original_run_descriptor, "__get__")
                else original_run_descriptor
            )
            original_run_sync = (
                original_run_sync_descriptor.__get__(None, Runner)
                if hasattr(original_run_sync_descriptor, "__get__")
                else original_run_sync_descriptor
            )
            original_run_streamed = (
                original_run_streamed_descriptor.__get__(None, Runner)
                if hasattr(original_run_streamed_descriptor, "__get__")
                else original_run_streamed_descriptor
            )

            @classmethod
            async def patched_run(cls, *args, **kwargs):
                status = "completed"
                cortex_hub.start_run(framework="openai_agents")
                try:
                    return await original_run(*args, **kwargs)
                except Exception:
                    status = "failed"
                    raise
                finally:
                    cortex_hub.finish_run(framework="openai_agents", status=status)

            @classmethod
            def patched_run_sync(cls, *args, **kwargs):
                status = "completed"
                cortex_hub.start_run(framework="openai_agents")
                try:
                    return original_run_sync(*args, **kwargs)
                except Exception:
                    status = "failed"
                    raise
                finally:
                    cortex_hub.finish_run(framework="openai_agents", status=status)

            @classmethod
            def patched_run_streamed(cls, *args, **kwargs):
                cortex_hub.start_run(framework="openai_agents")
                try:
                    result = original_run_streamed(*args, **kwargs)
                except Exception:
                    cortex_hub.finish_run(framework="openai_agents", status="failed")
                    raise

                original_stream_events = getattr(result, "stream_events", None)
                if not callable(original_stream_events):
                    return result

                async def wrapped_stream_events(*stream_args, **stream_kwargs):
                    completed = False
                    failed = False
                    try:
                        async for event in original_stream_events(*stream_args, **stream_kwargs):
                            yield event
                        completed = True
                    except Exception:
                        failed = True
                        completed = True
                        raise
                    finally:
                        if completed:
                            status = "failed" if failed else "completed"
                            cortex_hub.finish_run(framework="openai_agents", status=status)

                result.stream_events = wrapped_stream_events
                return result

            Runner.run = patched_run
            Runner.run_sync = patched_run_sync
            Runner.run_streamed = patched_run_streamed
            setattr(Runner, _PATCHED_RUN_ATTR, True)
            logger.info("OpenAI Agents run completion patched successfully")
        except ImportError:
            logger.debug("OpenAI Agents run completion patch skipped")

    def _patch_llm_calls(self, cortex_hub: "CortexHub") -> None:
        """Patch OpenAI Agents models to emit llm.call spans."""
        try:
            from agents.models.openai_responses import OpenAIResponsesModel
            from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

            if getattr(OpenAIResponsesModel, _PATCHED_LLM_ATTR, False):
                return

            if not hasattr(OpenAIResponsesModel, _ORIGINAL_RESPONSES_FETCH_ATTR):
                setattr(
                    OpenAIResponsesModel,
                    _ORIGINAL_RESPONSES_FETCH_ATTR,
                    OpenAIResponsesModel._fetch_response,
                )
            if not hasattr(OpenAIChatCompletionsModel, _ORIGINAL_CHAT_FETCH_ATTR):
                setattr(
                    OpenAIChatCompletionsModel,
                    _ORIGINAL_CHAT_FETCH_ATTR,
                    OpenAIChatCompletionsModel._fetch_response,
                )

            original_responses_fetch = getattr(
                OpenAIResponsesModel, _ORIGINAL_RESPONSES_FETCH_ATTR
            )
            original_chat_fetch = getattr(
                OpenAIChatCompletionsModel, _ORIGINAL_CHAT_FETCH_ATTR
            )

            def _with_system_prompt(system_instructions, input_payload):
                if not system_instructions:
                    return input_payload
                if isinstance(input_payload, list):
                    return [{"role": "system", "content": system_instructions}] + input_payload
                return [{"role": "system", "content": system_instructions}, input_payload]

            def _split_prompt_override(prompt_override, system_instructions, input_payload):
                if prompt_override is None:
                    return system_instructions, input_payload
                if isinstance(prompt_override, list) and prompt_override:
                    first = prompt_override[0]
                    if (
                        isinstance(first, dict)
                        and first.get("role") == "system"
                        and isinstance(first.get("content"), str)
                    ):
                        return first["content"], prompt_override[1:]
                    return system_instructions, prompt_override
                return system_instructions, prompt_override

            async def patched_responses_fetch(
                self,
                system_instructions,
                input,
                model_settings,
                tools,
                output_schema,
                handoffs,
                previous_response_id,
                stream=False,
            ):
                prompt = _with_system_prompt(system_instructions, input)
                model_name = str(getattr(self, "model", "unknown"))

                async def call_original(prompt_override):
                    new_system, new_input = _split_prompt_override(
                        prompt_override,
                        system_instructions,
                        input,
                    )
                    return await original_responses_fetch(
                        self,
                        new_system,
                        new_input,
                        model_settings,
                        tools,
                        output_schema,
                        handoffs,
                        previous_response_id,
                        stream=stream,
                    )

                llm_metadata = {
                    "kind": "llm",
                    "framework": "openai_agents",
                    "model": model_name,
                    "prompt": prompt,
                    "call_original": call_original,
                }
                governed = govern_execution(
                    tool_fn=lambda *a, **kw: original_responses_fetch(
                        self,
                        system_instructions,
                        input,
                        model_settings,
                        tools,
                        output_schema,
                        handoffs,
                        previous_response_id,
                        stream=stream,
                    ),
                    tool_metadata=llm_metadata,
                    cortex_hub=cortex_hub,
                )
                return await governed()

            async def patched_chat_fetch(
                self,
                system_instructions,
                input,
                model_settings,
                tools,
                output_schema,
                handoffs,
                span,
                tracing,
                stream=False,
            ):
                prompt = _with_system_prompt(system_instructions, input)
                model_name = str(getattr(self, "model", "unknown"))

                async def call_original(prompt_override):
                    new_system, new_input = _split_prompt_override(
                        prompt_override,
                        system_instructions,
                        input,
                    )
                    return await original_chat_fetch(
                        self,
                        new_system,
                        new_input,
                        model_settings,
                        tools,
                        output_schema,
                        handoffs,
                        span,
                        tracing,
                        stream=stream,
                    )

                llm_metadata = {
                    "kind": "llm",
                    "framework": "openai_agents",
                    "model": model_name,
                    "prompt": prompt,
                    "call_original": call_original,
                }
                governed = govern_execution(
                    tool_fn=lambda *a, **kw: original_chat_fetch(
                        self,
                        system_instructions,
                        input,
                        model_settings,
                        tools,
                        output_schema,
                        handoffs,
                        span,
                        tracing,
                        stream=stream,
                    ),
                    tool_metadata=llm_metadata,
                    cortex_hub=cortex_hub,
                )
                return await governed()

            OpenAIResponsesModel._fetch_response = patched_responses_fetch
            OpenAIChatCompletionsModel._fetch_response = patched_chat_fetch
            setattr(OpenAIResponsesModel, _PATCHED_LLM_ATTR, True)
            setattr(OpenAIChatCompletionsModel, _PATCHED_LLM_ATTR, True)
            logger.info("OpenAI Agents LLM interception patched successfully")
        except Exception as e:
            logger.debug("OpenAI Agents LLM interception skipped", reason=str(e))
