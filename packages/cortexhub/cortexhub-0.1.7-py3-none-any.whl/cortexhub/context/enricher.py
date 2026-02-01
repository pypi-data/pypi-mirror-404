"""Context enrichment for policy evaluation.

Adds runtime context to authorization requests:
- Agent roles and metadata
- Temporal constraints (time of day, business hours)
- Regulatory flags (HIPAA, SOX, GDPR)
- User context (when available)
"""

from datetime import datetime
from typing import Any

import structlog

from cortexhub.policy.models import AuthorizationRequest

logger = structlog.get_logger(__name__)


class AgentRegistry:
    """Registry mapping agent IDs to roles and metadata."""

    def __init__(self):
        """Initialize agent registry."""
        self._agents: dict[str, dict[str, Any]] = {}

    def register(
        self,
        agent_id: str,
        role: str,
        permissions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register an agent with role and permissions.

        Args:
            agent_id: Unique agent identifier
            role: Agent role (e.g., "nurse", "refund_processor")
            permissions: List of allowed actions
            metadata: Additional metadata (tenure, department, etc.)
        """
        self._agents[agent_id] = {
            "role": role,
            "permissions": permissions or [],
            "metadata": metadata or {},
        }
        logger.info("Agent registered", agent_id=agent_id, role=role)

    def get(self, agent_id: str) -> dict[str, Any]:
        """Get agent metadata.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent metadata or empty dict if not found
        """
        return self._agents.get(agent_id, {})


class ContextEnricher:
    """Enriches authorization requests with runtime context.

    Adds:
    - Agent roles and permissions
    - Temporal constraints (time, business hours)
    - Regulatory flags (HIPAA, SOX compliance)
    - User context
    """

    def __init__(self, agent_registry: AgentRegistry | None = None):
        """Initialize context enricher.

        Args:
            agent_registry: Optional agent registry for role lookup
        """
        self.agent_registry = agent_registry or AgentRegistry()
        logger.info("Context enricher initialized")

    def enrich(self, request: AuthorizationRequest) -> AuthorizationRequest:
        """Enrich authorization request with additional context.

        INVARIANT: Enrichment may only ADD context keys, never MUTATE args or resource.
        This protects policy correctness and audit integrity.

        Args:
            request: Base authorization request

        Returns:
            Enriched authorization request
        """
        agent_id = request.principal.id

        # Get agent metadata
        agent_metadata = self.agent_registry.get(agent_id)

        if agent_metadata:
            # Add agent role
            request.context["agent_role"] = agent_metadata.get("role", "unknown")
            request.context["agent_permissions"] = agent_metadata.get("permissions", [])

            # Add agent metadata
            metadata_dict = agent_metadata.get("metadata", {})
            if metadata_dict:
                request.context["agent_metadata"] = metadata_dict

            logger.debug(
                "Agent context enriched",
                agent_id=agent_id,
                role=agent_metadata.get("role"),
                trace_id=request.trace_id,
            )

        # Add temporal context
        now = datetime.utcnow()
        request.context["temporal"] = {
            "timestamp": now.isoformat(),
            "hour": now.hour,
            "day_of_week": now.weekday(),  # 0=Monday, 6=Sunday
            "is_business_hours": self._is_business_hours(now),
        }

        # Add regulatory context (based on agent role)
        if agent_metadata:
            role = agent_metadata.get("role", "")
            request.context["regulatory"] = self._get_regulatory_context(role)

        return request

    def _is_business_hours(self, dt: datetime) -> bool:
        """Check if current time is within business hours.

        Args:
            dt: Datetime to check

        Returns:
            True if business hours (9 AM - 5 PM, Monday-Friday)
        """
        # Business hours: 9 AM - 5 PM, Monday-Friday
        is_weekday = dt.weekday() < 5  # 0-4 = Monday-Friday
        is_work_hours = 9 <= dt.hour < 17  # 9 AM - 5 PM
        return is_weekday and is_work_hours

    def _get_regulatory_context(self, role: str) -> dict[str, Any]:
        """Get regulatory context based on agent role.

        Args:
            role: Agent role

        Returns:
            Regulatory context dict
        """
        context = {
            "hipaa_applicable": False,
            "sox_applicable": False,
            "gdpr_applicable": False,
            "minimum_necessary": False,
        }

        # Healthcare roles = HIPAA
        if role in ["nurse", "doctor", "healthcare_agent", "patient_communication"]:
            context["hipaa_applicable"] = True
            context["minimum_necessary"] = True  # HIPAA minimum necessary rule

        # Financial roles = SOX
        if role in ["refund_processor", "billing_agent", "finance_agent"]:
            context["sox_applicable"] = True

        # All roles = GDPR (if EU)
        context["gdpr_applicable"] = True

        return context
