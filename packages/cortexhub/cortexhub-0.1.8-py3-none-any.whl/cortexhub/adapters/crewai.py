"""CrewAI adapter for tool and LLM interception.

Patches CrewAI at multiple levels:
- CrewStructuredTool.invoke for all LLM-driven tool calls
- BaseTool._run for direct tool usage
- LiteLLM completion for LLM call governance (guardrails, PII detection)

IMPORTANT: CrewAI has its own OpenTelemetry setup that may conflict with
CortexHub's telemetry. To ensure proper telemetry capture, either:
1. Call cortexhub.init() BEFORE importing crewai
2. Set environment variable: CREWAI_TRACING_ENABLED=false

Architectural rules:
- Adapter is DUMB plumbing
- SDK orchestrates everything via govern_execution()
- Store original on class, not global
"""

from typing import Any

import structlog

from cortexhub.adapters.base import ToolAdapter
from cortexhub.pipeline import govern_execution

logger = structlog.get_logger(__name__)

# Attribute names for storing originals on class
_ORIGINAL_INVOKE_ATTR = "__cortexhub_original_invoke__"
_ORIGINAL_RUN_ATTR = "__cortexhub_original_run__"
_ORIGINAL_RUN_METHOD_ATTR = "__cortexhub_original_run_method__"
_PATCHED_ATTR = "__cortexhub_patched__"
_PATCHED_TOOL_ATTR = "__cortexhub_tool_patched__"
_PATCHED_RUN_METHOD_ATTR = "__cortexhub_run_method_patched__"
_ORIGINAL_TOOL_RUN_ATTR = "__cortexhub_original_tool_run__"
_PATCHED_TOOL_RUN_ATTR = "__cortexhub_tool_run_patched__"
_PATCHED_LLM_ATTR = "__cortexhub_llm_patched__"
_ORIGINAL_COMPLETION_ATTR = "__cortexhub_original_completion__"
_ORIGINAL_ACOMPLETION_ATTR = "__cortexhub_original_acompletion__"
_ORIGINAL_KICKOFF_ATTR = "__cortexhub_original_kickoff__"
_ORIGINAL_KICKOFF_ASYNC_ATTR = "__cortexhub_original_kickoff_async__"
_PATCHED_RUN_ATTR = "__cortexhub_run_patched__"
_ORIGINAL_LLM_CALL_ATTR = "__cortexhub_original_llm_call__"
_ORIGINAL_LLM_ACALL_ATTR = "__cortexhub_original_llm_acall__"
_PATCHED_LLM_CALL_ATTR = "__cortexhub_llm_call_patched__"


