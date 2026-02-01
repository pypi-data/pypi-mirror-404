"""Backend API client for SDK."""

import os
import re
import structlog
import httpx
from typing import Any
from dataclasses import dataclass


logger = structlog.get_logger(__name__)


@dataclass
class CustomPattern:
    """Custom regex pattern for detection."""
    name: str
    pattern: str
    description: str | None = None
    enabled: bool = True


@dataclass
class GuardrailConfig:
    """Configuration for guardrail policies (PII/Secrets).
    
    Controls which types are detected and redacted.
    """
    action: str = "redact"  # redact, block, allow
    pii_types: list[str] | None = None  # None = all types
    secret_types: list[str] | None = None
    custom_patterns: list[CustomPattern] | None = None
    # Where to apply redaction: "input_only", "output_only", or "both"
    redaction_scope: str = "both"


@dataclass
class PolicyBundle:
    """Policy bundle from backend.
    
    When policies is empty, SDK runs in observation mode.
    When policies has content, SDK runs in enforcement mode.
    """
    version: str
    policies: str  # Cedar policies (empty = observation mode)
    schema: dict[str, Any] | None = None
    policy_metadata: dict[str, dict[str, Any]] | None = None
    # Guardrail configurations (keyed by policy type: "pii", "secrets")
    guardrail_configs: dict[str, GuardrailConfig] | None = None


@dataclass
class SDKConfig:
    """SDK configuration from backend.
    
    Returned during API key validation.
    """
    project_id: str
    organization_id: str
    plan: str
    policies: PolicyBundle
    
    @property
    def has_policies(self) -> bool:
        """Check if policies are present (enforcement mode)."""
        return bool(self.policies.policies.strip())


