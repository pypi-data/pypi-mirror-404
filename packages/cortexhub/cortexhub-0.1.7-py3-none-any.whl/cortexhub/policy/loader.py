"""Policy loader for local Cedar policy bundles.

Architectural invariants (from AGENTS.md):
- MUST NOT make decisions
- MUST NOT evaluate policies
- ONLY loads and validates policy files
"""

import json
from pathlib import Path
from typing import Any

import structlog

from cortexhub.errors import PolicyLoadError

logger = structlog.get_logger(__name__)


class PolicyBundle:
    """Represents a loaded policy bundle."""

    def __init__(
        self,
        policies: str,
        schema: dict[str, Any],
        metadata: dict[str, Any],
    ):
        """Initialize policy bundle.

        Args:
            policies: Cedar policies as string
            schema: Cedar schema as dict
            metadata: Bundle metadata
        """
        self.policies = policies
        self.schema = schema
        self.metadata = metadata
        self.version = metadata.get("version", "unknown")
        self.default_behavior = metadata.get("default_behavior", "allow_and_log")


class PolicyLoader:
    """Loads Cedar policy bundles from local filesystem.

    Responsibilities:
    - Load policy files
    - Validate structure
    - Parse metadata

    NOT responsible for:
    - Making decisions
    - Evaluating policies
    """

    def __init__(self, policies_dir: str = "./policies"):
        """Initialize policy loader.

        Args:
            policies_dir: Directory containing Cedar policy bundle
        """
        self.policies_dir = Path(policies_dir)
        logger.info("Policy loader initialized", policies_dir=str(self.policies_dir))

    def load(self) -> PolicyBundle:
        """Load policy bundle from filesystem.

        Returns:
            PolicyBundle with policies, schema, and metadata

        Raises:
            PolicyLoadError: If bundle cannot be loaded or is invalid
        """
        try:
            # Load Cedar policies
            policies_file = self.policies_dir / "cedar" / "policies.cedar"
            if not policies_file.exists():
                raise PolicyLoadError(
                    f"Policies file not found: {policies_file}",
                    policies_dir=str(self.policies_dir),
                )

            with open(policies_file) as f:
                policies = f.read()

            # Load Cedar schema
            schema_file = self.policies_dir / "cedar" / "schema.json"
            if not schema_file.exists():
                raise PolicyLoadError(
                    f"Schema file not found: {schema_file}",
                    policies_dir=str(self.policies_dir),
                )

            with open(schema_file) as f:
                schema = json.load(f)

            # Load metadata
            metadata_file = self.policies_dir / "metadata.json"
            if not metadata_file.exists():
                raise PolicyLoadError(
                    f"Metadata file not found: {metadata_file}",
                    policies_dir=str(self.policies_dir),
                )

            with open(metadata_file) as f:
                metadata = json.load(f)

            bundle = PolicyBundle(policies=policies, schema=schema, metadata=metadata)

            logger.info(
                "Policy bundle loaded",
                version=bundle.version,
                default_behavior=bundle.default_behavior,
                policies_size=len(policies),
            )

            return bundle

        except PolicyLoadError:
            raise
        except Exception as e:
            raise PolicyLoadError(
                f"Failed to load policy bundle: {e}",
                policies_dir=str(self.policies_dir),
            ) from e

    def validate_bundle(self, bundle: PolicyBundle) -> None:
        """Validate policy bundle structure.

        Args:
            bundle: Policy bundle to validate

        Raises:
            PolicyLoadError: If bundle is invalid
        """
        # Basic validation
        if not bundle.policies:
            raise PolicyLoadError(
                "Policy bundle contains no policies",
                policies_dir=str(self.policies_dir),
            )

        if not bundle.schema:
            raise PolicyLoadError(
                "Policy bundle contains no schema",
                policies_dir=str(self.policies_dir),
            )

        # Validate metadata
        required_metadata_fields = ["version", "default_behavior"]
        for field in required_metadata_fields:
            if field not in bundle.metadata:
                raise PolicyLoadError(
                    f"Metadata missing required field: {field}",
                    policies_dir=str(self.policies_dir),
                )

        logger.info("Policy bundle validated successfully")