class CrewAIAdapter(ToolAdapter):
    """Adapter for CrewAI framework.

    Patches CrewStructuredTool.invoke - the method called by CrewAI's
    agent executor when tools are invoked by the LLM.
    
    Key properties:
    - Adapter is dumb plumbing
    - Patches at class level so all tools are governed
    - Works regardless of when tools are created
    """

    @property
    def framework_name(self) -> str:
        return "crewai"

    def _get_framework_modules(self) -> list[str]:
        return ["crewai", "crewai.tools"]

    def patch(self) -> None:
        """Patch CrewAI tool execution methods."""
        try:
            from crewai.tools.structured_tool import CrewStructuredTool
            
            cortex_hub = self.cortex_hub

            # Patch CrewStructuredTool.invoke (primary execution path)
            if not getattr(CrewStructuredTool, _PATCHED_ATTR, False):
                if not hasattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR):
                    setattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR, CrewStructuredTool.invoke)
                
                original_invoke = getattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR)

                def patched_invoke(self, input, config=None, **kwargs):
                    """Governed CrewStructuredTool execution."""
                    tool_name = getattr(self, 'name', 'unknown_tool')
                    tool_description = getattr(self, 'description', None)
                    
                    tool_metadata = {
                        "name": tool_name,
                        "description": tool_description,
                        "framework": "crewai",
                    }

                    governed_fn = govern_execution(
                        tool_fn=lambda **_kw: original_invoke(self, input, config, **kwargs),
                        tool_metadata=tool_metadata,
                        cortex_hub=cortex_hub,
                    )

                    # Extract args from input
                    if isinstance(input, dict):
                        return governed_fn(**input)
                    elif isinstance(input, str):
                        return governed_fn(_raw=input)
                    return governed_fn()

                CrewStructuredTool.invoke = patched_invoke
                setattr(CrewStructuredTool, _PATCHED_ATTR, True)
                logger.info("CrewAI CrewStructuredTool.invoke patched")

            # Also patch BaseTool._run for direct tool.run() calls
            try:
                from crewai.tools.base_tool import BaseTool, Tool
                
                if not getattr(BaseTool, _PATCHED_TOOL_ATTR, False):
                    if not hasattr(BaseTool, _ORIGINAL_RUN_ATTR):
                        setattr(BaseTool, _ORIGINAL_RUN_ATTR, BaseTool._run)
                    
                    original_run = getattr(BaseTool, _ORIGINAL_RUN_ATTR)

                    def patched_run(self, *args, **kwargs):
                        """Governed BaseTool execution."""
                        tool_name = getattr(self, 'name', 'unknown_tool')
                        tool_description = getattr(self, 'description', None)
                        
                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "crewai",
                        }

                        governed_fn = govern_execution(
                            tool_fn=lambda **_kw: original_run(self, *args, **kwargs),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )

                        # Extract args
                        if kwargs:
                            return governed_fn(**kwargs)
                        if len(args) == 1 and isinstance(args[0], dict):
                            return governed_fn(**args[0])
                        if args:
                            return governed_fn(_raw=args[0])
                        return governed_fn()

                    BaseTool._run = patched_run
                    setattr(BaseTool, _PATCHED_TOOL_ATTR, True)
                    logger.info("CrewAI BaseTool._run patched")

                if not getattr(BaseTool, _PATCHED_RUN_METHOD_ATTR, False):
                    if not hasattr(BaseTool, _ORIGINAL_RUN_METHOD_ATTR):
                        setattr(BaseTool, _ORIGINAL_RUN_METHOD_ATTR, BaseTool.run)

                    original_run_method = getattr(BaseTool, _ORIGINAL_RUN_METHOD_ATTR)

                    def patched_run_method(self, *args, **kwargs):
                        """Governed BaseTool.run execution."""
                        tool_name = getattr(self, "name", "unknown_tool")
                        tool_description = getattr(self, "description", None)

                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "crewai",
                        }

                        governed_fn = govern_execution(
                            tool_fn=lambda **_kw: original_run_method(self, *args, **kwargs),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )

                        if kwargs:
                            return governed_fn(**kwargs)
                        if len(args) == 1 and isinstance(args[0], dict):
                            return governed_fn(**args[0])
                        if args:
                            return governed_fn(_raw=args[0])
                        return governed_fn()

                    BaseTool.run = patched_run_method
                    setattr(BaseTool, _PATCHED_RUN_METHOD_ATTR, True)
                    logger.info("CrewAI BaseTool.run patched")

                if not getattr(Tool, _PATCHED_TOOL_RUN_ATTR, False):
                    if not hasattr(Tool, _ORIGINAL_TOOL_RUN_ATTR):
                        setattr(Tool, _ORIGINAL_TOOL_RUN_ATTR, Tool.run)

                    original_tool_run = getattr(Tool, _ORIGINAL_TOOL_RUN_ATTR)

                    def patched_tool_run(self, *args, **kwargs):
                        """Governed Tool.run execution (bypasses BaseTool.run)."""
                        tool_name = getattr(self, "name", "unknown_tool")
                        tool_description = getattr(self, "description", None)

                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "crewai",
                        }

                        governed_fn = govern_execution(
                            tool_fn=lambda **_kw: original_tool_run(self, *args, **kwargs),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )

                        if kwargs:
                            return governed_fn(**kwargs)
                        if len(args) == 1 and isinstance(args[0], dict):
                            return governed_fn(**args[0])
                        if args:
                            return governed_fn(_raw=args[0])
                        return governed_fn()

                    Tool.run = patched_tool_run
                    setattr(Tool, _PATCHED_TOOL_RUN_ATTR, True)
                    logger.info("CrewAI Tool.run patched")
                    
            except ImportError:
                logger.debug("CrewAI BaseTool not available")

            logger.info("CrewAI adapter patched successfully")
            
            # Patch LiteLLM for LLM call governance (guardrails, PII)
            self._patch_litellm(cortex_hub)
            self._patch_llm_call(cortex_hub)
            self._patch_run_completion(cortex_hub)

        except ImportError:
            logger.debug("CrewAI not available, skipping adapter")
            raise
        except Exception as e:
            logger.error("Failed to patch CrewAI", error=str(e))
            raise

    def _patch_litellm(self, cortex_hub) -> None:
        """Patch LiteLLM completion for LLM call governance.
        
        CrewAI uses LiteLLM internally for all LLM calls.
        We patch litellm.completion to intercept and run guardrails.
        """
        try:
            import litellm
            
            if getattr(litellm, _PATCHED_LLM_ATTR, False):
                logger.debug("LiteLLM already patched for CrewAI")
                return
            
            # Store originals
            if not hasattr(litellm, _ORIGINAL_COMPLETION_ATTR):
                setattr(litellm, _ORIGINAL_COMPLETION_ATTR, litellm.completion)
            original_completion = getattr(litellm, _ORIGINAL_COMPLETION_ATTR)
            
            def patched_completion(*args, **kwargs):
                """Governed LiteLLM completion."""
                model = kwargs.get("model") or (args[0] if args else "unknown")
                messages = kwargs.get("messages") or (args[1] if len(args) > 1 else [])
                
                # Extract prompt from messages
                prompt = messages
                
                def call_original(prompt_override):
                    # Replace messages if overridden (for redaction)
                    call_kwargs = kwargs.copy()
                    if prompt_override is not None:
                        call_kwargs["messages"] = prompt_override
                    return original_completion(*args[:1] if args else [], **call_kwargs)
                
                llm_metadata = {
                    "kind": "llm",
                    "framework": "crewai",
                    "model": model,
                    "prompt": prompt,
                    "call_original": call_original,
                }
                
                governed = govern_execution(
                    tool_fn=lambda *a, **kw: original_completion(*args, **kwargs),
                    tool_metadata=llm_metadata,
                    cortex_hub=cortex_hub,
                )
                return governed()
            
            litellm.completion = patched_completion
            
            # Patch async version too
            if hasattr(litellm, "acompletion"):
                if not hasattr(litellm, _ORIGINAL_ACOMPLETION_ATTR):
                    setattr(litellm, _ORIGINAL_ACOMPLETION_ATTR, litellm.acompletion)
                original_acompletion = getattr(litellm, _ORIGINAL_ACOMPLETION_ATTR)
                
                async def patched_acompletion(*args, **kwargs):
                    """Governed async LiteLLM completion."""
                    model = kwargs.get("model") or (args[0] if args else "unknown")
                    messages = kwargs.get("messages") or (args[1] if len(args) > 1 else [])
                    prompt = messages
                    
                    async def call_original(prompt_override):
                        call_kwargs = kwargs.copy()
                        if prompt_override is not None:
                            call_kwargs["messages"] = prompt_override
                        return await original_acompletion(*args[:1] if args else [], **call_kwargs)
                    
                    llm_metadata = {
                        "kind": "llm",
                        "framework": "crewai",
                        "model": model,
                        "prompt": prompt,
                        "call_original": call_original,
                    }
                    
                    governed = govern_execution(
                        tool_fn=lambda *a, **kw: original_acompletion(*args, **kwargs),
                        tool_metadata=llm_metadata,
                        cortex_hub=cortex_hub,
                    )
                    return await governed()
                
                litellm.acompletion = patched_acompletion
            
            setattr(litellm, _PATCHED_LLM_ATTR, True)
            logger.info("CrewAI LiteLLM interception patched successfully")
            
        except ImportError:
            logger.debug("LiteLLM not available, skipping LLM interception for CrewAI")
        except Exception as e:
            logger.debug("CrewAI LiteLLM interception skipped", reason=str(e))

    def _patch_llm_call(self, cortex_hub) -> None:
        """Patch CrewAI LLM provider call methods for llm.call spans."""
        try:
            from crewai.llms.base_llm import BaseLLM
            provider_modules = [
                "crewai.llms.providers.openai.completion",
                "crewai.llms.providers.anthropic.completion",
                "crewai.llms.providers.azure.completion",
                "crewai.llms.providers.gemini.completion",
                "crewai.llms.providers.bedrock.completion",
            ]
            for module_path in provider_modules:
                try:
                    __import__(module_path)
                except Exception:
                    continue

            def _all_subclasses(base):
                seen = set()
                stack = list(base.__subclasses__())
                while stack:
                    cls = stack.pop()
                    if cls in seen:
                        continue
                    seen.add(cls)
                    stack.extend(cls.__subclasses__())
                    yield cls

            patched_any = False
            for llm_cls in _all_subclasses(BaseLLM):
                if getattr(llm_cls, _PATCHED_LLM_CALL_ATTR, False):
                    continue

                if hasattr(llm_cls, "call"):
                    if not hasattr(llm_cls, _ORIGINAL_LLM_CALL_ATTR):
                        setattr(llm_cls, _ORIGINAL_LLM_CALL_ATTR, llm_cls.call)
                    original_call = getattr(llm_cls, _ORIGINAL_LLM_CALL_ATTR)

                    def _make_patched_call(call_impl):
                        def patched_call(self, messages, *args, **kwargs):
                            if getattr(self, "is_litellm", False):
                                return call_impl(self, messages, *args, **kwargs)

                            model = getattr(self, "model", "unknown")
                            prompt = messages

                            def call_original(prompt_override):
                                new_messages = (
                                    prompt_override if prompt_override is not None else messages
                                )
                                return call_impl(self, new_messages, *args, **kwargs)

                            llm_metadata = {
                                "kind": "llm",
                                "framework": "crewai",
                                "model": model,
                                "prompt": prompt,
                                "call_original": call_original,
                            }

                            governed = govern_execution(
                                tool_fn=lambda *a, **kw: call_impl(
                                    self, messages, *args, **kwargs
                                ),
                                tool_metadata=llm_metadata,
                                cortex_hub=cortex_hub,
                            )
                            return governed()

                        return patched_call

                    llm_cls.call = _make_patched_call(original_call)
                    patched_any = True

                if hasattr(llm_cls, "acall"):
                    if not hasattr(llm_cls, _ORIGINAL_LLM_ACALL_ATTR):
                        setattr(llm_cls, _ORIGINAL_LLM_ACALL_ATTR, llm_cls.acall)
                    original_acall = getattr(llm_cls, _ORIGINAL_LLM_ACALL_ATTR)

                    def _make_patched_acall(call_impl):
                        async def patched_acall(self, messages, *args, **kwargs):
                            if getattr(self, "is_litellm", False):
                                return await call_impl(self, messages, *args, **kwargs)

                            model = getattr(self, "model", "unknown")
                            prompt = messages

                            async def call_original(prompt_override):
                                new_messages = (
                                    prompt_override if prompt_override is not None else messages
                                )
                                return await call_impl(self, new_messages, *args, **kwargs)

                            llm_metadata = {
                                "kind": "llm",
                                "framework": "crewai",
                                "model": model,
                                "prompt": prompt,
                                "call_original": call_original,
                            }

                            governed = govern_execution(
                                tool_fn=lambda *a, **kw: call_impl(
                                    self, messages, *args, **kwargs
                                ),
                                tool_metadata=llm_metadata,
                                cortex_hub=cortex_hub,
                            )
                            return await governed()

                        return patched_acall

                    llm_cls.acall = _make_patched_acall(original_acall)
                    patched_any = True

                setattr(llm_cls, _PATCHED_LLM_CALL_ATTR, True)

            if patched_any:
                logger.info("CrewAI LLM provider calls patched successfully")
        except ImportError:
            logger.debug("CrewAI LLM base not available, skipping LLM call patch")
        except Exception as e:
            logger.debug("CrewAI LLM call patch skipped", reason=str(e))

    def _patch_run_completion(self, cortex_hub) -> None:
        """Patch CrewAI crew kickoff methods to emit run completion."""
        try:
            import crewai
            Crew = getattr(crewai, "Crew", None)
            if Crew is None:
                from crewai.crew import Crew

            if getattr(Crew, _PATCHED_RUN_ATTR, False):
                return

            if not hasattr(Crew, _ORIGINAL_KICKOFF_ATTR):
                setattr(Crew, _ORIGINAL_KICKOFF_ATTR, Crew.kickoff)
            original_kickoff = getattr(Crew, _ORIGINAL_KICKOFF_ATTR)

            def patched_kickoff(self, *args, **kwargs):
                status = "completed"
                cortex_hub.start_run(framework="crewai")
                try:
                    return original_kickoff(self, *args, **kwargs)
                except Exception:
                    status = "failed"
                    raise
                finally:
                    cortex_hub.finish_run(framework="crewai", status=status)

            Crew.kickoff = patched_kickoff

            if hasattr(Crew, "kickoff_async"):
                if not hasattr(Crew, _ORIGINAL_KICKOFF_ASYNC_ATTR):
                    setattr(Crew, _ORIGINAL_KICKOFF_ASYNC_ATTR, Crew.kickoff_async)
                original_kickoff_async = getattr(Crew, _ORIGINAL_KICKOFF_ASYNC_ATTR)

                async def patched_kickoff_async(self, *args, **kwargs):
                    status = "completed"
                    cortex_hub.start_run(framework="crewai")
                    try:
                        return await original_kickoff_async(self, *args, **kwargs)
                    except Exception:
                        status = "failed"
                        raise
                    finally:
                        cortex_hub.finish_run(framework="crewai", status=status)

                Crew.kickoff_async = patched_kickoff_async

            setattr(Crew, _PATCHED_RUN_ATTR, True)
            logger.info("CrewAI run completion patched successfully")
        except ImportError:
            logger.debug("CrewAI run completion patch skipped")
        except Exception as e:
            logger.debug("CrewAI run completion patch failed", reason=str(e))

    def unpatch(self) -> None:
        """Restore original CrewAI methods."""
        try:
            from crewai.tools.structured_tool import CrewStructuredTool
            
            if hasattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR):
                original = getattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR)
                CrewStructuredTool.invoke = original
                setattr(CrewStructuredTool, _PATCHED_ATTR, False)
            
            logger.info("CrewAI CrewStructuredTool unpatched")
            
            try:
                from crewai.tools.base_tool import BaseTool
                if hasattr(BaseTool, _ORIGINAL_RUN_ATTR):
                    original = getattr(BaseTool, _ORIGINAL_RUN_ATTR)
                    BaseTool._run = original
                    setattr(BaseTool, _PATCHED_TOOL_ATTR, False)
                logger.info("CrewAI BaseTool unpatched")
            except ImportError:
                pass
            
            # Restore LiteLLM
            try:
                import litellm
                if hasattr(litellm, _ORIGINAL_COMPLETION_ATTR):
                    litellm.completion = getattr(litellm, _ORIGINAL_COMPLETION_ATTR)
                if hasattr(litellm, _ORIGINAL_ACOMPLETION_ATTR):
                    litellm.acompletion = getattr(litellm, _ORIGINAL_ACOMPLETION_ATTR)
                setattr(litellm, _PATCHED_LLM_ATTR, False)
                logger.info("CrewAI LiteLLM unpatched")
            except ImportError:
                pass

            # Restore run completion patches
            try:
                import crewai
                Crew = getattr(crewai, "Crew", None)
                if Crew is None:
                    from crewai.crew import Crew

                if hasattr(Crew, _ORIGINAL_KICKOFF_ATTR):
                    Crew.kickoff = getattr(Crew, _ORIGINAL_KICKOFF_ATTR)
                if hasattr(Crew, _ORIGINAL_KICKOFF_ASYNC_ATTR):
                    Crew.kickoff_async = getattr(Crew, _ORIGINAL_KICKOFF_ASYNC_ATTR)
                setattr(Crew, _PATCHED_RUN_ATTR, False)
            except ImportError:
                pass
                
        except ImportError:
            pass

    def intercept(self, tool_fn, tool_name, args, **kwargs):
        """Not used - governance happens via SDK entrypoint."""
        raise NotImplementedError("Use govern_execution via pipeline")

    def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools from CrewAI (best-effort)."""
        return []