class BackendClient:
    """Client for communicating with CortexHub backend.
    
    Handles:
    - API key validation + policy retrieval
    """

    def __init__(self, api_key: str | None, backend_url: str):
        """Initialize backend client.
        
        Args:
            api_key: API key for authentication
            backend_url: Backend API URL
        """
        self.api_key = api_key
        self.backend_url = backend_url.rstrip("/")
        self._client: httpx.Client | None = None
        
        if api_key:
            self._client = httpx.Client(
                base_url=self.backend_url,
                headers={"X-API-Key": api_key},
                timeout=10.0,
            )
    
    def validate_api_key(self, *, agent_id: str | None = None) -> tuple[bool, SDKConfig | None]:
        """Validate API key with backend and get SDK configuration.
        
        Returns:
            (is_valid, SDKConfig or None)
            
        SDKConfig includes:
            - project_id, organization_id, environment
            - policies (empty = observation mode, non-empty = enforcement mode)
        """
        if not self.api_key or not self._client:
            return False, None
        
        try:
            # Note: base_url already includes /v1, so just /api-keys/validate
            response = self._client.post(
                "/api-keys/validate",
                headers={"X-API-Key": self.api_key},
                timeout=5.0,
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if valid
                if not data.get("valid", False):
                    logger.warning("API key validation failed", message=data.get("message"))
                    return False, None
                
                # Parse policy bundle from backend
                # Backend returns: { policies: { version, policies: [...policy objects...] } }
                policies_data = data.get("policies", {})
                
                # Convert policy objects to Cedar string if needed
                raw_policies = policies_data.get("policies", [])
                if agent_id:
                    raw_policies = [
                        policy for policy in raw_policies if policy.get("agent_id") == agent_id
                    ]
                guardrail_configs: dict[str, GuardrailConfig] = {}

                def _merge_guardrail_config(
                    existing: GuardrailConfig | None,
                    incoming: GuardrailConfig,
                ) -> GuardrailConfig:
                    if not existing:
                        return incoming
                    priority = {"block": 3, "redact": 2, "allow": 1}
                    action = (
                        incoming.action
                        if priority.get(incoming.action, 0) > priority.get(existing.action, 0)
                        else existing.action
                    )
                    if existing.pii_types is None or incoming.pii_types is None:
                        pii_types = None
                    else:
                        pii_types = sorted(set(existing.pii_types + incoming.pii_types))
                    if existing.secret_types is None or incoming.secret_types is None:
                        secret_types = None
                    else:
                        secret_types = sorted(set(existing.secret_types + incoming.secret_types))
                    custom_patterns = (existing.custom_patterns or []) + (incoming.custom_patterns or [])
                    if existing.redaction_scope == "both" or incoming.redaction_scope == "both":
                        redaction_scope = "both"
                    elif existing.redaction_scope != incoming.redaction_scope:
                        redaction_scope = "both"
                    else:
                        redaction_scope = existing.redaction_scope
                    return GuardrailConfig(
                        action=action,
                        pii_types=pii_types,
                        secret_types=secret_types,
                        custom_patterns=custom_patterns,
                        redaction_scope=redaction_scope,
                    )
                
                if isinstance(raw_policies, list):
                    # Backend returns list of policy objects - extract Cedar code
                    cedar_parts = []
                    policy_map = {}
                    cedar_index = 0
                    for p in raw_policies:
                        if p.get("cedar_policy"):
                            cedar_parts.append(f"// Policy: {p.get('name')} (tool: {p.get('tool_name')})")
                            cedar_parts.append(p.get("cedar_policy"))
                            cedar_parts.append("")
                            policy_text = p.get("cedar_policy") or ""
                            statement_count = len(
                                re.findall(r"\b(permit|forbid)\s*\(", policy_text)
                            )
                            if statement_count == 0:
                                continue
                            for _ in range(statement_count):
                                policy_map[f"policy{cedar_index}"] = {
                                    "name": p.get("name"),
                                    "effect": p.get("effect"),
                                    "tool_name": p.get("tool_name"),
                                    "policy_document_id": p.get("id"),
                                    "approval_destination": p.get("approval_destination"),
                                    "approval_webhook_id": p.get("approval_webhook_id"),
                                }
                                cedar_index += 1
                        
                        # Extract guardrail config if present
                        gc = p.get("guardrail_config")
                        if gc:
                            policy_key = p.get("policy_key", "")
                            if "pii" in policy_key:
                                custom_patterns = []
                                # Handle None explicitly (custom_patterns can be null in JSON)
                                raw_patterns = gc.get("custom_patterns") or []
                                for cp in raw_patterns:
                                    custom_patterns.append(CustomPattern(
                                        name=cp.get("name", ""),
                                        pattern=cp.get("pattern", ""),
                                        description=cp.get("description"),
                                        enabled=cp.get("enabled", True),
                                    ))
                                merged = _merge_guardrail_config(
                                    guardrail_configs.get("pii"),
                                    GuardrailConfig(
                                        action=gc.get("action", "redact"),
                                        pii_types=gc.get("pii_types"),
                                        custom_patterns=custom_patterns if custom_patterns else None,
                                        redaction_scope=gc.get("redaction_scope", "both"),
                                    ),
                                )
                                guardrail_configs["pii"] = merged
                            elif "secrets" in policy_key:
                                custom_patterns = []
                                raw_patterns = gc.get("custom_patterns") or []
                                for cp in raw_patterns:
                                    custom_patterns.append(CustomPattern(
                                        name=cp.get("name", ""),
                                        pattern=cp.get("pattern", ""),
                                        description=cp.get("description"),
                                        enabled=cp.get("enabled", True),
                                    ))
                                merged = _merge_guardrail_config(
                                    guardrail_configs.get("secrets"),
                                    GuardrailConfig(
                                        action=gc.get("action", "redact"),
                                        secret_types=gc.get("secret_types"),
                                        custom_patterns=custom_patterns if custom_patterns else None,
                                        redaction_scope=gc.get("redaction_scope", "both"),
                                    ),
                                )
                                guardrail_configs["secrets"] = merged
                    policies_str = "\n".join(cedar_parts)
                else:
                    policies_str = raw_policies or ""
                    policy_map = {}
                
                policies = PolicyBundle(
                    version=policies_data.get("version", "0"),
                    policies=policies_str,
                    schema=policies_data.get("schema"),
                    policy_metadata=policy_map,
                    guardrail_configs=guardrail_configs if guardrail_configs else None,
                )
                
                config = SDKConfig(
                    project_id=data.get("project_id", ""),
                    organization_id=data.get("org_id", ""),
                    plan=data.get("plan", "free"),
                    policies=policies,
                )
                
                mode = "enforcement" if config.has_policies else "observation"
                logger.info(
                    "API key validated",
                    project_id=config.project_id,
                    mode=mode,
                    policy_version=policies.version,
                )
                if os.getenv("CORTEXHUB_DEBUG_POLICY_BUNDLE", "").lower() in ("1", "true", "yes"):
                    logger.info(
                        "Policy bundle received",
                        policy_count=len(policy_map),
                        policy_ids=list(policy_map.keys()),
                        policy_effects={k: v.get("effect") for k, v in policy_map.items()},
                    )
                    if os.getenv("CORTEXHUB_DEBUG_POLICY_TEXT", "").lower() in (
                        "1",
                        "true",
                        "yes",
                    ):
                        logger.info("Policy bundle cedar", policies=policies_str)
                return True, config
            else:
                error_detail = response.json().get("detail", "Invalid API key")
                logger.warning("API key validation failed", error=error_detail)
                return False, None
                
        except httpx.ConnectError:
            logger.warning(
                "Backend unreachable - running in offline observation mode",
                backend_url=self.backend_url,
            )
            return False, None
        except Exception as e:
            logger.error("API key validation error", error=str(e))
            return False, None
    
    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()

    def create_approval(
        self,
        *,
        run_id: str,
        trace_id: str | None,
        tool_name: str,
        tool_args_values: dict[str, Any] | None,
        context_hash: str,
        policy_id: str,
        policy_name: str,
        policy_explanation: str,
        risk_category: str | None,
        agent_id: str,
        framework: str,
        environment: str | None = None,
        expires_in_seconds: int = 3600,
    ) -> dict[str, Any]:
        """Create approval request. Idempotent on natural key."""

        if not self._client:
            raise RuntimeError("Backend client not initialized")

        response = self._client.post(
            "/approvals",
            json={
                "run_id": run_id,
                "trace_id": trace_id,
                "tool_name": tool_name,
                "tool_args_values": tool_args_values,
                "context_hash": context_hash,
                "policy_id": policy_id,
                "policy_name": policy_name,
                "policy_explanation": policy_explanation,
                "risk_category": risk_category,
                "agent_id": agent_id,
                "framework": framework,
                "environment": environment,
                "expires_in_seconds": expires_in_seconds,
            },
        )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error(
                "Approval creation failed",
                status_code=response.status_code,
                response_text=response.text,
            )
            raise

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error(
                "Approval creation returned invalid JSON",
                status_code=response.status_code,
                response_text=response.text,
            )
            raise RuntimeError("Approval creation returned invalid JSON") from exc

        if not payload.get("approval_id"):
            logger.error("Approval creation missing approval_id", payload=payload)
            raise RuntimeError("Approval creation response missing approval_id")

        return payload
