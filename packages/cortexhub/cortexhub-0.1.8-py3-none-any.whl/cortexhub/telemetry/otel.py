"""OpenTelemetry-based telemetry for CortexHub.

This module implements the OTLP-based telemetry as specified in TELEMETRY_OTEL_DESIGN.md.

Key features:
- OTel spans instead of custom events
- BatchSpanProcessor for batching, retry, backpressure
- OTLP/HTTP (JSON) transport
- Guardrail findings as span events
- Privacy mode support

Usage:
    from cortexhub.telemetry.otel import OTelTelemetry
    
    telemetry = OTelTelemetry(
        agent_id="customer_support",
        api_key="chk_...",
        backend_url="https://api.cortexhub.io",
        privacy=True,
    )
    
    # Create span for tool call
    with telemetry.trace_tool_call("process_refund", args={"amount": 75}) as span:
        result = tool.invoke(args)
        telemetry.record_tool_result(span, success=True, result=result)
"""

import json
import os
from datetime import datetime
from typing import Any
from contextlib import contextmanager

import structlog

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Span, Status, StatusCode, SpanKind

from cortexhub.version import __version__

logger = structlog.get_logger(__name__)


class OTelTelemetry:
    """OpenTelemetry-based telemetry for CortexHub.
    
    This class manages OTel tracing with proper batching, retry, and backpressure.
    """
    
    def __init__(
        self,
        agent_id: str,
        api_key: str | None = None,
        backend_url: str = "https://api.cortexhub.io",
        privacy: bool = True,
        session_id: str | None = None,
    ):
        """Initialize OTel telemetry.
        
        Args:
            agent_id: Unique identifier for this agent
            api_key: CortexHub API key (from environment if not provided)
            backend_url: CortexHub backend URL
            privacy: If True (default), no raw data sent. If False, raw data included.
            session_id: Session identifier (auto-generated if not provided)
        """
        self.agent_id = agent_id
        self.api_key = api_key or os.getenv("CORTEXHUB_API_KEY")
        self.backend_url = backend_url.rstrip("/")
        self.privacy = privacy
        self.session_id = session_id or self._generate_session_id()
        
        # Create resource with agent/project metadata
        self.resource = Resource.create({
            "service.name": "cortexhub-sdk",
            "service.version": __version__,
            "cortexhub.agent.id": agent_id,
            "cortexhub.privacy.mode": "enabled" if privacy else "disabled",
        })
        
        # Create tracer provider
        self.provider = TracerProvider(resource=self.resource)
        
        # Configure OTLP exporter if API key provided
        if self.api_key:
            exporter = OTLPSpanExporter(
                endpoint=f"{self.backend_url}/v1/traces",
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
            self.provider.add_span_processor(processor)
            
            logger.info(
                "OTel telemetry initialized with backend export",
                backend_url=self.backend_url,
                agent_id=agent_id,
                privacy="enabled" if privacy else "DISABLED",
            )
        else:
            logger.info(
                "OTel telemetry initialized (local only - no API key)",
                agent_id=agent_id,
            )
        
        # Set as global tracer provider
        trace.set_tracer_provider(self.provider)
        
        # Get tracer
        self.tracer = trace.get_tracer("cortexhub", __version__)
        
        if not privacy:
            logger.warning(
                "⚠️  PRIVACY MODE DISABLED - Raw inputs/outputs will be sent to backend",
                warning="DO NOT USE IN PRODUCTION",
                use_case="Testing policies, redaction, and approval workflows",
            )
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        import uuid
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"{timestamp}-{random_suffix}"
    
    @contextmanager
    def trace_tool_call(
        self,
        tool_name: str,
        tool_description: str | None = None,
        arg_names: list[str] | None = None,
        args: dict | None = None,
        framework: str = "unknown",
    ):
        """Start a span for a tool call.
        
        Usage:
            with telemetry.trace_tool_call("process_refund", args={"amount": 75}) as span:
                result = tool.invoke(args)
                telemetry.record_tool_result(span, success=True, result=result)
        
        Args:
            tool_name: Name of the tool being invoked
            tool_description: Human-readable description of the tool
            arg_names: List of argument names (extracted from args if not provided)
            args: Tool arguments (only sent if privacy=False)
            framework: Framework name (langchain, openai_agents, etc.)
            
        Yields:
            OTel Span for the tool call
        """
        span = self.tracer.start_span(
            name="tool.invoke",
            kind=SpanKind.INTERNAL,
        )
        
        try:
            # Set standard attributes
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", self.agent_id)
            span.set_attribute("cortexhub.tool.name", tool_name)
            span.set_attribute("cortexhub.tool.framework", framework)
            
            if tool_description:
                span.set_attribute("cortexhub.tool.description", tool_description)
            
            # Extract arg names if not provided
            if arg_names is None and args:
                arg_names = list(args.keys())
            
            if arg_names:
                span.set_attribute("cortexhub.tool.arg_names", arg_names)
            
            # Raw data only if privacy disabled
            if not self.privacy and args:
                span.set_attribute("cortexhub.raw.args", json.dumps(args, default=str))
            
            yield span
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("cortexhub.error.message", str(e))
            raise
        finally:
            span.end()
    
    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        prompt: str | None = None,
    ):
        """Start a span for an LLM call.
        
        Usage:
            with telemetry.trace_llm_call("gpt-4o-mini", prompt=messages) as span:
                response = llm.invoke(messages)
                telemetry.record_llm_result(span, response=response.content)
        
        Args:
            model: Model name (e.g., "gpt-4o-mini")
            prompt: Prompt content (only for guardrail checking, sent only if privacy=False)
            
        Yields:
            OTel Span for the LLM call
        """
        span = self.tracer.start_span(
            name="llm.call",
            kind=SpanKind.CLIENT,
        )
        
        try:
            # Set standard attributes (following gen_ai.* conventions)
            span.set_attribute("cortexhub.session.id", self.session_id)
            span.set_attribute("cortexhub.agent.id", self.agent_id)
            span.set_attribute("gen_ai.request.model", model)
            
            # Raw data only if privacy disabled
            if not self.privacy and prompt:
                span.set_attribute("cortexhub.raw.prompt", prompt)
            
            yield span
            
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("cortexhub.error.message", str(e))
            raise
        finally:
            span.end()
    
    def record_tool_result(
        self,
        span: Span,
        success: bool,
        result: Any = None,
        error: str | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Record the result of a tool call.
        
        Args:
            span: The span to record the result on
            success: Whether the tool call succeeded
            result: Tool result (only sent if privacy=False)
            error: Error message if failed
            latency_ms: Execution latency in milliseconds
        """
        span.set_attribute("cortexhub.result.success", success)
        
        if latency_ms is not None:
            span.set_attribute("cortexhub.latency_ms", latency_ms)
        
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
        span: Span,
        response: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        latency_ms: float | None = None,
    ) -> None:
        """Record the result of an LLM call.
        
        Args:
            span: The span to record the result on
            response: LLM response content (only sent if privacy=False)
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency_ms: LLM call latency in milliseconds
        """
        span.set_status(Status(StatusCode.OK))
        
        if prompt_tokens is not None:
            span.set_attribute("gen_ai.usage.prompt_tokens", prompt_tokens)
        if completion_tokens is not None:
            span.set_attribute("gen_ai.usage.completion_tokens", completion_tokens)
        if latency_ms is not None:
            span.set_attribute("cortexhub.latency_ms", latency_ms)
        
        if not self.privacy and response:
            span.set_attribute("cortexhub.raw.response", response)
    
    def add_guardrail_event(
        self,
        span: Span,
        event_name: str,
        attributes: dict[str, Any],
    ) -> None:
        """Add a guardrail finding as a span event.
        
        Args:
            span: The span to add the event to
            event_name: Event name (e.g., "guardrail.pii_in_prompt")
            attributes: Event attributes
        """
        span.add_event(event_name, attributes=attributes)
    
    def add_pii_finding(
        self,
        span: Span,
        content_type: str,  # "prompt" or "response"
        pii_types: list[str],
        count: int,
        counts_per_type: dict[str, int] | None = None,
    ) -> None:
        """Add a PII detection finding as a span event.
        
        Args:
            span: The span to add the event to
            content_type: Where PII was found ("prompt" or "response")
            pii_types: List of unique PII types detected
            count: Total number of PII instances found
            counts_per_type: Optional dict mapping type to count (e.g., {"email_address": 3})
        """
        attributes: dict[str, Any] = {
            "pii.detected": True,
            "pii.count": count,
            "pii.types": pii_types,
        }
        
        # Add per-type counts for backend aggregation
        if counts_per_type:
            # Store as JSON string since OTLP attributes don't support nested objects
            attributes["pii.counts_per_type"] = json.dumps(counts_per_type)
        
        span.add_event(f"guardrail.pii_in_{content_type}", attributes=attributes)
    
    def add_secrets_finding(
        self,
        span: Span,
        content_type: str,  # "prompt" or "response"
        secret_types: list[str],
        count: int,
        counts_per_type: dict[str, int] | None = None,
    ) -> None:
        """Add a secrets detection finding as a span event.
        
        Args:
            span: The span to add the event to
            content_type: Where secrets were found ("prompt" or "response")
            secret_types: List of unique secret types detected
            count: Total number of secrets found
            counts_per_type: Optional dict mapping type to count (e.g., {"api_key": 2})
        """
        attributes: dict[str, Any] = {
            "secrets.detected": True,
            "secrets.count": count,
            "secrets.types": secret_types,
        }
        
        # Add per-type counts for backend aggregation
        if counts_per_type:
            attributes["secrets.counts_per_type"] = json.dumps(counts_per_type)
        
        span.add_event(f"guardrail.secrets_in_{content_type}", attributes=attributes)
    
    def add_prompt_manipulation_finding(
        self,
        span: Span,
        patterns: list[str],
    ) -> None:
        """Add a prompt manipulation detection finding as a span event.
        
        Args:
            span: The span to add the event to
            patterns: List of manipulation patterns detected
        """
        span.add_event(
            "guardrail.prompt_manipulation",
            attributes={
                "manipulation.detected": True,
                "manipulation.patterns": patterns,
            }
        )
    
    def add_policy_decision(
        self,
        span: Span,
        effect: str,
        policy_id: str | None = None,
        reasoning: str | None = None,
    ) -> None:
        """Add a policy decision as a span event.
        
        Args:
            span: The span to add the event to
            effect: Policy effect ("allow", "deny", "escalate")
            policy_id: ID of the policy that matched
            reasoning: Explanation for the decision
        """
        attributes = {
            "policy.effect": effect,
        }
        if policy_id:
            attributes["policy.id"] = policy_id
        if reasoning:
            attributes["policy.reasoning"] = reasoning
        
        span.add_event("policy.decision", attributes=attributes)
    
    def shutdown(self) -> None:
        """Flush pending spans and shutdown."""
        if hasattr(self.provider, 'shutdown'):
            self.provider.shutdown()
        logger.info("OTel telemetry shutdown complete")
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush all pending spans.
        
        Args:
            timeout_millis: Timeout in milliseconds
            
        Returns:
            True if flush succeeded, False otherwise
        """
        if hasattr(self.provider, 'force_flush'):
            return self.provider.force_flush(timeout_millis)
        return True


# Singleton instance for easy access
_telemetry_instance: OTelTelemetry | None = None


def init_telemetry(
    agent_id: str,
    api_key: str | None = None,
    backend_url: str = "https://api.cortexhub.io",
    privacy: bool = True,
) -> OTelTelemetry:
    """Initialize the global OTel telemetry instance.
    
    Args:
        agent_id: Unique identifier for this agent
        api_key: CortexHub API key
        backend_url: CortexHub backend URL
        privacy: If True (default), no raw data sent
        
    Returns:
        OTelTelemetry instance
    """
    global _telemetry_instance
    _telemetry_instance = OTelTelemetry(
        agent_id=agent_id,
        api_key=api_key,
        backend_url=backend_url,
        privacy=privacy,
    )
    return _telemetry_instance


def get_telemetry() -> OTelTelemetry | None:
    """Get the global OTel telemetry instance."""
    return _telemetry_instance


def shutdown_telemetry() -> None:
    """Shutdown the global OTel telemetry instance."""
    global _telemetry_instance
    if _telemetry_instance:
        _telemetry_instance.shutdown()
        _telemetry_instance = None
