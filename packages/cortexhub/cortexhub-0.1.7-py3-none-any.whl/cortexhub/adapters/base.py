"""Base adapter interface for framework interception.

Critical: Adapters MUST NOT infer intent, classify tools, rewrite arguments, or suppress failures.
They MUST ONLY construct AuthorizationRequest and run the enforcement pipeline.

Architectural rules:
- Adapter is DUMB plumbing
- SDK orchestrates everything
- Adapter explicitly branches on Decision
- Async-safe with output guardrails
- No hidden behavior
"""

from abc import ABC, abstractmethod
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


class ToolAdapter(ABC):
    """Base class for framework-specific tool adapters.

    Adapters intercept tool calls at the framework level and enforce policies
    before execution.

    Architectural Rules:
    - MUST NOT infer intent
    - MUST NOT classify tools
    - MUST NOT rewrite arguments
    - MUST NOT suppress failures
    - MUST construct AuthorizationRequest and run pipeline only
    - MUST explicitly branch on Decision (ALLOW/DENY/ESCALATE)
    - MUST support unpatch() for test isolation
    """

    def __init__(self, cortex_hub: Any):  # Type: CortexHub, but avoiding circular import
        """Initialize adapter.

        Args:
            cortex_hub: CortexHub instance for policy enforcement
        """
        self.cortex_hub = cortex_hub
        logger.info(
            "Adapter initialized", adapter=self.__class__.__name__, framework=self.framework_name
        )

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Name of the framework this adapter supports."""
        pass

    @abstractmethod
    def patch(self) -> None:
        """Patch the framework to intercept tool calls.

        This method should monkey-patch or wrap the framework's tool execution
        mechanism to enforce governance before actual execution.
        
        Pipeline that MUST be followed:
        1. Build AuthorizationRequest (don't flatten!)
        2. Log tool invocation (pending)
        3. Run input guardrails
        4. Evaluate policy -> get Decision
        5. EXPLICITLY branch on Decision
        6. Execute tool
        7. Run output guardrails (async-safe)
        8. Log execution result
        """
        pass

    def unpatch(self) -> None:
        """Restore original framework methods.
        
        Useful for:
        - Test isolation
        - REPL usage
        - Multiple SDK instances
        
        Default implementation does nothing.
        Subclasses should override if they store original methods.
        """
        logger.debug("unpatch() not implemented for this adapter")

    @abstractmethod
    def intercept(
        self, tool_fn: Callable, tool_name: str, args: dict[str, Any], **kwargs: Any
    ) -> Any:
        """Intercept a tool call and enforce policies.

        NOTE: Most adapters should use govern_execution() from pipeline.py
        instead of implementing this directly.

        Args:
            tool_fn: The actual tool function to execute (if allowed)
            tool_name: Name of the tool being invoked
            args: Arguments passed to the tool
            **kwargs: Additional metadata from the framework

        Returns:
            Result of tool execution (if allowed)

        Raises:
            PolicyViolationError: If policy denies execution
            GuardrailViolationError: If guardrails block execution
            ApprovalDeniedError: If approval is denied
        """
        pass

    def is_framework_available(self) -> bool:
        """Check if the framework is available (imported).

        Returns:
            True if the framework is available
        """
        import sys

        # Check if framework module is in sys.modules
        framework_modules = self._get_framework_modules()
        return any(mod in sys.modules for mod in framework_modules)

    @abstractmethod
    def _get_framework_modules(self) -> list[str]:
        """Get list of module names that indicate framework presence.

        Returns:
            List of module names to check in sys.modules
        """
        pass
