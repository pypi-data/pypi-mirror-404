"""Secrets detection using detect-secrets.

Production-grade secret detection using Yelp's detect-secrets.
"""

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import structlog
from detect_secrets.core.secrets_collection import SecretsCollection
from detect_secrets.plugins.aws import AWSKeyDetector
from detect_secrets.plugins.basic_auth import BasicAuthDetector
from detect_secrets.plugins.github_token import GitHubTokenDetector
from detect_secrets.plugins.high_entropy_strings import HexHighEntropyString
from detect_secrets.plugins.jwt import JwtTokenDetector
from detect_secrets.plugins.private_key import PrivateKeyDetector
from detect_secrets.plugins.slack import SlackDetector

logger = structlog.get_logger(__name__)


@dataclass
class SecretsDetectionResult:
    """Result of secrets detection scan."""
    detected: bool
    count: int
    types: list[str]
    counts_per_type: dict[str, int] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)


class SecretsDetector:
    """Production-grade secrets detection using detect-secrets.

    Uses multiple plugins to detect:
    - AWS keys (AKIA...)
    - GitHub tokens (ghp_, gho_, etc.)
    - Slack tokens (xoxb-, xoxp-, etc.)
    - JWT tokens
    - Private keys (RSA, SSH)
    - Basic auth credentials
    - High entropy strings
    """

    def __init__(self, enabled: bool = True):
        """Initialize secrets detector.

        Args:
            enabled: Whether secrets detection is enabled
        """
        self.enabled = enabled

        # Initialize all plugins
        self.plugins = [
            AWSKeyDetector(),
            GitHubTokenDetector(),
            SlackDetector(),
            BasicAuthDetector(),
            PrivateKeyDetector(),
            JwtTokenDetector(),
            HexHighEntropyString(limit=3.0),  # High entropy threshold
        ]

        logger.info(
            "Secrets detector initialized",
            plugins=len(self.plugins),
        )

    def scan(self, text: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Scan text or dict for secrets.

        Args:
            text: Text or dict to scan

        Returns:
            List of secret findings
        """
        if not self.enabled:
            return []

        # Convert dict to JSON string
        if isinstance(text, dict):
            text = json.dumps(text)

        findings = []

        # Scan with each plugin
        for plugin in self.plugins:
            try:
                secrets = plugin.analyze_line(filename="inline", line=text, line_number=0)

                for secret in secrets:
                    # Never log actual secret value
                    findings.append(
                        {
                            "type": secret.type,
                            "value": "***",  # Redacted
                            "start": secret.line_number,
                            "end": secret.line_number,
                            "confidence": 0.9,
                        }
                    )
            except Exception as e:
                logger.debug(f"Plugin {plugin.__class__.__name__} error: {e}")

        if findings:
            logger.warning(
                "Secrets detected",
                count=len(findings),
                types=list(set(f["type"] for f in findings)),
            )

        return findings

    def detect(self, text: str | dict[str, Any]) -> SecretsDetectionResult:
        """Detect secrets in text and return structured result.

        Args:
            text: Text or dict to scan

        Returns:
            SecretsDetectionResult with detection details and counts per type
        """
        findings = self.scan(text)
        
        if not findings:
            return SecretsDetectionResult(
                detected=False,
                count=0,
                types=[],
                counts_per_type={},
                findings=[],
            )
        
        # Count occurrences per type
        type_counts = Counter(f["type"] for f in findings)
        
        return SecretsDetectionResult(
            detected=True,
            count=len(findings),
            types=list(type_counts.keys()),
            counts_per_type=dict(type_counts),
            findings=findings,
        )

    def has_secrets(self, text: str | dict[str, Any]) -> bool:
        """Check if text contains secrets.

        Args:
            text: Text or dict to check

        Returns:
            True if secrets detected
        """
        return len(self.scan(text)) > 0

    def redact(self, text: str | dict[str, Any]) -> tuple[str | dict, list[dict[str, Any]]]:
        """Scan and redact secrets.

        Args:
            text: Text or dict to redact

        Returns:
            (redacted_content, findings)
        """
        is_dict = isinstance(text, dict)
        original_text = json.dumps(text) if is_dict else text

        # Scan for secrets
        findings = self.scan(original_text)

        if not findings:
            return text, []

        # Redact known patterns
        redacted = original_text

        # AWS keys
        redacted = re.sub(r"AKIA[0-9A-Z]{16}", "[REDACTED-AWS_KEY]", redacted)

        # GitHub tokens
        redacted = re.sub(r"gh[ps]_[A-Za-z0-9]{36}", "[REDACTED-GITHUB_TOKEN]", redacted)

        # Slack tokens
        redacted = re.sub(r"xox[baprs]-[A-Za-z0-9-]+", "[REDACTED-SLACK_TOKEN]", redacted)

        # Generic high-entropy strings (be conservative)
        # redacted = re.sub(r"\b[A-Za-z0-9]{40,}\b", "[REDACTED-SECRET]", redacted)

        logger.info(
            "Secrets redacted",
            count=len(findings),
            types=list(set(f["type"] for f in findings)),
        )

        # Convert back to dict if needed
        if is_dict:
            try:
                return json.loads(redacted), findings
            except json.JSONDecodeError:
                return text, findings

        return redacted, findings
