"""LLM call interceptor for governance.

Intercepts calls to language model APIs (OpenAI, Anthropic, etc.) and records
them for observability. In enforcement mode, also evaluates policies.

GUARDRAILS APPLY HERE - LLMs should NOT receive sensitive data.
Unlike tools (which NEED the data), LLM prompts should be sanitized.

This allows compliance teams to see:
- What models are being used
- What data is being sent to LLMs
- ⚠️ PII in prompts (risk alert)
- 🚨 Secrets in prompts (critical risk)
- Prompt manipulation attempts
"""

from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class LLMInterceptor:
    """Intercepts and observes LLM API calls.

    Supports:
    - OpenAI (ChatCompletion, Completion)
    - Anthropic (Claude)
    - Azure OpenAI
    - Generic LLM APIs
    
    GUARDRAILS APPLY HERE because:
    - LLMs should NOT receive PII (data leak to external model)
    - LLMs should NOT receive secrets (credential exposure)
    - Prompts should be checked for manipulation attempts
    
    This is different from tools, which NEED the sensitive data to work.
    """

    def __init__(self, cortex_hub: Any):  # Type: CortexHub
        """Initialize LLM interceptor.

        Args:
            cortex_hub: CortexHub instance for policy enforcement
        """
        self.cortex_hub = cortex_hub
        self._openai_patched = False
        self._anthropic_patched = False
        logger.info("LLM interceptor initialized")

    def intercept_openai(self) -> None:
        """Provider-specific interception disabled (use framework adapters)."""
        logger.info("OpenAI interception disabled; use framework adapters")

    def intercept_anthropic(self) -> None:
        """Provider-specific interception disabled (use framework adapters)."""
        logger.info("Anthropic interception disabled; use framework adapters")

    def apply_all(self) -> None:
        """Provider-specific interception disabled (use framework adapters)."""
        logger.info("LLM interception is handled by framework adapters")
