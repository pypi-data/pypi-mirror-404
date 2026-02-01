"""CortexHub Python SDK - Runtime Governance for AI Agents.

Add 2 lines to your existing agent code to get full governance:

    import cortexhub
    cortex = cortexhub.init("my_agent", cortexhub.Framework.LANGGRAPH)

That's it! CortexHub will:
- Monitor all tool calls and LLM interactions  
- Detect PII, secrets, and sensitive data in real-time
- Enforce policies (block, redact, require approval) based on your configuration

IMPORTANT: A valid API key is REQUIRED. Get yours at https://app.cortexhub.ai

Supported Agent Frameworks:
- LangGraph: Stateful agents with checkpointing and interrupt()
- CrewAI: Multi-agent crews with human_input support
- OpenAI Agents SDK: Native agents with needsApproval
- Claude Agent SDK: Computer-use agents with subagents

Installation:
    # Core SDK (includes Cedar, OpenTelemetry, Presidio, detect-secrets)
    pip install cortexhub
    
    # With framework adapter
    pip install cortexhub[langgraph]      # + LangGraph
    pip install cortexhub[crewai]         # + CrewAI  
    pip install cortexhub[openai-agents]  # + OpenAI Agents SDK
    pip install cortexhub[claude-agents]  # + Claude Agent SDK

Usage:
    import cortexhub
    
    # Set your API key (or use CORTEXHUB_API_KEY environment variable)
    # For LangGraph
    cortex = cortexhub.init("my_agent", cortexhub.Framework.LANGGRAPH)
    
    # For CrewAI
    cortex = cortexhub.init("my_crew", cortexhub.Framework.CREWAI)
    
    # For OpenAI Agents
    cortex = cortexhub.init("my_agent", cortexhub.Framework.OPENAI_AGENTS)
    
    # For Claude Agents
    cortex = cortexhub.init("my_agent", cortexhub.Framework.CLAUDE_AGENTS)
"""

from cortexhub.client import CortexHub
from cortexhub.frameworks import Framework
from cortexhub.version import __version__
from cortexhub.errors import (
    CortexHubError,
    ConfigurationError,
    PolicyViolationError,
    GuardrailViolationError,
    ApprovalRequiredError,
    ApprovalDeniedError,
    PolicyLoadError,
)

# Global instance for simple init() usage
_global_instance: CortexHub | None = None


def init(
    agent_id: str,
    framework: Framework,
    *,
    api_key: str | None = None,
    privacy: bool = True,
) -> CortexHub:
    """Initialize CortexHub governance for your AI agent.
    
    Call this ONCE at the start of your application, BEFORE importing
    your AI framework. CortexHub will automatically govern all tool 
    calls and LLM interactions.
    
    Args:
        agent_id: A stable identifier for your agent. Use something
                  descriptive like "customer_support_agent" or 
                  "financial_analysis_crew".
        framework: The AI agent framework you're using:
                   - Framework.LANGGRAPH (LangGraph)
                   - Framework.CREWAI (CrewAI)
                   - Framework.OPENAI_AGENTS (OpenAI Agents SDK)
                   - Framework.CLAUDE_AGENTS (Claude Agent SDK)
        api_key: Your CortexHub API key. Can also be set via the
                 CORTEXHUB_API_KEY environment variable.
        privacy: If True (default), only metadata is sent to cloud.
                 If False, raw data is included for testing redaction.
    
    Returns:
        CortexHub instance
    
    Example:
        import cortexhub
        
        # Initialize before importing your framework
        cortex = cortexhub.init("customer_support", cortexhub.Framework.LANGGRAPH)
        
        # Now import and use LangGraph as normal
        from langgraph.prebuilt import create_react_agent
        
        # All tool calls are now governed by CortexHub
    """
    global _global_instance
    
    _global_instance = CortexHub(
        api_key=api_key,
        agent_id=agent_id,
        privacy=privacy,
    )
    
    # Apply the framework-specific adapter
    _global_instance.protect(framework)
    
    return _global_instance


def get_instance() -> CortexHub | None:
    """Get the global CortexHub instance.
    
    Returns None if init() hasn't been called.
    """
    return _global_instance


__all__ = [
    # Main API
    "init",
    "get_instance",
    "CortexHub",
    "Framework",
    "__version__",
    # Errors (for exception handling)
    "CortexHubError",
    "ConfigurationError",
    "PolicyViolationError",
    "GuardrailViolationError",
    "ApprovalRequiredError",
    "ApprovalDeniedError",
    "PolicyLoadError",
]
