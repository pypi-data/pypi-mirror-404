# CortexHub Python SDK

**Runtime Governance for AI Agents** - Policy enforcement, PII/secrets detection, complete audit trails with OpenTelemetry.

## Installation

```bash
# Core SDK
pip install cortexhub

# With framework support (choose one or more)
pip install cortexhub[langgraph]      # LangGraph
pip install cortexhub[crewai]         # CrewAI
pip install cortexhub[openai-agents]  # OpenAI Agents SDK
pip install cortexhub[claude-agents]  # Claude Agent SDK

# All frameworks (for development)
pip install cortexhub[all]
```

## Quick Start

```python
from cortexhub import init, Framework

# Initialize CortexHub FIRST, before importing your framework
cortex = init(
    agent_id="customer_support_agent",
    framework=Framework.LANGGRAPH,  # or CREWAI, OPENAI_AGENTS, CLAUDE_AGENTS
)

# Now import and use your framework
from langgraph.prebuilt import create_react_agent

# Continue with your LangGraph setup...
```

## Supported Frameworks

| Framework | Enum Value | Install |
|-----------|------------|---------|
| LangGraph | `Framework.LANGGRAPH` | `pip install cortexhub[langgraph]` |
| CrewAI | `Framework.CREWAI` | `pip install cortexhub[crewai]` |
| OpenAI Agents | `Framework.OPENAI_AGENTS` | `pip install cortexhub[openai-agents]` |
| Claude Agents | `Framework.CLAUDE_AGENTS` | `pip install cortexhub[claude-agents]` |

## Tracing Coverage

All frameworks emit `run.started` and `run.completed`/`run.failed` for each run.
Tool spans (`tool.invoke`) and model spans (`llm.call`) vary by SDK:

- **LangGraph**: tool calls via `BaseTool.invoke`, LLM calls via `BaseChatModel.invoke/ainvoke`
- **CrewAI**: tool calls via `CrewStructuredTool.invoke`/`BaseTool.run`, LLM calls via LiteLLM and `BaseLLM.call/acall`
- **OpenAI Agents**: tool calls via `function_tool`, LLM calls via `OpenAIResponsesModel` and `OpenAIChatCompletionsModel`
- **Claude Agents**: tool calls via `@tool` and built-in tool hooks; LLM calls run inside the Claude Code CLI and are not intercepted by the Python SDK

## Configuration

```bash
# Required: API key
export CORTEXHUB_API_KEY=ch_live_...

```

## Features

- **Policy Enforcement** - Cloud configuration, local evaluation
- **PII Detection** - 50+ entity types, configurable
- **Secrets Detection** - 30+ secret types
- **Configurable Guardrails** - Select specific PII/secret types to redact
- **Custom Patterns** - Add company-specific regex patterns
- **OpenTelemetry** - Industry-standard observability
- **Framework Adapters** - Automatic interception for all major frameworks
- **Privacy Mode** - Metadata-only by default, safe for production

## Privacy Modes

```python
# Production (default) - only metadata sent
cortex = init(agent_id="...", framework=..., privacy=True)
# Sends: tool names, arg schemas, PII types detected
# Never: raw values, prompts, responses

# Development - full data for testing policies  
cortex = init(agent_id="...", framework=..., privacy=False)
# Also sends: raw args, results, prompts (for policy testing)
```

## Policy Enforcement

Policies are created in the CortexHub dashboard from detected risks. The SDK automatically fetches and enforces them:

```python
from cortexhub.errors import PolicyViolationError, ApprovalRequiredError

# Policies are fetched automatically during init()
# If policies exist, enforcement mode is enabled

try:
    agent.run("Process a $10,000 refund")
except PolicyViolationError as e:
    print(f"Blocked by policy: {e.policy_name}")
    print(f"Reason: {e.reasoning}")
except ApprovalRequiredError as e:
    print(f"\n⏸️  APPROVAL REQUIRED")
    print(f"   Approval ID: {e.approval_id}")
    print(f"   Tool: {e.tool_name}")
    print(f"   Reason: {e.reason}")
    print(f"   Expires: {e.expires_at}")
    print(f"\n   Decision endpoint: {e.decision_endpoint}")
    print(f"   Configure a webhook to receive approval.decisioned event")
```

## Guardrail Configuration

Guardrails detect PII and secrets in LLM prompts. Configure in the dashboard:

1. **Select types to redact**: Choose specific PII types (email, phone, etc.)
2. **Add custom patterns**: Regex for company-specific data (employee IDs, etc.)
3. **Choose action**: Redact, block, or monitor only

The SDK applies your configuration automatically:

```python
# With guardrail policy active:
# Input prompt: "Contact john@email.com about employee EMP-123456"
# After redaction: "Contact [REDACTED-EMAIL_ADDRESS] about employee [REDACTED-CUSTOM_EMPLOYEE_ID]"
# Only configured types are redacted
```

## Important: Initialization Order

**Always initialize CortexHub FIRST**, before importing your framework:

```python
# ✅ CORRECT
from cortexhub import init, Framework
cortex = init(agent_id="my_agent", framework=Framework.LANGGRAPH)

from langgraph.prebuilt import create_react_agent  # Import AFTER init

# ❌ WRONG
from langgraph.prebuilt import create_react_agent  # Framework imported first
from cortexhub import init, Framework
cortex = init(...)  # Too late!
```

This ensures:
1. CortexHub sets up OpenTelemetry before frameworks that also use it
2. Framework decorators/classes are properly wrapped

## Architecture

```
Agent Decides → [CortexHub] → Agent Executes
                    │
              ┌─────┴─────┐
              │           │
         Policy      Guardrails
         Engine      (PII/Secrets)
              │           │
              └─────┬─────┘
                    │
              OpenTelemetry
               (to backend)
```

## Development

```bash
cd python

# Install with all frameworks
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Links

- [Documentation](https://docs.cortexhub.ai)
- [Dashboard](https://app.cortexhub.ai)
- [Issues](https://github.com/cortexhub/sdks/issues)

## License

MIT
