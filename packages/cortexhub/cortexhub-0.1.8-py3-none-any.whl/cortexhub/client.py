"""CortexHub client - main SDK entrypoint.

MODE DETERMINATION
==================
The SDK mode is determined AUTOMATICALLY by the backend:

1. No policies from backend → OBSERVATION MODE
   - Records all agent activity (tool calls, LLM interactions, etc.)
   - Detects PII, secrets, prompt manipulation (logged, not blocked)
   - Sends OpenTelemetry spans to cloud for analysis
   - Compliance teams analyze behavior and create policies

2. Policies from backend → ENFORCEMENT MODE
   - Evaluates Cedar policies before execution
   - Can block, redact, or require approvals based on policies
   - Policies are created by compliance team in CortexHub Cloud

Architecture:
- Adapters call execute_governed_tool() - single entrypoint
- SDK creates OpenTelemetry spans for all activity
- Spans are sent to cloud via OTLP/HTTP (batched, non-blocking)
- Policy enforcement only when backend provides policies

Privacy Mode:
- privacy=True (default): Only metadata sent (production-safe)
- privacy=False: Raw data included (for testing policies in dev/staging)
"""

import contextvars
import json
import os
import time
import uuid
from typing import TYPE_CHECKING, Any, Callable, Tuple

if TYPE_CHECKING:
    from cortexhub.frameworks import Framework

import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource as OtelResource
from opentelemetry.trace import Status, StatusCode

from cortexhub.backend.client import BackendClient
from cortexhub.context.enricher import AgentRegistry, ContextEnricher
from cortexhub.errors import ApprovalRequiredError, ApprovalDeniedError, PolicyViolationError
from cortexhub.audit.events import LLMGuardrailFindings
from cortexhub.guardrails.injection import PromptManipulationDetector
from cortexhub.guardrails.pii import PIIDetector
from cortexhub.guardrails.secrets import SecretsDetector
from cortexhub.interceptors.llm import LLMInterceptor
from cortexhub.interceptors.mcp import MCPInterceptor
from cortexhub.policy.effects import Decision, Effect
from cortexhub.policy.evaluator import PolicyEvaluator
from cortexhub.policy.models import (
    Action,
    AuthorizationRequest,
    Metadata,
    Principal,
    Resource as PolicyResource,
    RuntimeContext,
)
from cortexhub.version import __version__

logger = structlog.get_logger(__name__)
_run_depth: contextvars.ContextVar[int] = contextvars.ContextVar("cortexhub_run_depth", default=0)
_session_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "cortexhub_session_id",
    default=None,
)


