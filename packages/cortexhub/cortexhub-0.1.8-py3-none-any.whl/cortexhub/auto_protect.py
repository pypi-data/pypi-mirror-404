"""Framework auto-detection and automatic protection.

Detects imported frameworks and applies appropriate adapters automatically.
"""

import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from cortexhub.client import CortexHub

logger = structlog.get_logger(__name__)


def auto_protect_frameworks(
    cortex_hub: "CortexHub",
    *,
    enable_llm: bool = True,
    enable_tools: bool = True,
) -> None:
    """Auto-detect and patch supported frameworks.

    Checks sys.modules to see which frameworks are loaded, then applies
    appropriate adapters.

    Args:
        cortex_hub: CortexHub instance
    """
    protected_count = 0

    # Check for LangChain
    if enable_tools and _is_langchain_available():
        logger.info("LangChain detected - applying adapter")
        try:
            from cortexhub.adapters.langchain import LangChainAdapter

            adapter = LangChainAdapter(cortex_hub)
            adapter.patch()
            protected_count += 1
        except Exception as e:
            logger.error("Failed to apply LangChain adapter", error=str(e))

    # Check for OpenAI Agents
    if enable_tools and _is_openai_agents_available():
        logger.info("OpenAI Agents detected - applying adapter")
        try:
            from cortexhub.adapters.openai_agents import OpenAIAgentsAdapter

            adapter = OpenAIAgentsAdapter(cortex_hub)
            adapter.patch()
            protected_count += 1
        except Exception as e:
            logger.error("Failed to apply OpenAI Agents adapter", error=str(e))

    # Check for CrewAI
    if enable_tools and _is_crewai_available():
        logger.info("CrewAI detected - applying adapter")
        try:
            from cortexhub.adapters.crewai import CrewAIAdapter

            adapter = CrewAIAdapter(cortex_hub)
            adapter.patch()
            protected_count += 1
        except Exception as e:
            logger.error("Failed to apply CrewAI adapter", error=str(e))

    # Check for LlamaIndex
    if enable_tools and _is_llamaindex_available():
        logger.info("LlamaIndex detected - applying adapter")
        try:
            from cortexhub.adapters.llamaindex import LlamaIndexAdapter

            adapter = LlamaIndexAdapter(cortex_hub)
            adapter.patch()
            protected_count += 1
        except Exception as e:
            logger.error("Failed to apply LlamaIndex adapter", error=str(e))

    if enable_llm and _is_litellm_available():
        logger.info("LiteLLM detected - applying adapter")
        try:
            from cortexhub.adapters.litellm import LiteLLMAdapter

            adapter = LiteLLMAdapter(cortex_hub)
            adapter.patch()
            protected_count += 1
        except Exception as e:
            logger.error("Failed to apply LiteLLM adapter", error=str(e))

    if protected_count == 0:
        logger.warning(
            "No supported frameworks detected. "
            "Make sure you import your framework before calling auto_protect()"
        )
    else:
        logger.info(f"Auto-protection enabled for {protected_count} framework(s)")


def _is_langchain_available() -> bool:
    """Check if LangChain is available."""
    langchain_modules = [
        "langchain",
        "langchain_core",
        "langchain.tools",
    ]
    return any(mod in sys.modules for mod in langchain_modules)


def _is_openai_agents_available() -> bool:
    """Check if OpenAI Agents is available."""
    return "openai_agents" in sys.modules or "agents" in sys.modules


def _is_crewai_available() -> bool:
    """Check if CrewAI is available."""
    return "crewai" in sys.modules


def _is_llamaindex_available() -> bool:
    """Check if LlamaIndex is available."""
    return any(mod in sys.modules for mod in ["llama_index", "llama_index.core"])


def _is_litellm_available() -> bool:
    """Check if LiteLLM is available."""
    return "litellm" in sys.modules
