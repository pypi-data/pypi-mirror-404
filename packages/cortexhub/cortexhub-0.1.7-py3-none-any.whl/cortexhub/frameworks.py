"""Supported framework definitions.

Users specify which framework they're using via the Framework enum.
This avoids fragile auto-detection and makes dependencies explicit.

We support AGENT frameworks only - not LLM proxies or RAG tools.
"""

from enum import Enum


class Framework(str, Enum):
    """Supported AI agent frameworks.
    
    CortexHub supports frameworks that provide agent orchestration with
    native approval/human-in-the-loop mechanisms:
    
    - LangGraph: Checkpointing + interrupt()
    - CrewAI: human_input=True
    - OpenAI Agents SDK: needsApproval + state serialization
    - Claude Agent SDK: Subagents + tool-based
    
    Usage:
        import cortexhub
        cortex = cortexhub.init("my_agent", cortexhub.Framework.LANGGRAPH)
    
    Each framework requires its corresponding optional dependency:
        pip install cortexhub[langgraph]
        pip install cortexhub[crewai]
        pip install cortexhub[openai-agents]
        pip install cortexhub[claude-agents]
    """
    
    LANGGRAPH = "langgraph"
    """LangGraph - Stateful agent orchestration.
    
    Features:
    - Graph-based agent workflows
    - Checkpointing for pause/resume
    - interrupt() for human-in-the-loop
    - Cycles and branches
    
    Install: pip install cortexhub[langgraph]
    """
    
    CREWAI = "crewai"
    """CrewAI - Multi-agent crews.
    
    Features:
    - Role-based agents
    - Sequential and hierarchical processes
    - human_input=True for approval
    - Task delegation
    
    Install: pip install cortexhub[crewai]
    """
    
    OPENAI_AGENTS = "openai_agents"
    """OpenAI Agents SDK.
    
    Features:
    - Native tool calling
    - needsApproval for human-in-the-loop
    - State serialization for pause/resume
    - Handoffs between agents
    
    Install: pip install cortexhub[openai-agents]
    """
    
    CLAUDE_AGENTS = "claude_agents"
    """Claude Agent SDK (formerly Claude Code SDK).
    
    Features:
    - Computer use (bash, files, code)
    - Subagents for parallelization
    - MCP integration
    - Context compaction
    
    Install: pip install cortexhub[claude-agents]
    """
    
    def __str__(self) -> str:
        return self.value
