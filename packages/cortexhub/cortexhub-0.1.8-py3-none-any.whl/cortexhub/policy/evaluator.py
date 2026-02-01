"""Policy evaluator using Cedar.

Architectural invariants (from AGENTS.md):
- MUST NOT read files directly (use loader.py)
- MUST NOT make decisions (only evaluate)

Uses cedarpy for production-grade policy evaluation.
"""

import os
import time
from datetime import datetime
from typing import Any

import structlog

from cortexhub.errors import PolicyLoadError

try:
    import cedarpy as cedar_module
except Exception as exc:
    raise PolicyLoadError(
        "Cedar policy engine is required for enforcement. Install with: uv add cedarpy",
        policies_dir="backend",
    ) from exc

from cortexhub.policy.effects import Decision, Effect
from cortexhub.policy.loader import PolicyBundle
from cortexhub.policy.models import AuthorizationRequest

logger = structlog.get_logger(__name__)


class PolicyEvaluator:
    """Evaluates authorization requests against Cedar policies.

    Deterministic guarantee: Same input → same output, always.
    Performance target: <0.5ms
    """

    def __init__(self, policy_bundle: PolicyBundle):
        """Initialize policy evaluator.

        Args:
            policy_bundle: Loaded policy bundle (from loader.py)
        """
        self.policy_bundle = policy_bundle
        self.default_behavior = policy_bundle.default_behavior

        try:
            logger.info(
                "Cedar policy evaluator initialized",
                version=policy_bundle.version,
                default_behavior=self.default_behavior,
                cedar_version="cedarpy",
            )
        except Exception as e:
            raise PolicyLoadError(
                f"Failed to initialize Cedar policy evaluator: {e}",
                policies_dir="backend",
            ) from e

    def evaluate(self, request: AuthorizationRequest) -> Decision:
        """Evaluate authorization request against policies.

        Deterministic: Same request always produces same decision.
        Performance target: <0.5ms

        Args:
            request: Authorization request to evaluate

        Returns:
            Decision (ALLOW/DENY/ESCALATE)
        """
        start_time = time.perf_counter()

        try:
            decision = self._evaluate_cedar(request)

            latency_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Policy evaluated",
                effect=decision.effect,
                latency_ms=f"{latency_ms:.3f}",
                trace_id=request.trace_id,
                tool=request.action.name,
            )

            return decision

        except Exception as e:
            logger.error("Policy evaluation failed", error=str(e), trace_id=request.trace_id)
            # Fail closed - deny on error
            return Decision.deny(f"Policy evaluation error: {e}")

    def _evaluate_cedar(self, request: AuthorizationRequest) -> Decision:
        """Evaluate using real Cedar engine.

        Args:
            request: Authorization request

        Returns:
            Decision
        """
        principal_type = request.principal.type
        principal_id = request.principal.id
        action = request.action.type
        resource_type = request.resource.type
        resource_id = request.resource.id

        cedar_request = {
            "principal": f'{principal_type}::"{principal_id}"',
            "action": f'Action::"{action}"',
            "resource": f'{resource_type}::"{resource_id}"',
            "context": self._json_safe(request.context),
        }

        result = cedar_module.is_authorized(
            request=cedar_request,
            policies=self.policy_bundle.policies,
            entities=[],
            schema=self.policy_bundle.schema or None,
        )
        policy_map = self.policy_bundle.metadata.get("policy_map", {}) if self.policy_bundle else {}
        if os.getenv("CORTEXHUB_CEDAR_DEBUG", "").lower() in ("1", "true", "yes"):
            logger.debug(
                "Cedar evaluation",
                decision=str(result.decision),
                reasons=result.diagnostics.reasons,
                policy_count=len(policy_map),
                action=request.action.type,
                resource=request.resource.type,
                guardrails=self._json_safe(request.context.get("guardrails", {})),
                redaction=self._json_safe(request.context.get("redaction", {})),
                context_summary=self._summarize_context(request.context),
            )

        def _resolve_policy_metadata(policy_id: str | None) -> tuple[str | None, str | None, str | None]:
            if policy_id:
                meta = policy_map.get(policy_id, {})
                return (
                    meta.get("policy_document_id") or policy_id,
                    meta.get("name"),
                    meta.get("effect"),
                )
            if len(policy_map) == 1:
                only_id = next(iter(policy_map.keys()))
                meta = policy_map.get(only_id, {})
                return (
                    meta.get("policy_document_id") or only_id,
                    meta.get("name"),
                    meta.get("effect"),
                )
            return None, None, None

        if result.decision == cedar_module.Decision.Allow:
            reason = result.diagnostics.reasons[0] if result.diagnostics.reasons else None
            policy_id, policy_name, policy_effect = _resolve_policy_metadata(reason)
            return Decision.allow(
                reasoning="Allowed by Cedar policy",
                policy_id=policy_id,
                policy_name=policy_name,
            )
        if result.decision == cedar_module.Decision.Deny:
            if not result.diagnostics.reasons:
                if self.default_behavior == "allow_and_log":
                    return Decision.allow(
                        f"Tool '{request.action.name}' allowed by default behavior",
                        policy_id="default",
                    )
                if self.default_behavior == "deny_and_log":
                    return Decision.deny(
                        f"Tool '{request.action.name}' denied by default behavior (no matching policy)",
                        policy_id="default",
                    )
                if self.default_behavior == "escalate":
                    return Decision.escalate(
                        f"Tool '{request.action.name}' requires approval (unknown tool)",
                        policy_id="default",
                    )
                return Decision.deny("Invalid default behavior configuration", policy_id="error")
            reason = result.diagnostics.reasons[0]
            policy_id, policy_name, policy_effect = _resolve_policy_metadata(reason)
            if policy_effect == "require_approval":
                return Decision.escalate(
                    reasoning="Approval required by policy",
                    policy_id=policy_id,
                    policy_name=policy_name,
                )
            if self._should_escalate(request):
                return Decision.escalate(
                    reasoning="High-risk operation requires approval",
                    policy_id=policy_id,
                    policy_name=policy_name,
                )
            return Decision.deny(
                reasoning="Denied by CortexHub Policy",
                policy_id=policy_id,
                policy_name=policy_name,
            )

        # NoDecision: apply default behavior
        if result.decision == cedar_module.Decision.NoDecision and self.default_behavior == "allow_and_log":
            return Decision.allow(
                f"Tool '{request.action.name}' allowed by default behavior",
                policy_id="default",
            )
        if result.decision == cedar_module.Decision.NoDecision and self.default_behavior == "deny_and_log":
            return Decision.deny(
                f"Tool '{request.action.name}' denied by default behavior (no matching policy)",
                policy_id="default",
            )
        if result.decision == cedar_module.Decision.NoDecision and self.default_behavior == "escalate":
            return Decision.escalate(
                f"Tool '{request.action.name}' requires approval (unknown tool)",
                policy_id="default",
            )
        return Decision.deny("Invalid default behavior configuration", policy_id="error")

    def _json_safe(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            cleaned: dict[str, Any] = {}
            for key, val in value.items():
                safe_val = self._json_safe(val)
                if safe_val is not None:
                    cleaned[key] = safe_val
            return cleaned
        if isinstance(value, list):
            return [item for item in (self._json_safe(item) for item in value) if item is not None]
        return value

    def _summarize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        def summarize(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: summarize(val) for key, val in value.items()}
            if isinstance(value, list):
                return [summarize(item) for item in value]
            return type(value).__name__

        return summarize(context)

    def _should_escalate(self, request: AuthorizationRequest) -> bool:
        """Determine if a DENY should be escalated to approval (Cedar version).

        Args:
            request: Authorization request

        Returns:
            True if should escalate
        """
        tool_name = request.action.name
        args = request.context.get("args", {})

        # High-value refunds
        if tool_name == "refund_payment":
            amount = args.get("amount", 0)
            return amount > 100

        # Other escalation rules can be added here
        return False

    
