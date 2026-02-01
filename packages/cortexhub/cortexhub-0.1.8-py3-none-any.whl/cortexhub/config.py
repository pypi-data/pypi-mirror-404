"""Configuration management for CortexHub SDK.

The SDK configuration is minimal by design:
- Telemetry is ALWAYS governance mode (not configurable)
- Guardrail behavior comes from POLICIES (not SDK config)
- Approval behavior comes from POLICIES (not SDK config)

SDK only configures:
- Where to cache policies locally
- Connection settings (API key, URL)
"""

import os


class Config:
    """SDK configuration - minimal by design.
    
    Most behavior is determined by POLICIES in the CortexHub cloud,
    not SDK configuration.
    """

    def __init__(
        self,
        policies_dir: str = "./policies",
    ):
        """Initialize configuration.

        Args:
            policies_dir: Directory for local policy cache
        """
        self.policies_dir = policies_dir

    def validate(self) -> None:
        """Validate configuration settings."""
        # Minimal validation - most config comes from cloud
        pass
