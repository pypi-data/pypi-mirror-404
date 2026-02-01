"""Decision effects from policy evaluation.

Critical: Determinism guarantee - Same AuthorizationRequest MUST always produce
same Decision. This is essential for testing and auditability.
"""

from enum import Enum

from pydantic import BaseModel


class Effect(str, Enum):
    """Policy decision effect."""

    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"
    REDACT = "redact"  # PII/secrets were redacted before LLM call


class Decision(BaseModel):
    """Result of policy evaluation.

    Attributes:
        effect: The decision (ALLOW/DENY/ESCALATE)
        reasoning: Human-readable explanation
        policy_id: Which policy triggered this decision (if any)
        policy_name: Friendly policy name (if available)
    """

    effect: Effect
    reasoning: str
    policy_id: str | None = None
    policy_name: str | None = None

    def is_allowed(self) -> bool:
        """Check if the decision allows execution."""
        return self.effect == Effect.ALLOW

    def is_denied(self) -> bool:
        """Check if the decision denies execution."""
        return self.effect == Effect.DENY

    def requires_approval(self) -> bool:
        """Check if the decision requires approval (escalation)."""
        return self.effect == Effect.ESCALATE

    @classmethod
    def allow(
        cls,
        reasoning: str = "Allowed by policy",
        policy_id: str | None = None,
        policy_name: str | None = None,
    ):
        """Create an ALLOW decision."""
        return cls(
            effect=Effect.ALLOW, reasoning=reasoning, policy_id=policy_id, policy_name=policy_name
        )

    @classmethod
    def deny(cls, reasoning: str, policy_id: str | None = None, policy_name: str | None = None):
        """Create a DENY decision."""
        return cls(
            effect=Effect.DENY, reasoning=reasoning, policy_id=policy_id, policy_name=policy_name
        )

    @classmethod
    def escalate(
        cls, reasoning: str, policy_id: str | None = None, policy_name: str | None = None
    ):
        """Create an ESCALATE decision."""
        return cls(
            effect=Effect.ESCALATE, reasoning=reasoning, policy_id=policy_id, policy_name=policy_name
        )

    @classmethod
    def redact(
        cls, reasoning: str, policy_id: str | None = None, policy_name: str | None = None
    ):
        """Create a REDACT decision (PII/secrets were redacted before execution)."""
        return cls(
            effect=Effect.REDACT, reasoning=reasoning, policy_id=policy_id, policy_name=policy_name
        )

    def is_redacted(self) -> bool:
        """Check if the decision resulted in redaction."""
        return self.effect == Effect.REDACT
