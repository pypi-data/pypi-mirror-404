"""Audit event schemas for governance telemetry.

All events include trace_id for traceability across spans and debugging.
Uses Pydantic for type-safe, structured events.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    """Base event with common fields for all audit events."""

    event_type: str
    trace_id: str
    session_id: str | None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence: int  # Monotonic sequence number per session for replay ordering


class ToolInvocationEvent(BaseEvent):
    """Event logged when a tool is invoked.
    
    SDK is DUMB - just sends metadata, no classifications or counts.
    Backend aggregates and uses LLM for analysis.
    
    NOTE: No guardrail findings here - tools NEED the sensitive data to work.
    NOTE: Argument VALUES only sent when privacy=False (for dev/testing).
    """

    event_type: str = "tool.invocation"
    tool_name: str
    tool_description: str | None = None  # Human-readable description from framework
    arg_names: list[str] = Field(default_factory=list)  # Argument names only (NOT values)
    framework: str  # "langchain", "openai_agents", etc.
    agent_id: str | None = None  # Agent identifier (from cortexhub.init)
    
    # Only populated when privacy=False (for testing policies in dev/staging)
    args: dict[str, Any] | None = None  # Raw argument values (NEVER in production!)


class PolicyDecisionEvent(BaseEvent):
    """Event logged for policy evaluation results."""

    event_type: str = "policy.decision"
    effect: str  # "allow", "deny", "escalate"
    policy_id: str | None
    reasoning: str
    latency_ms: float  # Time taken to evaluate policy
    agent_id: str | None = None  # Agent identifier
    tool_name: str | None = None  # Tool being evaluated


class GuardrailViolationEvent(BaseEvent):
    """Event logged when a guardrail detects a violation."""

    event_type: str = "guardrail.violation"
    guardrail_type: str  # "pii", "secrets", "injection"
    findings: list[dict[str, Any]]  # Detailed findings (entities, locations, scores)
    blocked: bool  # Whether execution was blocked


class ApprovalRequestEvent(BaseEvent):
    """Event logged for approval requests (ESCALATE flow)."""

    event_type: str = "approval.request"
    tool_name: str
    args: dict[str, Any]
    approved: bool | None  # None if pending, True/False after decision
    approver: str | None  # Who approved/denied (None for auto-approve/deny)
    approval_mode: str  # "auto-approve", "auto-deny", "cli-prompt"


class ToolExecutionEvent(BaseEvent):
    """Event logged after tool execution completes."""

    event_type: str = "tool.execution"
    tool_name: str
    success: bool
    error: str | None  # Error message if execution failed
    latency_ms: float  # Time taken to execute tool
    agent_id: str | None = None  # Agent identifier
    
    # Only populated when privacy=False (for testing policies in dev/staging)
    result: Any | None = None  # Raw result (NEVER in production!)


class LLMGuardrailFindings(BaseModel):
    """Guardrail findings for LLM calls.
    
    THIS is where guardrails matter - sensitive data should NOT go to LLMs.
    """
    pii_in_prompt: dict[str, Any] = Field(default_factory=lambda: {
        "detected": False,
        "count": 0,
        "types": [],  # ["email_address", "person", "ssn"]
        "findings": [],  # [{"type": "email", "score": 0.95}]
    })
    secrets_in_prompt: dict[str, Any] = Field(default_factory=lambda: {
        "detected": False,
        "count": 0,
        "types": [],  # ["api_key", "password"]
        "findings": [],
    })
    pii_in_response: dict[str, Any] = Field(default_factory=lambda: {
        "detected": False,
        "count": 0,
        "types": [],
        "findings": [],
    })
    prompt_manipulation: dict[str, Any] = Field(default_factory=lambda: {
        "detected": False,
        "count": 0,
        "patterns": [],  # ["ignore_instructions", "jailbreak"]
        "findings": [],
    })


class LLMCallEvent(BaseEvent):
    """Event logged for LLM API calls.
    
    Guardrails ARE relevant here - sensitive data flowing to LLMs is a risk.
    """

    event_type: str = "llm.call"
    model: str  # "gpt-4", "claude-3", etc.
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: float = 0.0
    cost_estimate: float | None = None
    agent_id: str | None = None  # Agent identifier (same as tool calls)
    
    # Rich guardrail findings - THIS is where guardrails matter
    guardrail_findings: LLMGuardrailFindings = Field(default_factory=LLMGuardrailFindings)
    
    # Only populated when privacy=False (for testing policies in dev/staging)
    prompt: str | None = None  # Raw prompt content (NEVER in production!)
    response: str | None = None  # Raw response content (NEVER in production!)


class AgentDecisionEvent(BaseEvent):
    """Event logged for agent decision-making."""

    event_type: str = "agent.decision"
    agent_id: str
    agent_role: str | None
    decision: str  # What the agent decided to do
    reasoning: str | None  # Why the agent made this decision (from LLM output)
    alternatives_considered: list[str] | None  # Other options the agent considered
    confidence: float | None  # Confidence score (0-1)
    context_used: dict[str, Any]  # What context the agent had


class ComplianceEvent(BaseEvent):
    """Event logged for regulatory compliance tracking."""

    event_type: str = "compliance.audit"
    regulation: str  # "HIPAA", "SOX", "GDPR"
    regulation_section: str | None  # e.g., "164.312(a)(1)"
    access_justification: str  # Why data was accessed (HIPAA minimum necessary)
    data_classification: str | None  # "PHI", "PII", "confidential"
    compliant: bool  # Whether action was compliant
    violations: list[str] | None  # Any violations detected