class CortexHub:
    """Main CortexHub SDK client.

    Privacy-first governance for AI agents using OpenTelemetry.

    Architecture:
    - Adapters call execute_governed_tool() - single entrypoint
    - SDK creates OpenTelemetry spans for all activity
    - Spans are batched and sent via OTLP/HTTP to backend
    - Policy enforcement only when backend provides policies
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str | None = None,
        agent_id: str | None = None,
        privacy: bool = True,
    ):
        """Initialize CortexHub client.

        A valid API key is REQUIRED. The SDK will not function without it.

        Args:
            api_key: CortexHub API key (REQUIRED - get from https://app.cortexhub.ai)
            api_url: CortexHub API URL (optional, defaults to https://api.cortexhub.ai)
            agent_id: Stable agent identifier (e.g., "customer_support_agent")
            privacy: If True (default), only metadata is sent to backend.
                     If False, raw inputs/outputs are also sent - useful for
                     testing policies, redaction, and approval workflows in
                     non-production environments. NEVER set to False in production!
        
        Raises:
            ValueError: If no API key is provided
            RuntimeError: If API key validation fails
        """
        from cortexhub.errors import ConfigurationError
        
        # Agent identity - stable across framework adapters
        self.agent_id = agent_id or os.getenv("CORTEXHUB_AGENT_ID") or self._default_agent_id()

        # Backend connection - API key is REQUIRED
        self.api_key = api_key or os.getenv("CORTEXHUB_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "CortexHub API key is required. "
                "Set CORTEXHUB_API_KEY environment variable or pass api_key parameter. "
                "Get your API key from https://app.cortexhub.ai"
            )
        
        self.api_url = self._normalize_api_url(
            api_url or os.getenv("CORTEXHUB_API_URL", "https://api.cortexhub.ai")
        )
        self.api_base_url = f"{self.api_url}/v1"

        # Privacy mode - controls whether raw data is sent
        # True (default): Only metadata sent (production-safe)
        # False: Raw inputs/outputs sent (for testing policies in dev/staging)
        privacy_env = os.getenv("CORTEXHUB_PRIVACY", "true").lower()
        self.privacy = privacy if privacy is not None else (privacy_env != "false")

        if not self.privacy:
            logger.warning(
                "⚠️  PRIVACY MODE DISABLED - Raw inputs/outputs will be sent to backend",
                warning="DO NOT USE IN PRODUCTION",
                use_case="Testing policies, redaction, and approval workflows",
            )

        # Internal state
        self._project_id: str | None = None
        self._sdk_config = None  # SDKConfig from backend
        self._session_id = self._generate_session_id()

        # Initialize OpenTelemetry
        self._tracer_provider = None
        self._tracer = None
        self._init_opentelemetry()
        import atexit
        atexit.register(self.shutdown)

        # Policy evaluator - set based on backend response
        self.evaluator: PolicyEvaluator | None = None
        self.enforce = False  # Will be set to True if policies exist

        # Validate API key and get configuration (including policies)
        self.backend = BackendClient(self.api_key, self.api_base_url)
        is_valid, sdk_config = self.backend.validate_api_key(agent_id=self.agent_id)
        
        if not is_valid:
            raise ConfigurationError(
                "API key validation failed. "
                "Check that your API key is correct and not expired. "
                "Get a new API key from https://app.cortexhub.ai"
            )
        
        self._sdk_config = sdk_config
        self._project_id = sdk_config.project_id

        # Initialize enforcement if backend returned policies
        if sdk_config.has_policies:
            self._init_enforcement_mode(sdk_config)
        else:
            logger.info(
                "No policies configured yet",
                project_id=self._project_id,
                next_step="Create policies in CortexHub dashboard to enable enforcement",
            )

        # Initialize guardrails with config from backend
        # The guardrail_config specifies:
        # - action: "redact" | "block" | "allow" (what to do when detected)
        # - pii_types/secret_types: which types to detect (None = all)
        # - custom_patterns: additional regex patterns
        pii_allowed_types = None
        secrets_allowed_types = None
        pii_custom_patterns = []
        secrets_custom_patterns = []
        
        # Store guardrail actions and scope for use during enforcement
        self._pii_guardrail_action: str | None = None  # "redact", "block", or "allow"
        self._secrets_guardrail_action: str | None = None
        self._pii_redaction_scope: str = "both"  # "input_only", "output_only", or "both"
        self._secrets_redaction_scope: str = "both"
        
        if self._sdk_config and self._sdk_config.policies.guardrail_configs:
            gc = self._sdk_config.policies.guardrail_configs
            
            if "pii" in gc:
                pii_config = gc["pii"]
                pii_allowed_types = pii_config.pii_types
                self._pii_guardrail_action = pii_config.action  # "redact", "block", or "allow"
                self._pii_redaction_scope = pii_config.redaction_scope or "both"
                if pii_config.custom_patterns:
                    from cortexhub.guardrails.pii import CustomPattern as PIICustomPattern
                    pii_custom_patterns = [
                        PIICustomPattern(
                            name=cp.name,
                            pattern=cp.pattern,
                            description=cp.description,
                            enabled=cp.enabled,
                        )
                        for cp in pii_config.custom_patterns
                    ]
                logger.info(
                    "PII guardrail configured from backend",
                    action=self._pii_guardrail_action,
                    redaction_scope=self._pii_redaction_scope,
                    allowed_types=pii_allowed_types,
                    custom_patterns=len(pii_custom_patterns),
                )
            
            if "secrets" in gc:
                secrets_config = gc["secrets"]
                secrets_allowed_types = secrets_config.secret_types
                self._secrets_guardrail_action = secrets_config.action
                self._secrets_redaction_scope = secrets_config.redaction_scope or "both"
                # Note: secrets detector doesn't have custom patterns yet
                logger.info(
                    "Secrets guardrail configured from backend",
                    action=self._secrets_guardrail_action,
                    redaction_scope=self._secrets_redaction_scope,
                    allowed_types=secrets_allowed_types,
                )
        
        self.pii_detector = PIIDetector(
            enabled=True,
            allowed_types=pii_allowed_types,
            custom_patterns=pii_custom_patterns if pii_custom_patterns else None,
        )
        self.secrets_detector = SecretsDetector(enabled=True)
        self.injection_detector = PromptManipulationDetector(enabled=True)

        # Initialize context enrichment
        self.agent_registry = AgentRegistry()
        self.context_enricher = ContextEnricher(self.agent_registry)

        # Initialize interceptors
        self.llm_interceptor = LLMInterceptor(self)
        self.mcp_interceptor = MCPInterceptor(self)

        mode_str = "enforcement" if self.enforce else "observation"
        privacy_str = "enabled (metadata only)" if self.privacy else "DISABLED (raw data sent)"
        logger.info(
            "CortexHub initialized",
            agent_id=self.agent_id,
            session_id=self.session_id,
            mode=mode_str,
            privacy=privacy_str,
            telemetry="OpenTelemetry (OTLP/HTTP)",
        )

    def _init_opentelemetry(self) -> None:
        """Initialize OpenTelemetry tracer and exporter."""
        # Create resource with agent metadata
        resource = OtelResource.create({
            "service.name": "cortexhub-sdk",
            "service.version": __version__,
            "cortexhub.agent.id": self.agent_id,
            "cortexhub.privacy.mode": "enabled" if self.privacy else "disabled",
        })

        # Create tracer provider
        self._tracer_provider = TracerProvider(resource=resource)

        # Configure OTLP exporter if we have API key
        if self.api_key and self.api_url:
            base_url = self.api_url.rstrip("/")
            exporter = OTLPSpanExporter(
                endpoint=f"{base_url}/v1/traces",
                headers={"X-API-Key": self.api_key},
            )

            # Add batch processor (handles batching, retry, backpressure)
            processor = BatchSpanProcessor(
                exporter,
                max_queue_size=2048,           # Max spans in queue
                max_export_batch_size=1,       # Export each span quickly
                schedule_delay_millis=250,     # Near real-time export
                export_timeout_millis=30000,   # 30 second timeout
            )
            self._tracer_provider.add_span_processor(processor)

        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)

        # Create tracer
        self._tracer = trace.get_tracer("cortexhub", __version__)

        logger.debug(
            "OpenTelemetry initialized",
            exporter="OTLP/HTTP" if self.api_key else "none",
            resource_attributes={
                "service.name": "cortexhub-sdk",
                "cortexhub.agent.id": self.agent_id,
                "cortexhub.privacy.mode": "enabled" if self.privacy else "disabled",
            },
        )

    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{timestamp}-{str(uuid.uuid4())[:8]}"

    def _normalize_api_url(self, url: str) -> str:
        base_url = url.rstrip("/")
        if base_url.endswith("/api/v1"):
            base_url = base_url[: -len("/api/v1")]
        if base_url.endswith("/v1"):
            base_url = base_url[: -len("/v1")]
        return base_url

    def _init_enforcement_mode(self, sdk_config) -> None:
        """Initialize enforcement mode with policies from backend."""
        from cortexhub.policy.loader import PolicyBundle
        from cortexhub.errors import PolicyLoadError
        
        # Create policy bundle from backend response
        policy_bundle = PolicyBundle(
            policies=sdk_config.policies.policies,
            schema=sdk_config.policies.schema or {},
            metadata={
                "version": sdk_config.policies.version,
                    "default_behavior": "allow_and_log",
                "policy_map": sdk_config.policies.policy_metadata or {},
            },
        )
        
        try:
            self.evaluator = PolicyEvaluator(policy_bundle)
            self.enforce = True
        except PolicyLoadError:
            self.enforce = False
            raise
        
        logger.info(
            "Enforcement mode (policies from backend)",
            project_id=self._project_id,
            policy_version=sdk_config.policies.version,
        )

    def _default_agent_id(self) -> str:
        """Generate a default agent ID based on hostname."""
        import socket
        hostname = socket.gethostname()
        return f"agent.{hostname}"

    # =========================================================================
    # REQUEST BUILDER - Structured, not flattened
    # =========================================================================

    def build_request(
        self,
        *,
        principal: Principal | dict[str, str] | None = None,
        action: Action | dict[str, str],
        resource: PolicyResource | dict[str, str],
        args: dict[str, Any],
        framework: str,
    ) -> AuthorizationRequest:
        """Build a properly structured AuthorizationRequest.
        
        This is the ONLY way to build requests. No flattening.
        
        Args:
            principal: Who is making the request (defaults to self.agent_id)
            action: What action is being performed
            resource: What resource is being accessed
            args: Arguments to the action
            framework: Framework name (langchain, openai_agents, etc.)
            
        Returns:
            Properly structured AuthorizationRequest
        """
        # Principal - use agent_id if not specified
        if principal is None:
            principal = Principal(type="Agent", id=self.agent_id)
        elif isinstance(principal, dict):
            principal = Principal(**principal)
        
        # Action
        if isinstance(action, dict):
            action = Action(**action)
        
        # Resource
        if isinstance(resource, dict):
            resource = PolicyResource(**resource)
        
        # Build context
        metadata = Metadata(session_id=self.session_id)
        runtime = RuntimeContext(framework=framework)
        
        context = {
            "args": args,
            "runtime": runtime.model_dump(),
            "metadata": metadata.model_dump(),
            "guardrails": {
                "pii_detected": False,
                "pii_types": [],
                "secrets_detected": False,
                "secrets_types": [],
                "prompt_manipulation": False,
            },
            "redaction": {"applied": False},
        }
        
        return AuthorizationRequest(
            principal=principal,
            action=action,
            resource=resource,
            context=context,
        )

    # =========================================================================
    # SINGLE ENTRYPOINT FOR ADAPTERS
    # =========================================================================

    def execute_governed_tool(
        self,
        *,
        tool_name: str,
        args: dict[str, Any],
        framework: str,
        call_original: Callable[[], Any],
        tool_description: str | None = None,
        parameters_schema: dict[str, Any] | None = None,
        principal: Principal | dict[str, str] | None = None,
        resource_type: str = "Tool",
    ) -> Any:
        """Execute a tool with full governance pipeline.

        This is the SINGLE entrypoint for all adapters.
        Adapters should not implement governance logic themselves.

        NOTE: Guardrails do NOT apply to tools - tools NEED sensitive data to work.
        Guardrails only apply to LLM calls where sensitive data should NOT flow.

        Pipeline:
        1. Build AuthorizationRequest (structured, not flattened)
        2. Create tool.invoke span with metadata
        3. Evaluate policy -> get Decision (enforcement mode only)
        4. Add policy decision to span if enforcement mode
        5. Branch on Decision (ALLOW/DENY/ESCALATE)
        6. Execute tool
        7. Record result on span and end span

        Args:
            tool_name: Name of the tool being invoked
            args: Arguments to the tool
            framework: Framework name (langchain, openai_agents, etc.)
            call_original: Callable that executes the original tool
            tool_description: Human-readable description of what the tool does
            principal: Optional principal override
            resource_type: Type of resource (default: "Tool")

        Returns:
            Result of tool execution

        Raises:
            PolicyViolationError: If policy denies
            ApprovalDeniedError: If approval denied
        """
        expected_types = self._extract_expected_arg_types(parameters_schema)

        expected_types = self._extract_expected_arg_types(parameters_schema)

        # Step 1: Build request (structured, NOT flattened)
        policy_args = self._sanitize_policy_args(args)
        request = self.build_request(
            principal=principal,
            action={"type": "tool.invoke", "name": tool_name},
            resource=PolicyResource(type=resource_type, id=tool_name),
            args=policy_args,
            framework=framework,
        )

        # Step 2: Extract arg names only (not values, not classifications)
        arg_names = list(policy_args.keys()) if isinstance(policy_args, dict) else []

        # Step 3: Create tool.invoke span
        with self._tracer.start_as_current_span(
            name="tool.invoke",
            kind=trace.SpanKind.INTERNAL,
        ) as span:
            # Set standard attributes
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", self.agent_id)
            span.set_attribute("cortexhub.tool.name", tool_name)
            span.set_attribute("cortexhub.tool.framework", framework)

            if tool_description:
                span.set_attribute("cortexhub.tool.description", tool_description)

            if arg_names:
                span.set_attribute("cortexhub.tool.arg_names", arg_names)

            if isinstance(policy_args, dict) and policy_args:
                arg_schema = self._infer_arg_schema(policy_args)
                if arg_schema:
                    span.set_attribute("cortexhub.tool.arg_schema", json.dumps(arg_schema))

            # Raw data only if privacy disabled
            if not self.privacy and args:
                span.set_attribute("cortexhub.raw.args", json.dumps(args, default=str))

            try:
                if expected_types and self.enforce and self.evaluator:
                    mismatches = self._validate_arg_types(args, expected_types)
                    if mismatches:
                        message = f"Tool argument type mismatch: {'; '.join(mismatches)}"
                        span.add_event(
                            "policy.decision",
                            attributes={
                                "decision.effect": "deny",
                                "decision.policy_id": "",
                                "decision.reasoning": message,
                                "decision.policy_name": "type_mismatch",
                            },
                        )
                        span.set_status(Status(StatusCode.ERROR, message))
                        raise PolicyViolationError(message, reasoning=message)
                # Step 4: Policy evaluation (enforcement mode only)
                if self.enforce and self.evaluator:
                    if os.getenv("CORTEXHUB_DEBUG_POLICY", "").lower() in ("1", "true", "yes"):
                        logger.info(
                            "Policy evaluation request",
                            tool=tool_name,
                            args=self._summarize_policy_args(policy_args),
                            privacy=self.privacy,
                        )
                    # ENFORCEMENT MODE: Evaluate policies
                    decision = self.evaluator.evaluate(request)

                    # Add policy decision event to span
                    span.add_event(
                        "policy.decision",
                        attributes={
                            "decision.effect": decision.effect.value,
                            "decision.policy_id": decision.policy_id or "",
                            "decision.reasoning": decision.reasoning,
                            "decision.policy_name": decision.policy_name or "",
                        }
                    )

                    # Branch on Decision
                    if decision.effect == Effect.DENY:
                        span.set_status(Status(StatusCode.ERROR, decision.reasoning))
                        policy_label = decision.reasoning
                        if decision.policy_id:
                            name_segment = (
                                f"{decision.policy_name}" if decision.policy_name else "Unknown policy"
                            )
                            policy_label = f"{decision.reasoning} (Policy: {name_segment}, ID: {decision.policy_id})"
                        raise PolicyViolationError(
                            policy_label,
                            policy_id=decision.policy_id,
                            reasoning=decision.reasoning,
                        )

                    if decision.effect == Effect.ESCALATE:
                        context_hash = self._compute_context_hash(tool_name, policy_args)
                        try:
                            approval_response = self.backend.create_approval(
                                run_id=self.session_id,
                                trace_id=self._get_current_trace_id(),
                                tool_name=tool_name,
                                tool_args_values=args if not self.privacy else None,
                                context_hash=context_hash,
                                policy_id=decision.policy_id or "",
                                policy_name=decision.policy_name or "Unknown Policy",
                                policy_explanation=decision.reasoning,
                                risk_category=self._infer_risk_category(decision, tool_name),
                                agent_id=self.agent_id,
                                framework=framework,
                                environment=os.getenv("CORTEXHUB_ENVIRONMENT"),
                            )
                        except Exception as e:
                            logger.error("Failed to create approval", error=str(e))
                            raise PolicyViolationError(
                                f"Tool '{tool_name}' requires approval but failed to create approval record: {e}",
                                policy_id=decision.policy_id,
                                reasoning=decision.reasoning,
                            )

                        span.add_event(
                            "approval.created",
                            attributes={
                                "approval_id": approval_response.get("approval_id", ""),
                                "tool_name": tool_name,
                                "policy_id": decision.policy_id or "",
                                "expires_at": approval_response.get("expires_at", ""),
                            },
                        )
                        span.set_status(Status(StatusCode.ERROR, "Approval required"))

                        raise ApprovalRequiredError(
                            f"Tool '{tool_name}' requires approval: {decision.reasoning}",
                            approval_id=approval_response.get("approval_id", ""),
                            run_id=self.session_id,
                            tool_name=tool_name,
                            policy_id=decision.policy_id,
                            policy_name=decision.policy_name,
                            reason=decision.reasoning,
                            expires_at=approval_response.get("expires_at"),
                            decision_endpoint=approval_response.get("decision_endpoint"),
                        )
                # else: OBSERVATION MODE - no policy evaluation
                # Just observe the tool invocation

                # Step 5: Execute tool
                exec_start = time.perf_counter()
                result = call_original()
                exec_latency_ms = (time.perf_counter() - exec_start) * 1000

                # Step 6: Record success result on span
                span.set_attribute("cortexhub.result.success", True)
                span.set_status(Status(StatusCode.OK))

                # Raw result only if privacy disabled
                if not self.privacy and result is not None:
                    span.set_attribute("cortexhub.raw.result", json.dumps(result, default=str))

                return result

            except (PolicyViolationError, ApprovalRequiredError, ApprovalDeniedError):
                # These are expected governance failures - re-raise
                raise
            except Exception as e:
                # Unexpected error during execution
                span.set_attribute("cortexhub.result.success", False)
                span.set_attribute("cortexhub.error.message", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    async def execute_governed_tool_async(
        self,
        *,
        tool_name: str,
        args: dict[str, Any],
        framework: str,
        call_original: Callable[[], Any],
        tool_description: str | None = None,
        parameters_schema: dict[str, Any] | None = None,
        principal: Principal | dict[str, str] | None = None,
        resource_type: str = "Tool",
    ) -> Any:
        """Async version of execute_governed_tool.
        
        Same pipeline as sync version, but awaits the tool execution.
        NOTE: Guardrails do NOT apply to tools - tools NEED sensitive data.
        """
        # Step 1: Build request
        policy_args = self._sanitize_policy_args(args)
        request = self.build_request(
            principal=principal,
            action={"type": "tool.invoke", "name": tool_name},
            resource=PolicyResource(type=resource_type, id=tool_name),
            args=policy_args,
            framework=framework,
        )
        
        # Step 2: Extract arg names only (not values, not classifications)
        arg_names = list(policy_args.keys()) if isinstance(policy_args, dict) else []

        # Step 3: Create tool.invoke span
        with self._tracer.start_as_current_span(
            name="tool.invoke",
            kind=trace.SpanKind.INTERNAL,
        ) as span:
            # Set standard attributes
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", self.agent_id)
            span.set_attribute("cortexhub.tool.name", tool_name)
            span.set_attribute("cortexhub.tool.framework", framework)

            if tool_description:
                span.set_attribute("cortexhub.tool.description", tool_description)

            if arg_names:
                span.set_attribute("cortexhub.tool.arg_names", arg_names)

            if isinstance(policy_args, dict) and policy_args:
                arg_schema = self._infer_arg_schema(policy_args)
                if arg_schema:
                    span.set_attribute("cortexhub.tool.arg_schema", json.dumps(arg_schema))

            # Raw data only if privacy disabled
            if not self.privacy and args:
                span.set_attribute("cortexhub.raw.args", json.dumps(args, default=str))

            try:
                if expected_types and self.enforce and self.evaluator:
                    mismatches = self._validate_arg_types(args, expected_types)
                    if mismatches:
                        message = f"Tool argument type mismatch: {'; '.join(mismatches)}"
                        span.add_event(
                            "policy.decision",
                            attributes={
                                "decision.effect": "deny",
                                "decision.policy_id": "",
                                "decision.reasoning": message,
                                "decision.policy_name": "type_mismatch",
                            },
                        )
                        span.set_status(Status(StatusCode.ERROR, message))
                        raise PolicyViolationError(message, reasoning=message)
                # Step 4: Policy evaluation (enforcement mode only)
                if self.enforce and self.evaluator:
                    decision = self.evaluator.evaluate(request)

                    # Add policy decision event to span
                    span.add_event(
                        "policy.decision",
                        attributes={
                            "decision.effect": decision.effect.value,
                            "decision.policy_id": decision.policy_id or "",
                            "decision.reasoning": decision.reasoning,
                            "decision.policy_name": decision.policy_name or "",
                        },
                    )

                    if decision.effect == Effect.DENY:
                        span.set_status(Status(StatusCode.ERROR, decision.reasoning))
                        policy_label = decision.reasoning
                        if decision.policy_id:
                            name_segment = (
                                f"{decision.policy_name}" if decision.policy_name else "Unknown policy"
                            )
                            policy_label = f"{decision.reasoning} (Policy: {name_segment}, ID: {decision.policy_id})"
                        raise PolicyViolationError(
                            policy_label,
                            policy_id=decision.policy_id,
                            reasoning=decision.reasoning,
                        )

                    if decision.effect == Effect.ESCALATE:
                        context_hash = self._compute_context_hash(tool_name, policy_args)
                        try:
                            approval_response = self.backend.create_approval(
                                run_id=self.session_id,
                                trace_id=self._get_current_trace_id(),
                                tool_name=tool_name,
                                tool_args_values=args if not self.privacy else None,
                                context_hash=context_hash,
                                policy_id=decision.policy_id or "",
                                policy_name=decision.policy_name or "Unknown Policy",
                                policy_explanation=decision.reasoning,
                                risk_category=self._infer_risk_category(decision, tool_name),
                                agent_id=self.agent_id,
                                framework=framework,
                                environment=os.getenv("CORTEXHUB_ENVIRONMENT"),
                            )
                        except Exception as e:
                            logger.error("Failed to create approval", error=str(e))
                            raise PolicyViolationError(
                                f"Tool '{tool_name}' requires approval but failed to create approval record: {e}",
                                policy_id=decision.policy_id,
                                reasoning=decision.reasoning,
                            )

                        span.add_event(
                            "approval.created",
                            attributes={
                                "approval_id": approval_response.get("approval_id", ""),
                                "tool_name": tool_name,
                                "policy_id": decision.policy_id or "",
                                "expires_at": approval_response.get("expires_at", ""),
                            },
                        )
                        span.set_status(Status(StatusCode.ERROR, "Approval required"))

                        raise ApprovalRequiredError(
                            f"Tool '{tool_name}' requires approval: {decision.reasoning}",
                            approval_id=approval_response.get("approval_id", ""),
                            run_id=self.session_id,
                            tool_name=tool_name,
                            policy_id=decision.policy_id,
                            policy_name=decision.policy_name,
                            reason=decision.reasoning,
                            expires_at=approval_response.get("expires_at"),
                            decision_endpoint=approval_response.get("decision_endpoint"),
                        )

                # Step 5: Execute tool (async)
                exec_start = time.perf_counter()
                result = await call_original()
                exec_latency_ms = (time.perf_counter() - exec_start) * 1000

                # Step 6: Record success result on span
                span.set_attribute("cortexhub.result.success", True)
                span.set_status(Status(StatusCode.OK))
                span.set_attribute("cortexhub.result.latency_ms", exec_latency_ms)

                if not self.privacy and result is not None:
                    span.set_attribute("cortexhub.raw.result", json.dumps(result, default=str))

                return result

            except (PolicyViolationError, ApprovalRequiredError, ApprovalDeniedError):
                raise
            except Exception as e:
                span.set_attribute("cortexhub.result.success", False)
                span.set_attribute("cortexhub.error.message", str(e))
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    def execute_governed_llm_call(
        self,
        *,
        model: str,
        prompt: Any,
        framework: str,
        call_original: Callable[[Any], Any],
    ) -> Any:
        """Execute an LLM call with governance enforcement and guardrails."""
        guardrail_findings = LLMGuardrailFindings()
        prompt_text = self._extract_llm_prompt_text(prompt)

        if prompt_text:
            # Use detect() for better summary statistics
            pii_result = self.pii_detector.detect({"prompt": prompt_text})
            if pii_result.detected:
                guardrail_findings.pii_in_prompt = {
                    "detected": True,
                    "count": pii_result.count,  # Total occurrences
                    "unique_count": pii_result.unique_count,  # Unique values
                    "types": pii_result.types,
                    "counts_per_type": pii_result.counts_per_type,
                    "unique_per_type": pii_result.unique_values_per_type,
                    "summary": pii_result.summary,  # Human-readable: "2 SSN, 3 EMAIL"
                    "findings": [
                        {"type": f.get("type"), "score": f.get("confidence", 0.0)}
                        for f in pii_result.findings[:10]
                    ],
                }

            secrets_result = self.secrets_detector.detect({"prompt": prompt_text})
            if secrets_result.detected:
                guardrail_findings.secrets_in_prompt = {
                    "detected": True,
                    "count": secrets_result.count,
                    "types": secrets_result.types,
                    "counts_per_type": secrets_result.counts_per_type,
                    "findings": [{"type": f.get("type")} for f in secrets_result.findings[:10]],
                }

            injection_result = self.injection_detector.detect({"prompt": prompt_text})
            if injection_result.detected:
                guardrail_findings.prompt_manipulation = {
                    "detected": True,
                    "count": injection_result.count,
                    "patterns": injection_result.patterns,
                    "findings": injection_result.findings[:10],
                }

        decision = None
        redaction_applied = False
        redaction_summary: dict[str, Any] | None = None
        prompt_to_send = prompt

        if self.enforce and self.evaluator:
            guardrails_context = {
                "pii_detected": guardrail_findings.pii_in_prompt.get("detected", False),
                "pii_types": guardrail_findings.pii_in_prompt.get("types", []),
                "secrets_detected": guardrail_findings.secrets_in_prompt.get("detected", False),
                "secrets_types": guardrail_findings.secrets_in_prompt.get("types", []),
                "prompt_manipulation": guardrail_findings.prompt_manipulation.get("detected", False),
            }
            request = self.build_request(
                action={"type": "llm.call", "name": model},
                resource=PolicyResource(type="LLM", id=model),
                args={"model": model},
                framework=framework,
            ).with_enriched_context(
                guardrails=guardrails_context,
                redaction={"applied": False},
            )
            decision = self.evaluator.evaluate(request)

            # If DENY and PII/secrets detected, attempt redaction based on guardrail action and scope
            if decision.effect == Effect.DENY and (
                guardrails_context["pii_detected"] or guardrails_context["secrets_detected"]
            ):
                # Check if guardrail action allows redaction (vs hard block) for INPUT
                pii_wants_redact_input = (
                    guardrails_context["pii_detected"] and 
                    self._pii_guardrail_action == "redact" and
                    self._pii_redaction_scope in ("both", "input_only")
                )
                secrets_wants_redact_input = (
                    guardrails_context["secrets_detected"] and 
                    self._secrets_guardrail_action == "redact" and
                    self._secrets_redaction_scope in ("both", "input_only")
                )
                should_attempt_redaction = pii_wants_redact_input or secrets_wants_redact_input
                
                if should_attempt_redaction:
                    redacted_prompt, redaction_summary = self.redact_llm_prompt_for_enforcement(
                        prompt
                    )
                    if redaction_summary.get("applied"):
                        redaction_applied = True
                        prompt_to_send = redacted_prompt
                        request = request.with_enriched_context(
                            guardrails=guardrails_context,
                            redaction={"applied": True},
                        )
                        # Re-evaluate with redacted content
                        re_evaluated = self.evaluator.evaluate(request)
                        # If now allowed, mark as REDACT (sensitive data was removed before LLM call)
                        if re_evaluated.effect == Effect.ALLOW:
                            decision = Decision.redact(
                                reasoning=f"PII/secrets redacted before LLM call. Original: {decision.reasoning}",
                                policy_id=decision.policy_id,
                                policy_name=decision.policy_name,
                            )
                        else:
                            decision = re_evaluated

            if decision.effect == Effect.DENY:
                policy_label = decision.reasoning
                if decision.policy_id:
                    name_segment = (
                        f"{decision.policy_name}" if decision.policy_name else "Unknown policy"
                    )
                    policy_label = (
                        f"{decision.reasoning} (Policy: {name_segment}, ID: {decision.policy_id})"
                    )
                raise PolicyViolationError(
                    policy_label,
                    policy_id=decision.policy_id,
                    reasoning=decision.reasoning,
                )

            if decision.effect == Effect.ESCALATE:
                llm_args = {"model": model}
                context_hash = self._compute_context_hash("llm.call", llm_args)
                try:
                    approval_response = self.backend.create_approval(
                        run_id=self.session_id,
                        trace_id=self._get_current_trace_id(),
                        tool_name="llm.call",
                        tool_args_values=llm_args if not self.privacy else None,
                        context_hash=context_hash,
                        policy_id=decision.policy_id or "",
                        policy_name=decision.policy_name or "Unknown Policy",
                        policy_explanation=decision.reasoning,
                        risk_category=self._infer_risk_category(decision, "llm.call"),
                        agent_id=self.agent_id,
                        framework=framework,
                        environment=os.getenv("CORTEXHUB_ENVIRONMENT"),
                    )
                except Exception as e:
                    logger.error("Failed to create approval", error=str(e))
                    raise PolicyViolationError(
                        f"LLM call to '{model}' requires approval but failed to create approval record: {e}",
                        policy_id=decision.policy_id,
                        reasoning=decision.reasoning,
                    )

                raise ApprovalRequiredError(
                    f"LLM call to '{model}' requires approval: {decision.reasoning}",
                    approval_id=approval_response.get("approval_id", ""),
                    run_id=self.session_id,
                    tool_name="llm.call",
                    policy_id=decision.policy_id,
                    policy_name=decision.policy_name,
                    reason=decision.reasoning,
                    expires_at=approval_response.get("expires_at"),
                    decision_endpoint=approval_response.get("decision_endpoint"),
                )

        response = call_original(prompt_to_send)
        response_text = self._extract_llm_response_text(response)
        response_redaction_applied = False
        response_redaction_summary: dict[str, Any] | None = None
        
        if response_text:
            pii_result = self.pii_detector.detect({"response": response_text})
            if pii_result.detected:
                guardrail_findings.pii_in_response = {
                    "detected": True,
                    "count": pii_result.count,
                    "unique_count": pii_result.unique_count,
                    "types": pii_result.types,
                    "counts_per_type": pii_result.counts_per_type,
                    "unique_per_type": pii_result.unique_values_per_type,
                    "summary": pii_result.summary,
                    "findings": [
                        {"type": f.get("type"), "score": f.get("confidence", 0.0)}
                        for f in pii_result.findings[:10]
                    ],
                }
                
                # Redact response if scope includes output
                pii_wants_redact_output = (
                    self._pii_guardrail_action == "redact" and
                    self._pii_redaction_scope in ("both", "output_only")
                )
                if pii_wants_redact_output:
                    response, response_redaction_summary = self._redact_llm_response(response)
                    if response_redaction_summary and response_redaction_summary.get("applied"):
                        response_redaction_applied = True
                        response_text = self._extract_llm_response_text(response)
        
        # Merge redaction summaries for logging
        final_redaction_summary = redaction_summary
        if response_redaction_applied and response_redaction_summary:
            if final_redaction_summary:
                final_redaction_summary = {
                    **final_redaction_summary,
                    "response_redacted": True,
                    "response_pii_types": response_redaction_summary.get("pii_types", []),
                }
            else:
                final_redaction_summary = {
                    "applied": True,
                    "response_redacted": True,
                    "response_pii_types": response_redaction_summary.get("pii_types", []),
                }

        self.log_llm_call(
            trace_id=str(uuid.uuid4()),
            model=model,
            prompt=prompt_to_send,
            response=response_text,
            guardrail_findings=guardrail_findings,
            agent_id=self.agent_id,
            decision=decision,
            redaction_applied=redaction_applied or response_redaction_applied,
            redaction_summary=final_redaction_summary,
        )

        return response

    async def execute_governed_llm_call_async(
        self,
        *,
        model: str,
        prompt: Any,
        framework: str,
        call_original: Callable[[Any], Any],
    ) -> Any:
        """Async LLM governance wrapper."""
        guardrail_findings = LLMGuardrailFindings()
        prompt_text = self._extract_llm_prompt_text(prompt)

        if prompt_text:
            # Use detect() for better summary statistics
            pii_result = self.pii_detector.detect({"prompt": prompt_text})
            if pii_result.detected:
                guardrail_findings.pii_in_prompt = {
                    "detected": True,
                    "count": pii_result.count,
                    "unique_count": pii_result.unique_count,
                    "types": pii_result.types,
                    "counts_per_type": pii_result.counts_per_type,
                    "unique_per_type": pii_result.unique_values_per_type,
                    "summary": pii_result.summary,
                    "findings": [
                        {"type": f.get("type"), "score": f.get("confidence", 0.0)}
                        for f in pii_result.findings[:10]
                    ],
                }

            secrets_result = self.secrets_detector.detect({"prompt": prompt_text})
            if secrets_result.detected:
                guardrail_findings.secrets_in_prompt = {
                    "detected": True,
                    "count": secrets_result.count,
                    "types": secrets_result.types,
                    "counts_per_type": secrets_result.counts_per_type,
                    "findings": [{"type": f.get("type")} for f in secrets_result.findings[:10]],
                }

            injection_result = self.injection_detector.detect({"prompt": prompt_text})
            if injection_result.detected:
                guardrail_findings.prompt_manipulation = {
                    "detected": True,
                    "count": injection_result.count,
                    "patterns": injection_result.patterns,
                    "findings": injection_result.findings[:10],
                }

        decision = None
        redaction_applied = False
        redaction_summary: dict[str, Any] | None = None
        prompt_to_send = prompt

        if self.enforce and self.evaluator:
            guardrails_context = {
                "pii_detected": guardrail_findings.pii_in_prompt.get("detected", False),
                "pii_types": guardrail_findings.pii_in_prompt.get("types", []),
                "secrets_detected": guardrail_findings.secrets_in_prompt.get("detected", False),
                "secrets_types": guardrail_findings.secrets_in_prompt.get("types", []),
                "prompt_manipulation": guardrail_findings.prompt_manipulation.get("detected", False),
            }
            request = self.build_request(
                action={"type": "llm.call", "name": model},
                resource=PolicyResource(type="LLM", id=model),
                args={"model": model},
                framework=framework,
            ).with_enriched_context(
                guardrails=guardrails_context,
                redaction={"applied": False},
            )
            decision = self.evaluator.evaluate(request)

            # If DENY and PII/secrets detected, attempt redaction based on guardrail action and scope
            if decision.effect == Effect.DENY and (
                guardrails_context["pii_detected"] or guardrails_context["secrets_detected"]
            ):
                # Check if guardrail action allows redaction (vs hard block) for INPUT
                pii_wants_redact_input = (
                    guardrails_context["pii_detected"] and 
                    self._pii_guardrail_action == "redact" and
                    self._pii_redaction_scope in ("both", "input_only")
                )
                secrets_wants_redact_input = (
                    guardrails_context["secrets_detected"] and 
                    self._secrets_guardrail_action == "redact" and
                    self._secrets_redaction_scope in ("both", "input_only")
                )
                should_attempt_redaction = pii_wants_redact_input or secrets_wants_redact_input
                
                if should_attempt_redaction:
                    redacted_prompt, redaction_summary = self.redact_llm_prompt_for_enforcement(
                        prompt
                    )
                    if redaction_summary.get("applied"):
                        redaction_applied = True
                        prompt_to_send = redacted_prompt
                        request = request.with_enriched_context(
                            guardrails=guardrails_context,
                            redaction={"applied": True},
                        )
                        # Re-evaluate with redacted content (async version)
                        re_evaluated = self.evaluator.evaluate(request)
                        # If now allowed, mark as REDACT (sensitive data was removed before LLM call)
                        if re_evaluated.effect == Effect.ALLOW:
                            decision = Decision.redact(
                                reasoning=f"PII/secrets redacted before LLM call. Original: {decision.reasoning}",
                                policy_id=decision.policy_id,
                                policy_name=decision.policy_name,
                            )
                        else:
                            decision = re_evaluated

            if decision.effect == Effect.DENY:
                policy_label = decision.reasoning
                if decision.policy_id:
                    name_segment = (
                        f"{decision.policy_name}" if decision.policy_name else "Unknown policy"
                    )
                    policy_label = (
                        f"{decision.reasoning} (Policy: {name_segment}, ID: {decision.policy_id})"
                    )
                raise PolicyViolationError(
                    policy_label,
                    policy_id=decision.policy_id,
                    reasoning=decision.reasoning,
                )

            if decision.effect == Effect.ESCALATE:
                llm_args = {"model": model}
                context_hash = self._compute_context_hash("llm.call", llm_args)
                try:
                    approval_response = self.backend.create_approval(
                        run_id=self.session_id,
                        trace_id=self._get_current_trace_id(),
                        tool_name="llm.call",
                        tool_args_values=llm_args if not self.privacy else None,
                        context_hash=context_hash,
                        policy_id=decision.policy_id or "",
                        policy_name=decision.policy_name or "Unknown Policy",
                        policy_explanation=decision.reasoning,
                        risk_category=self._infer_risk_category(decision, "llm.call"),
                        agent_id=self.agent_id,
                        framework=framework,
                        environment=os.getenv("CORTEXHUB_ENVIRONMENT"),
                    )
                except Exception as e:
                    logger.error("Failed to create approval", error=str(e))
                    raise PolicyViolationError(
                        f"LLM call to '{model}' requires approval but failed to create approval record: {e}",
                        policy_id=decision.policy_id,
                        reasoning=decision.reasoning,
                    )

                raise ApprovalRequiredError(
                    f"LLM call to '{model}' requires approval: {decision.reasoning}",
                    approval_id=approval_response.get("approval_id", ""),
                    run_id=self.session_id,
                    tool_name="llm.call",
                    policy_id=decision.policy_id,
                    policy_name=decision.policy_name,
                    reason=decision.reasoning,
                    expires_at=approval_response.get("expires_at"),
                    decision_endpoint=approval_response.get("decision_endpoint"),
                )

        response = await call_original(prompt_to_send)
        response_text = self._extract_llm_response_text(response)
        response_redaction_applied = False
        response_redaction_summary: dict[str, Any] | None = None
        
        if response_text:
            pii_result = self.pii_detector.detect({"response": response_text})
            if pii_result.detected:
                guardrail_findings.pii_in_response = {
                    "detected": True,
                    "count": pii_result.count,
                    "unique_count": pii_result.unique_count,
                    "types": pii_result.types,
                    "counts_per_type": pii_result.counts_per_type,
                    "unique_per_type": pii_result.unique_values_per_type,
                    "summary": pii_result.summary,
                    "findings": [
                        {"type": f.get("type"), "score": f.get("confidence", 0.0)}
                        for f in pii_result.findings[:10]
                    ],
                }
                
                # Redact response if scope includes output
                pii_wants_redact_output = (
                    self._pii_guardrail_action == "redact" and
                    self._pii_redaction_scope in ("both", "output_only")
                )
                if pii_wants_redact_output:
                    response, response_redaction_summary = self._redact_llm_response(response)
                    if response_redaction_summary and response_redaction_summary.get("applied"):
                        response_redaction_applied = True
                        response_text = self._extract_llm_response_text(response)
        
        # Merge redaction summaries for logging
        final_redaction_summary = redaction_summary
        if response_redaction_applied and response_redaction_summary:
            if final_redaction_summary:
                final_redaction_summary = {
                    **final_redaction_summary,
                    "response_redacted": True,
                    "response_pii_types": response_redaction_summary.get("pii_types", []),
                }
            else:
                final_redaction_summary = {
                    "applied": True,
                    "response_redacted": True,
                    "response_pii_types": response_redaction_summary.get("pii_types", []),
                }

        self.log_llm_call(
            trace_id=str(uuid.uuid4()),
            model=model,
            prompt=prompt_to_send,
            response=response_text,
            guardrail_findings=guardrail_findings,
            agent_id=self.agent_id,
            decision=decision,
            redaction_applied=redaction_applied or response_redaction_applied,
            redaction_summary=final_redaction_summary,
        )

        return response

    # =========================================================================
    # SPAN CREATION METHODS
    # =========================================================================

    def trace_tool_call(
        self,
        tool_name: str,
        tool_description: str | None = None,
        arg_names: list[str] | None = None,
        args: dict[str, Any] | None = None,
    ) -> trace.Span:
        """Start a span for a tool call.

        Usage:
            with cortex.trace_tool_call("process_refund", args={"amount": 75}) as span:
                result = tool.invoke(args)
                span.set_attribute("cortexhub.result.success", True)
        """
        span = self._tracer.start_span(
            name="tool.invoke",
            kind=trace.SpanKind.INTERNAL,
        )

        # Set standard attributes
        span.set_attribute("cortexhub.session.id", self.session_id)
        span.set_attribute("cortexhub.agent.id", self.agent_id)
        span.set_attribute("cortexhub.tool.name", tool_name)

        if tool_description:
            span.set_attribute("cortexhub.tool.description", tool_description)

        if arg_names:
            span.set_attribute("cortexhub.tool.arg_names", arg_names)

        if args:
            arg_schema = self._infer_arg_schema(args)
            if arg_schema:
                span.set_attribute("cortexhub.tool.arg_schema", json.dumps(arg_schema))

        # Raw data only if privacy disabled
        if not self.privacy and args:
            span.set_attribute("cortexhub.raw.args", json.dumps(args, default=str))

        return span

    def _infer_arg_schema(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        """Infer argument schema types without sending values."""
        if not isinstance(args, dict):
            return []
        schema: list[dict[str, Any]] = []
        for name, value in args.items():
            schema.append(
                {
                    "name": name,
                    "type": self._infer_value_type(value),
                    "classification": "safe",
                    "is_redacted": False,
                }
            )
        return schema

    def _infer_value_type(self, value: Any) -> str:
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, str):
            return "string"
        return "unknown"

    def _extract_expected_arg_types(self, parameters_schema: dict[str, Any] | None) -> dict[str, str]:
        if not parameters_schema or not isinstance(parameters_schema, dict):
            return {}
        properties = parameters_schema.get("properties")
        if not isinstance(properties, dict):
            return {}
        expected: dict[str, str] = {}
        for name, schema in properties.items():
            if not isinstance(schema, dict):
                continue
            raw_type = schema.get("type")
            if isinstance(raw_type, list):
                raw_type = next((t for t in raw_type if t != "null"), None)
            if not isinstance(raw_type, str):
                continue
            normalized = raw_type.lower()
            if normalized == "integer":
                normalized = "number"
            if normalized in ("number", "string", "boolean"):
                expected[str(name)] = normalized
        return expected

    def _validate_arg_types(self, args: dict[str, Any], expected_types: dict[str, str]) -> list[str]:
        if not isinstance(args, dict):
            return []
        mismatches: list[str] = []
        for name, expected in expected_types.items():
            if name not in args:
                continue
            value = args.get(name)
            if value is None:
                continue
            if expected == "number":
                if not isinstance(value, int) or isinstance(value, bool):
                    mismatches.append(f"{name} expected number but got {type(value).__name__}")
            elif expected == "string":
                if not isinstance(value, str):
                    mismatches.append(f"{name} expected string but got {type(value).__name__}")
            elif expected == "boolean":
                if not isinstance(value, bool):
                    mismatches.append(f"{name} expected boolean but got {type(value).__name__}")
        return mismatches

    def trace_llm_call(
        self,
        model: str,
        prompt: str | None = None,
    ) -> trace.Span:
        """Start a span for an LLM call.

        Usage:
            with cortex.trace_llm_call("gpt-4o-mini", prompt=messages) as span:
                response = llm.invoke(messages)
                span.set_attribute("gen_ai.usage.completion_tokens", response.usage.completion_tokens)
        """
        span = self._tracer.start_span(
            name="llm.call",
            kind=trace.SpanKind.CLIENT,
        )

        # Set standard attributes (following gen_ai.* conventions)
        span.set_attribute("cortexhub.session.id", self.session_id)
        span.set_attribute("cortexhub.agent.id", self.agent_id)
        span.set_attribute("gen_ai.request.model", model)

        # Run guardrails on prompt
        if prompt:
            self._check_guardrails(span, prompt, "prompt")

            # Raw data only if privacy disabled
            if not self.privacy:
                span.set_attribute("cortexhub.raw.prompt", prompt)

        return span

    def _check_guardrails(
        self,
        span: trace.Span,
        content: str,
        content_type: str,  # "prompt" or "response"
    ) -> None:
        """Run guardrail checks and add span events for findings."""

        # PII detection
        pii_result = self.pii_detector.detect(content)
        if pii_result.detected:
            attributes = {
                "pii.detected": True,
                "pii.unique_count": pii_result.unique_count,  # Unique PII values (meaningful number)
                "pii.total_occurrences": pii_result.count,  # Total matches (for detailed analysis)
                "pii.types": pii_result.types,
                "pii.summary": pii_result.summary,  # Human-readable: "2 SSN, 3 EMAIL"
            }
            # Add counts per type for backend aggregation
            if pii_result.counts_per_type:
                attributes["pii.counts_per_type"] = json.dumps(pii_result.counts_per_type)
            if pii_result.unique_values_per_type:
                attributes["pii.unique_per_type"] = json.dumps(pii_result.unique_values_per_type)
            span.add_event(f"guardrail.pii_in_{content_type}", attributes=attributes)

        # Secrets detection
        secrets_result = self.secrets_detector.detect(content)
        if secrets_result.detected:
            attributes = {
                "secrets.detected": True,
                "secrets.count": secrets_result.count,
                "secrets.types": secrets_result.types,
            }
            # Add counts per type for backend aggregation
            if secrets_result.counts_per_type:
                attributes["secrets.counts_per_type"] = json.dumps(secrets_result.counts_per_type)
            span.add_event(f"guardrail.secrets_in_{content_type}", attributes=attributes)

        # Prompt manipulation detection (only for prompts)
        if content_type == "prompt":
            manipulation_result = self.injection_detector.detect(content)
            if manipulation_result.detected:
                span.add_event(
                    "guardrail.prompt_manipulation",
                    attributes={
                        "manipulation.detected": True,
                        "manipulation.patterns": manipulation_result.patterns,
                    }
                )

    def _serialize_raw_value(self, value: Any) -> str | None:
        """Serialize raw values for span attributes."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)

    def _redact_for_display(self, value: Any) -> Any:
        """Redact sensitive data for display without altering execution.

        This keeps object structure intact and only redacts string values,
        so tool arguments/outputs remain readable.
        """
        if value is None:
            return None
        if isinstance(value, str):
            redacted, _ = self.pii_detector.redact(value)
            redacted, _ = self.secrets_detector.redact(redacted)
            return redacted
        if isinstance(value, dict):
            return {key: self._redact_for_display(val) for key, val in value.items()}
        if isinstance(value, list):
            return [self._redact_for_display(item) for item in value]
        return value

    def _redact_llm_prompt_preview(self, prompt: Any) -> Any:
        """Redact LLM prompt for preview without touching tool arguments.

        - Redacts message content fields
        - Leaves tool call arguments unchanged
        """
        if prompt is None:
            return None
        if isinstance(prompt, list):
            return [self._redact_llm_prompt_preview(item) for item in prompt]
        if isinstance(prompt, dict):
            redacted: dict[str, Any] = {}
            for key, value in prompt.items():
                if key == "content":
                    redacted[key] = self._redact_for_display(value)
                    continue
                if key == "tool_calls" and isinstance(value, list):
                    redacted_calls = []
                    for call in value:
                        if not isinstance(call, dict):
                            redacted_calls.append(call)
                            continue
                        call_copy = dict(call)
                        function = call_copy.get("function")
                        if isinstance(function, dict):
                            function_copy = dict(function)
                            if "arguments" in function_copy:
                                function_copy["arguments"] = function_copy["arguments"]
                            call_copy["function"] = function_copy
                        redacted_calls.append(call_copy)
                    redacted[key] = redacted_calls
                    continue
                redacted[key] = self._redact_llm_prompt_preview(value)
            return redacted
        return self._redact_for_display(prompt)

    def redact_llm_prompt_for_enforcement(
        self,
        prompt: Any,
    ) -> Tuple[Any, dict[str, Any]]:
        """Redact PII and secrets from LLM prompt content.

        Only message content is redacted; tool call arguments remain untouched.
        """
        import copy

        summary = {
            "pii_redacted": False,
            "pii_types": [],
            "secrets_redacted": False,
            "secrets_types": [],
            "applied": False,
        }

        if isinstance(prompt, list):
            redacted_messages = copy.deepcopy(prompt)
            for message in redacted_messages:
                if isinstance(message, dict):
                    content = message.get("content")
                    if not isinstance(content, str) or not content:
                        continue
                elif hasattr(message, "content") and isinstance(message.content, str):
                    content = message.content
                else:
                    continue

                content_after = content
                secrets_redacted, secret_findings = self.secrets_detector.redact(content_after)
                if secret_findings:
                    summary["secrets_redacted"] = True
                    summary["secrets_types"].extend(
                        list({f.get("type", "unknown") for f in secret_findings})
                    )
                    if isinstance(secrets_redacted, str):
                        content_after = secrets_redacted

                pii_redacted, pii_findings = self.pii_detector.redact(content_after)
                if pii_findings:
                    summary["pii_redacted"] = True
                    summary["pii_types"].extend(
                        list({f.get("type", "unknown") for f in pii_findings})
                    )
                    if isinstance(pii_redacted, str):
                        content_after = pii_redacted

                if content_after != content:
                    if isinstance(message, dict):
                        message["content"] = content_after
                    else:
                        message.content = content_after
                    summary["applied"] = True

            summary["pii_types"] = list(set(summary["pii_types"]))
            summary["secrets_types"] = list(set(summary["secrets_types"]))
            return redacted_messages, summary

        if isinstance(prompt, str):
            content_after = prompt
            secrets_redacted, secret_findings = self.secrets_detector.redact(content_after)
            if secret_findings:
                summary["secrets_redacted"] = True
                summary["secrets_types"] = list({f.get("type", "unknown") for f in secret_findings})
                if isinstance(secrets_redacted, str):
                    content_after = secrets_redacted

            pii_redacted, pii_findings = self.pii_detector.redact(content_after)
            if pii_findings:
                summary["pii_redacted"] = True
                summary["pii_types"] = list({f.get("type", "unknown") for f in pii_findings})
                if isinstance(pii_redacted, str):
                    content_after = pii_redacted

            summary["applied"] = content_after != prompt
            return content_after, summary

        return prompt, summary

    def _redact_llm_response(
        self,
        response: Any,
    ) -> Tuple[Any, dict[str, Any]]:
        """Redact PII and secrets from LLM response content.
        
        Modifies the response in place to redact sensitive data before
        passing to downstream systems.
        """
        import copy

        summary = {
            "pii_redacted": False,
            "pii_types": [],
            "secrets_redacted": False,
            "secrets_types": [],
            "applied": False,
        }

        # Handle string response
        if isinstance(response, str):
            content_after = response
            secrets_redacted, secret_findings = self.secrets_detector.redact(content_after)
            if secret_findings:
                summary["secrets_redacted"] = True
                summary["secrets_types"] = list({f.get("type", "unknown") for f in secret_findings})
                if isinstance(secrets_redacted, str):
                    content_after = secrets_redacted

            pii_redacted, pii_findings = self.pii_detector.redact(content_after)
            if pii_findings:
                summary["pii_redacted"] = True
                summary["pii_types"] = list({f.get("type", "unknown") for f in pii_findings})
                if isinstance(pii_redacted, str):
                    content_after = pii_redacted

            summary["applied"] = content_after != response
            return content_after, summary

        # Handle dict response (common format: {"content": "...", "role": "assistant"})
        if isinstance(response, dict):
            redacted = copy.deepcopy(response)
            content = redacted.get("content")
            if isinstance(content, str):
                content_after = content
                secrets_redacted, secret_findings = self.secrets_detector.redact(content_after)
                if secret_findings:
                    summary["secrets_redacted"] = True
                    summary["secrets_types"].extend(
                        list({f.get("type", "unknown") for f in secret_findings})
                    )
                    if isinstance(secrets_redacted, str):
                        content_after = secrets_redacted

                pii_redacted, pii_findings = self.pii_detector.redact(content_after)
                if pii_findings:
                    summary["pii_redacted"] = True
                    summary["pii_types"].extend(
                        list({f.get("type", "unknown") for f in pii_findings})
                    )
                    if isinstance(pii_redacted, str):
                        content_after = pii_redacted

                if content_after != content:
                    redacted["content"] = content_after
                    summary["applied"] = True
            
            summary["pii_types"] = list(set(summary["pii_types"]))
            summary["secrets_types"] = list(set(summary["secrets_types"]))
            return redacted, summary

        # Handle object with content attribute (e.g., OpenAI response objects)
        if hasattr(response, "content") and isinstance(response.content, str):
            # For immutable response objects, we can't modify them directly
            # Return the redacted text in a wrapper structure
            content = response.content
            content_after = content
            
            secrets_redacted, secret_findings = self.secrets_detector.redact(content_after)
            if secret_findings:
                summary["secrets_redacted"] = True
                summary["secrets_types"] = list({f.get("type", "unknown") for f in secret_findings})
                if isinstance(secrets_redacted, str):
                    content_after = secrets_redacted

            pii_redacted, pii_findings = self.pii_detector.redact(content_after)
            if pii_findings:
                summary["pii_redacted"] = True
                summary["pii_types"] = list({f.get("type", "unknown") for f in pii_findings})
                if isinstance(pii_redacted, str):
                    content_after = pii_redacted

            if content_after != content:
                summary["applied"] = True
                # Try to modify the object if possible, otherwise return modified dict
                try:
                    response.content = content_after
                    return response, summary
                except (AttributeError, TypeError):
                    # Object is immutable, return dict representation
                    return {"content": content_after, "_original_type": type(response).__name__}, summary

        return response, summary

    def _extract_llm_prompt_text(self, prompt: Any) -> str | None:
        """Extract a text view of the LLM prompt for scanning."""
        if prompt is None:
            return None
        if isinstance(prompt, str):
            return prompt
        if isinstance(prompt, dict):
            content = prompt.get("content")
            return content if isinstance(content, str) else None
        if isinstance(prompt, list):
            parts = []
            for item in prompt:
                if isinstance(item, dict) and isinstance(item.get("content"), str):
                    parts.append(item["content"])
                elif hasattr(item, "content") and isinstance(item.content, str):
                    parts.append(item.content)
                elif isinstance(item, str):
                    parts.append(item)
            return " ".join(parts) if parts else None
        return None

    def _extract_llm_response_text(self, response: Any) -> str | None:
        """Extract a text view of the LLM response for scanning."""
        if response is None:
            return None
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            content = response.get("content")
            return content if isinstance(content, str) else None
        if hasattr(response, "content") and isinstance(response.content, str):
            return response.content
        if hasattr(response, "choices"):
            try:
                choice = response.choices[0]
                message = getattr(choice, "message", None)
                if message and hasattr(message, "content") and isinstance(message.content, str):
                    return message.content
            except Exception:
                return None
        if isinstance(response, list):
            parts = []
            for item in response:
                if hasattr(item, "content") and isinstance(item.content, str):
                    parts.append(item.content)
                elif isinstance(item, str):
                    parts.append(item)
            return " ".join(parts) if parts else None
        return None

    def record_tool_result(
        self,
        span: trace.Span,
        success: bool,
        result: Any = None,
        error: str | None = None,
    ) -> None:
        """Record the result of a tool call."""
        span.set_attribute("cortexhub.result.success", success)

        if success:
            span.set_status(Status(StatusCode.OK))
            if not self.privacy and result is not None:
                span.set_attribute("cortexhub.raw.result", json.dumps(result, default=str))
        else:
            span.set_status(Status(StatusCode.ERROR, error or "Unknown error"))
            if error:
                span.set_attribute("cortexhub.error.message", error)

    def record_llm_result(
        self,
        span: trace.Span,
        response: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        """Record the result of an LLM call."""
        span.set_status(Status(StatusCode.OK))

        if prompt_tokens is not None:
            span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
        if completion_tokens is not None:
            span.set_attribute("gen_ai.usage.completion_tokens", completion_tokens)

        # Run guardrails on response
        if response:
            self._check_guardrails(span, response, "response")

            if not self.privacy:
                span.set_attribute("cortexhub.raw.response", response)

    def _compute_context_hash(self, tool_name: str, args: dict[str, Any]) -> str:
        """Compute stable hash for idempotency."""

        import hashlib

        key = f"{tool_name}:{json.dumps(args, sort_keys=True, default=str)}"
        return f"sha256:{hashlib.sha256(key.encode()).hexdigest()}"

    def _sanitize_policy_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Coerce args into Cedar-safe JSON primitives for evaluation."""

        def coerce_value(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                from decimal import Decimal

                dec = Decimal(str(value))
                if dec == dec.to_integral_value():
                    return int(dec)
                return str(dec)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                cleaned: dict[str, Any] = {}
                for key, val in value.items():
                    coerced = coerce_value(val)
                    if coerced is not None:
                        cleaned[key] = coerced
                return cleaned
            if isinstance(value, (list, tuple, set)):
                cleaned_list = [coerce_value(item) for item in value]
                return [item for item in cleaned_list if item is not None]
            try:
                return json.loads(json.dumps(value, default=str))
            except Exception:
                return str(value)

        if not isinstance(args, dict):
            return {}

        cleaned_args = coerce_value(args)
        if not isinstance(cleaned_args, dict):
            return {}

        return cleaned_args

    def _summarize_policy_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Summarize args for debug logging without leaking sensitive values."""

        def summarize(value: Any) -> Any:
            if isinstance(value, dict):
                return {key: summarize(val) for key, val in value.items()}
            if isinstance(value, list):
                return [summarize(item) for item in value]
            return type(value).__name__

        if not isinstance(args, dict):
            return {}
        if self.privacy:
            return summarize(args)
        return args

    def _get_current_trace_id(self) -> str | None:
        """Get current OpenTelemetry trace ID."""

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, "032x")
        return None

    def _infer_risk_category(self, decision: Decision, tool_name: str) -> str | None:
        """Infer risk category from policy metadata."""

        return None

    def log_llm_call(
        self,
        *,
        trace_id: str,
        model: str,
        prompt: Any | None = None,
        response: Any | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        latency_ms: float = 0.0,
        cost_estimate: float | None = None,
        guardrail_findings: Any | None = None,  # Updated to Any for compatibility
        agent_id: str | None = None,
        decision: Decision | None = None,
        redaction_applied: bool = False,
        redaction_summary: dict[str, Any] | None = None,
    ) -> None:
        """Log an LLM call event with guardrail findings.

        THIS is where guardrails matter - sensitive data should NOT go to LLMs.
        Called by LLM interceptors after scanning prompts.

        NOTE: This method creates OpenTelemetry spans for auditability.
        """
        # Create LLM span
        with self._tracer.start_span(
            name="llm.call",
            kind=trace.SpanKind.CLIENT,
        ) as span:
            # Set standard attributes
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", agent_id or self.agent_id)
            span.set_attribute("gen_ai.request.model", model)

            raw_prompt = None
            raw_response = None
            if not self.privacy:
                raw_prompt = self._serialize_raw_value(prompt)
                raw_response = self._serialize_raw_value(response)
                if raw_prompt is not None:
                    span.set_attribute("cortexhub.raw.prompt", raw_prompt)
                if raw_response is not None:
                    span.set_attribute("cortexhub.raw.response", raw_response)

            if not self.privacy:
                redacted_prompt = self._serialize_raw_value(
                    self._redact_llm_prompt_preview(prompt)
                )
                redacted_response = self._serialize_raw_value(
                    self._redact_for_display(response)
                )

                if redacted_prompt and redacted_prompt != raw_prompt:
                    span.set_attribute("cortexhub.redacted.prompt", redacted_prompt)
                if redacted_response and redacted_response != raw_response:
                    span.set_attribute("cortexhub.redacted.response", redacted_response)

            if prompt_tokens is not None:
                span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
            if completion_tokens is not None:
                span.set_attribute("gen_ai.usage.completion_tokens", completion_tokens)

            if decision is not None:
                span.add_event(
                    "policy.decision",
                    attributes={
                        "decision.effect": decision.effect.value,
                        "decision.policy_id": decision.policy_id or "",
                        "decision.reasoning": decision.reasoning,
                        "decision.policy_name": decision.policy_name or "",
                    },
                )

            if redaction_applied:
                span.set_attribute("cortexhub.redaction.applied", True)
            if redaction_summary:
                span.set_attribute(
                    "cortexhub.redaction.pii_applied", bool(redaction_summary.get("pii_redacted"))
                )
                span.set_attribute(
                    "cortexhub.redaction.secrets_applied",
                    bool(redaction_summary.get("secrets_redacted")),
                )
                pii_types = redaction_summary.get("pii_types", [])
                secrets_types = redaction_summary.get("secrets_types", [])
                if pii_types:
                    span.set_attribute(
                        "cortexhub.redaction.pii_types",
                        json.dumps(pii_types),
                    )
                if secrets_types:
                    span.set_attribute(
                        "cortexhub.redaction.secrets_types",
                        json.dumps(secrets_types),
                    )

            # Add guardrail findings as span events
            if guardrail_findings:
                # Handle guardrail findings format
                if hasattr(guardrail_findings, 'pii_in_prompt') and guardrail_findings.pii_in_prompt.get("detected"):
                    pii_data = guardrail_findings.pii_in_prompt
                    unique_count = pii_data.get("unique_count", pii_data.get("count", 0))
                    total_count = pii_data.get("count", 0)
                    summary = pii_data.get("summary", f"{unique_count} PII items")
                    
                    pii_attrs = {
                        "pii.detected": True,
                        "pii.types": pii_data.get("types", []),
                        "pii.unique_count": unique_count,
                        "pii.total_occurrences": total_count,
                        "pii.summary": summary,
                    }
                    # Include counts_per_type if available
                    if pii_data.get("counts_per_type"):
                        pii_attrs["pii.counts_per_type"] = json.dumps(pii_data["counts_per_type"])
                    if pii_data.get("unique_per_type"):
                        pii_attrs["pii.unique_per_type"] = json.dumps(pii_data["unique_per_type"])
                    span.add_event("guardrail.pii_in_prompt", attributes=pii_attrs)
                    logger.warning(
                        "⚠️ PII detected in LLM prompt",
                        model=model,
                        summary=summary,
                        types=pii_data.get("types", []),
                    )

                if hasattr(guardrail_findings, 'secrets_in_prompt') and guardrail_findings.secrets_in_prompt.get("detected"):
                    secrets_attrs = {
                        "secrets.detected": True,
                        "secrets.types": guardrail_findings.secrets_in_prompt.get("types", []),
                        "secrets.count": guardrail_findings.secrets_in_prompt.get("count", 0),
                    }
                    # Include counts_per_type if available
                    if guardrail_findings.secrets_in_prompt.get("counts_per_type"):
                        secrets_attrs["secrets.counts_per_type"] = json.dumps(guardrail_findings.secrets_in_prompt["counts_per_type"])
                    span.add_event("guardrail.secrets_in_prompt", attributes=secrets_attrs)
                    logger.error(
                        "🚨 Secrets detected in LLM prompt",
                        model=model,
                        count=guardrail_findings.secrets_in_prompt.get("count", 0),
                    )

                if hasattr(guardrail_findings, 'prompt_manipulation') and guardrail_findings.prompt_manipulation.get("detected"):
                    span.add_event(
                        "guardrail.prompt_manipulation",
                        attributes={
                            "manipulation.detected": True,
                            "manipulation.patterns": guardrail_findings.prompt_manipulation.get("patterns", []),
                        }
                    )
                    logger.warning(
                        "⚠️ Prompt manipulation detected",
                        model=model,
                        patterns=guardrail_findings.prompt_manipulation.get("patterns", []),
                    )

    # =========================================================================
    # PUBLIC UTILITY METHODS
    # =========================================================================

    def export_telemetry(self) -> bool:
        """Flush any pending OpenTelemetry spans (non-blocking)."""
        if self._tracer_provider:
            # Force flush any pending spans
            try:
                self._tracer_provider.force_flush(timeout_millis=5000)
            except TypeError:
                self._tracer_provider.force_flush()
        return True

    @property
    def session_id(self) -> str:
        """Return the current session ID for this execution context."""
        return _session_id_var.get() or self._session_id

    def finish_run(
        self,
        *,
        framework: str | None = None,
        status: str = "completed",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a run completion span and flush telemetry."""
        depth = _run_depth.get()
        if depth > 0:
            _run_depth.set(depth - 1)
            if depth > 1:
                return

        normalized_status = "failed" if status == "failed" else "completed"
        span_name = "run.failed" if normalized_status == "failed" else "run.completed"

        with self._tracer.start_as_current_span(
            name=span_name,
            kind=trace.SpanKind.INTERNAL,
        ) as span:
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", self.agent_id)
            span.set_attribute("cortexhub.run.status", normalized_status)

            if framework:
                span.set_attribute("cortexhub.run.framework", framework)
            if metadata:
                span.set_attribute(
                    "cortexhub.run.metadata",
                    json.dumps(metadata, default=str),
                )

            if normalized_status == "failed":
                span.set_status(Status(StatusCode.ERROR, "Run failed"))
            else:
                span.set_status(Status(StatusCode.OK))

        self.export_telemetry()

    def start_run(
        self,
        *,
        framework: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a run started span."""
        depth = _run_depth.get()
        if depth == 0:
            _session_id_var.set(self._generate_session_id())
        _run_depth.set(depth + 1)
        if depth > 0:
            return

        with self._tracer.start_as_current_span(
            name="run.started",
            kind=trace.SpanKind.INTERNAL,
        ) as span:
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", self.agent_id)
            span.set_attribute("cortexhub.run.status", "running")

            if framework:
                span.set_attribute("cortexhub.run.framework", framework)
            if metadata:
                span.set_attribute(
                    "cortexhub.run.metadata",
                    json.dumps(metadata, default=str),
                )

            span.set_status(Status(StatusCode.OK))

    def has_policies(self) -> bool:
        """Check if enforcement mode is active (policies loaded from CortexHub).
        
        Returns:
            True if policies are loaded and enforcement is active,
            False if in observation mode (no policies).
        """
        return self.enforce

    def sync_policies(self) -> bool:
        """Manually sync policies from cloud.
        
        Useful after enabling policies in the CortexHub dashboard
        to reload them without restarting your application.
        
        Returns:
            True if policies were loaded/refreshed,
            False if no policies available or sync failed.
        """
        if not self.backend:
            return False

        # Re-validate API key to get latest policies
        is_valid, sdk_config = self.backend.validate_api_key()
        if is_valid and sdk_config and sdk_config.has_policies:
            self._init_enforcement_mode(sdk_config)
            logger.info("Policies reloaded after sync")
            return True

        return False

    def protect(self, framework: "Framework") -> None:
        """Apply governance adapter for the specified framework.
        
        This is called automatically by cortexhub.init(). You typically
        don't need to call this directly.
        
        Args:
            framework: The Framework enum value to protect
            
        Raises:
            ImportError: If framework dependencies are not installed
            ValueError: If framework is not supported
        """
        from cortexhub.frameworks import Framework
        
        # Apply MCP interceptor (works with all frameworks)
        self.mcp_interceptor.apply_all()
        
        # Apply framework-specific adapter
        if framework == Framework.LANGGRAPH:
            try:
                from cortexhub.adapters.langgraph import LangGraphAdapter
                adapter = LangGraphAdapter(self)
                adapter.patch()
                logger.info("LangGraph adapter applied", framework="langgraph")
            except ImportError as e:
                raise ImportError(
                    "LangGraph dependencies not installed. "
                    "Install with: pip install cortexhub[langgraph]"
                ) from e
                
        elif framework == Framework.CREWAI:
            try:
                from cortexhub.adapters.crewai import CrewAIAdapter
                adapter = CrewAIAdapter(self)
                adapter.patch()
                logger.info("CrewAI adapter applied", framework="crewai")
            except ImportError as e:
                raise ImportError(
                    "CrewAI dependencies not installed. "
                    "Install with: pip install cortexhub[crewai]"
                ) from e
                
        elif framework == Framework.OPENAI_AGENTS:
            try:
                from cortexhub.adapters.openai_agents import OpenAIAgentsAdapter
                adapter = OpenAIAgentsAdapter(self)
                adapter.patch()
                logger.info("OpenAI Agents adapter applied", framework="openai_agents")
            except ImportError as e:
                raise ImportError(
                    "OpenAI Agents dependencies not installed. "
                    "Install with: pip install cortexhub[openai-agents]"
                ) from e
                
        elif framework == Framework.CLAUDE_AGENTS:
            try:
                from cortexhub.adapters.claude_agents import ClaudeAgentsAdapter
                adapter = ClaudeAgentsAdapter(self)
                adapter.patch()
                logger.info("Claude Agents adapter applied", framework="claude_agents")
            except ImportError as e:
                raise ImportError(
                    "Claude Agent SDK dependencies not installed. "
                    "Install with: pip install cortexhub[claude-agents]"
                ) from e
        else:
            raise ValueError(
                f"Unknown framework: {framework}. "
                f"Supported: LANGGRAPH, CREWAI, OPENAI_AGENTS, CLAUDE_AGENTS"
            )
    
    def auto_protect(
        self, enable_llm: bool = True, enable_mcp: bool = True, enable_tools: bool = True
    ) -> None:
        """[DEPRECATED] Auto-detect and patch supported frameworks.
        
        Use cortexhub.init(framework=Framework.XXX) instead.
        """
        import warnings
        warnings.warn(
            "auto_protect() is deprecated. Use cortexhub.init(framework=Framework.XXX) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        if enable_mcp:
            self.mcp_interceptor.apply_all()

        from cortexhub.auto_protect import auto_protect_frameworks
        auto_protect_frameworks(self, enable_llm=enable_llm, enable_tools=enable_tools)

        logger.info(
            "Auto-protection enabled",
            llm=enable_llm,
            mcp=enable_mcp,
            tools=enable_tools,
        )

    def shutdown(self) -> None:
        """Shutdown OpenTelemetry and flush spans."""
        try:
            if hasattr(self, '_tracer_provider') and self._tracer_provider:
                try:
                    self._tracer_provider.shutdown(timeout_millis=5000)
                except TypeError:
                    self._tracer_provider.shutdown()
            if hasattr(self, 'backend') and self.backend:
                self.backend.close()
        except Exception as e:
            logger.debug("Error during shutdown", error=str(e))

    def __del__(self):
        """Cleanup - flush telemetry on shutdown."""
        try:
            self.shutdown()
        except Exception:
            pass
