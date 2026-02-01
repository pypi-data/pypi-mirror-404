"""CortexHub Telemetry - OpenTelemetry-based Governance Telemetry.

CortexHub uses OpenTelemetry (OTel) for telemetry, providing:
- Industry-standard OTLP protocol
- Proper batching, retry, and backpressure
- Interoperability with observability tools
- AI/LLM semantic conventions

Privacy Mode (default: enabled):
- Tool name, description, argument names (NOT values)
- PII/secret types detected (NOT actual data)
- Agent ID, framework

What is NEVER sent (when privacy=True):
- Raw argument values
- Prompts or LLM responses
- PII literals (emails, SSNs, names, etc.)
- Secrets (API keys, passwords, tokens)
- Customer data

Telemetry Modes:
- privacy=True (DEFAULT): Metadata only, production-safe
- privacy=False: Raw data included, for dev/staging testing only
"""

# OTel-based telemetry
from cortexhub.telemetry.otel import (
    OTelTelemetry,
    init_telemetry,
    get_telemetry,
    shutdown_telemetry,
)

__all__ = [
    # OTel-based telemetry
    "OTelTelemetry",
    "init_telemetry",
    "get_telemetry",
    "shutdown_telemetry",
]
