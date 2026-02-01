"""Unified governance pipeline for adapters that can't use SDK entrypoint directly.

This is a thin wrapper around cortex_hub.execute_governed_tool() for adapters
that need to create governed wrappers (e.g., CrewAI, LlamaIndex).

Architectural rules:
- This is a convenience wrapper, not a separate pipeline
- All governance logic lives in CortexHub client
- Adapters should prefer calling SDK entrypoint directly when possible
"""

import asyncio
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


def is_async_callable(fn: Callable) -> bool:
    """Check if a callable is async."""
    return asyncio.iscoroutinefunction(fn)


def govern_execution(
    tool_fn: Callable,
    tool_metadata: dict[str, Any],
    cortex_hub: Any,  # Type: CortexHub
) -> Callable:
    """Create governed wrapper for sync or async execution.

    This wraps the SDK's execute_governed_tool() for adapters that need
    to create function wrappers.

    Args:
        tool_fn: The actual function to execute
        tool_metadata: Tool information (name, framework, description)
        cortex_hub: CortexHub instance

    Returns:
        Wrapped function (sync or async based on tool_fn)
    """
    execution_kind = tool_metadata.get("kind", "tool")
    tool_name = tool_metadata.get("name", "unknown")
    tool_description = tool_metadata.get("description")
    framework = tool_metadata.get("framework", "unknown")
    model = tool_metadata.get("model", "unknown")
    prompt = tool_metadata.get("prompt")
    call_original = tool_metadata.get("call_original")
    if call_original is None:
        call_original = tool_fn
    
    if execution_kind == "llm":
        if is_async_callable(call_original):
            async def async_wrapper(*args, **kwargs):
                return await cortex_hub.execute_governed_llm_call_async(
                    model=model,
                    prompt=prompt,
                    framework=framework,
                    call_original=call_original,
                )
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                return cortex_hub.execute_governed_llm_call(
                    model=model,
                    prompt=prompt,
                    framework=framework,
                    call_original=call_original,
                )
            return sync_wrapper

    if is_async_callable(tool_fn):
        async def async_wrapper(*args, **kwargs):
            return await cortex_hub.execute_governed_tool_async(
                tool_name=tool_name,
                tool_description=tool_description,
                args=kwargs,  # Use kwargs for structured arguments
                framework=framework,
                call_original=lambda: tool_fn(*args, **kwargs),
            )
        return async_wrapper
    else:
        def sync_wrapper(*args, **kwargs):
            return cortex_hub.execute_governed_tool(
                tool_name=tool_name,
                tool_description=tool_description,
                args=kwargs,  # Use kwargs for structured arguments
                framework=framework,
                call_original=lambda: tool_fn(*args, **kwargs),
            )
        return sync_wrapper
