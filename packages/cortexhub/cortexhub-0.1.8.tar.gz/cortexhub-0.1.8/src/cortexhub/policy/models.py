"""Core data models for authorization requests.

Critical: DO NOT simplify or flatten these models.
The structure is intentional and future-proof.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Principal(BaseModel):
    """Entity requesting to perform an action (e.g., an AI agent).
    
    Examples:
        Principal(type="Agent", id="customer_support")
        Principal(type="User", id="user_12345")
        Principal(type="Service", id="payment_processor")
    """

    type: str  # e.g., "Agent", "User", "Service"
    id: str  # e.g., "customer_support", "user_12345"


class Action(BaseModel):
    """Action being requested (e.g., tool invocation).
    
    Examples:
        Action(type="tool.invoke", name="send_email")
        Action(type="llm.call", name="gpt-4")
        Action(type="data.read", name="customer_records")
    """

    type: str  # e.g., "tool.invoke", "llm.call", "data.read"
    name: str  # e.g., "send_email", "gpt-4", "customer_records"


class Resource(BaseModel):
    """Resource being accessed (e.g., a tool, database, API).
    
    Examples:
        Resource(type="Tool", id="send_email")
        Resource(type="Database", id="customer_db")
        Resource(type="API", id="payment_gateway")
    """

    type: str  # e.g., "Tool", "Database", "API"
    id: str  # e.g., "send_email", "customer_db"


class RuntimeContext(BaseModel):
    """Runtime context about the framework and execution environment."""

    framework: str  # e.g., "langchain", "openai_agents"
    framework_version: str | None = None
    confidence: float | None = None  # Optional confidence score from LLM


class Metadata(BaseModel):
    """Tracing metadata for debugging and audit."""

    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuthorizationRequest(BaseModel):
    """Complete authorization request sent to the policy engine.

    This is the heart of the system. DO NOT simplify or flatten it.

    The context dict contains reserved top-level keys:
    - args: Tool arguments (dict)
    - runtime: RuntimeContext (framework info)
    - metadata: Metadata (trace_id, session_id, timestamp)
    
    Example:
        AuthorizationRequest(
            principal=Principal(type="Agent", id="customer_support"),
            action=Action(type="tool.invoke", name="send_email"),
            resource=Resource(type="Tool", id="send_email"),
            context={
                "args": {"to": "user@example.com", "body": "Hello"},
                "runtime": {"framework": "langchain"},
                "metadata": {"trace_id": "abc-123", "session_id": "sess-456"},
            },
        )
    """

    principal: Principal
    action: Action
    resource: Resource
    context: dict[str, Any]  # Reserved keys: args, runtime, metadata

    @property
    def trace_id(self) -> str:
        """Extract trace ID for logging/debugging."""
        metadata = self.context.get("metadata", {})
        if isinstance(metadata, dict):
            return metadata.get("trace_id", "unknown")
        if isinstance(metadata, Metadata):
            return metadata.trace_id
        return "unknown"
    
    @property
    def args(self) -> dict[str, Any]:
        """Extract args from context."""
        return self.context.get("args", {})

    def with_enriched_context(self, **kwargs) -> "AuthorizationRequest":
        """Return a new request with additional context.
        
        Does NOT mutate the original request.
        """
        new_context = {**self.context, **kwargs}
        return AuthorizationRequest(
            principal=self.principal,
            action=self.action,
            resource=self.resource,
            context=new_context,
        )
