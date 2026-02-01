"""Exception types for CortexHub SDK.

Distinct error types for debugging without ambiguity.
"""

from typing import Any


class CortexHubError(Exception):
    """Base exception for all CortexHub errors."""

    pass


class ConfigurationError(CortexHubError):
    """Raised when SDK configuration is invalid (missing API key, etc.)."""

    pass


class PolicyViolationError(CortexHubError):
    """Raised when a policy forbids a tool invocation (effect=DENY)."""

    def __init__(self, message: str, policy_id: str | None = None, reasoning: str = ""):
        super().__init__(message)
        self.policy_id = policy_id
        self.reasoning = reasoning


class GuardrailViolationError(CortexHubError):
    """Raised when a guardrail detects a violation (PII, secrets, injection)."""

    def __init__(
        self,
        message: str,
        guardrail_type: str,
        findings: list[dict] | None = None,
    ):
        super().__init__(message)
        self.guardrail_type = guardrail_type
        self.findings = findings or []


class ApprovalRequiredError(CortexHubError):
    """Raised when policy requires human approval before execution.

    The SDK creates an approval record in CortexHub cloud. Customer's system
    receives an approval.requested webhook and handles the approval workflow.
    After decision, customer resumes the agent using framework-native mechanisms.

    Attributes:
        approval_id: Cloud approval record ID (apr_xxx)
        run_id: SDK session ID for correlation
        tool_name: Name of the tool requiring approval
        policy_id: Policy that triggered escalation
        policy_name: Human-readable policy name
        reason: Policy explanation (why approval is required)
        expires_at: When approval expires (ISO format)
        decision_endpoint: URL to submit decision
    """

    def __init__(
        self,
        message: str,
        *,
        approval_id: str,
        run_id: str,
        tool_name: str,
        policy_id: str | None = None,
        policy_name: str | None = None,
        reason: str = "",
        expires_at: str | None = None,
        decision_endpoint: str | None = None,
    ):
        super().__init__(message)
        self.approval_id = approval_id
        self.run_id = run_id
        self.tool_name = tool_name
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.reason = reason
        self.expires_at = expires_at
        self.decision_endpoint = decision_endpoint

    def to_dict(self) -> dict[str, Any]:
        """Deterministic outcome for customer handling."""
        return {
            "type": "approval_required",
            "blocked": True,
            "approval_id": self.approval_id,
            "run_id": self.run_id,
            "tool_name": self.tool_name,
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "reason": self.reason,
            "expires_at": self.expires_at,
            "decision_endpoint": self.decision_endpoint,
        }


class ApprovalDeniedError(CortexHubError):
    """Raised when an approval request is denied or expired."""

    def __init__(
        self,
        message: str,
        *,
        approval_id: str,
        denied_by: str | None = None,
        reason: str = "",
    ):
        super().__init__(message)
        self.approval_id = approval_id
        self.denied_by = denied_by
        self.reason = reason


class PolicyLoadError(CortexHubError):
    """Raised when policy bundle cannot be loaded or is invalid."""

    def __init__(self, message: str, policies_dir: str):
        super().__init__(message)
        self.policies_dir = policies_dir
