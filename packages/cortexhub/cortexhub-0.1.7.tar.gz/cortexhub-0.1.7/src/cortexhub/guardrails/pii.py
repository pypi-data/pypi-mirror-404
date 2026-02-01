"""PII detection and redaction using Presidio.

Production-grade PII detection with 50+ entity types using Microsoft Presidio.
NO fallbacks - Presidio is required.

Supports:
- User-configured PII types (redact only selected types)
- Custom regex patterns for company-specific sensitive data
"""

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

import structlog
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = structlog.get_logger(__name__)


@dataclass
class CustomPattern:
    """Custom regex pattern for detection."""
    name: str
    pattern: str
    description: str | None = None
    enabled: bool = True


@dataclass
class PIIDetectionResult:
    """Result of PII detection scan."""
    detected: bool
    count: int  # Total raw matches
    types: list[str]  # Unique PII types found
    counts_per_type: dict[str, int] = field(default_factory=dict)  # Matches per type
    unique_values_per_type: dict[str, int] = field(default_factory=dict)  # Unique values per type
    findings: list[dict[str, Any]] = field(default_factory=list)
    
    @property
    def summary(self) -> str:
        """Human-readable summary of detections."""
        if not self.detected:
            return "No PII detected"
        
        parts = []
        for pii_type in sorted(self.types):
            unique_count = self.unique_values_per_type.get(pii_type, 0)
            total_count = self.counts_per_type.get(pii_type, 0)
            
            # Format: "3 SSN" or "5 SSN (12 occurrences)" if duplicates
            if unique_count == total_count:
                parts.append(f"{unique_count} {pii_type}")
            else:
                parts.append(f"{unique_count} {pii_type} ({total_count} occurrences)")
        
        return ", ".join(parts)
    
    @property
    def unique_count(self) -> int:
        """Total unique PII values detected."""
        return sum(self.unique_values_per_type.values())


class PIIDetector:
    """Production-grade PII detection using Microsoft Presidio.

    Detects 50+ PII types:
    - EMAIL_ADDRESS, PHONE_NUMBER
    - US_SSN, US_PASSPORT, US_DRIVER_LICENSE
    - CREDIT_CARD, IBAN_CODE, CRYPTO
    - PERSON, LOCATION, ORGANIZATION
    - MEDICAL_LICENSE, NRP (medical terms for HIPAA)
    - And many more...
    
    Supports user configuration:
    - allowed_types: Only detect/redact these specific PII types
    - custom_patterns: Custom regex patterns for company-specific data
    """

    def __init__(
        self,
        enabled: bool = True,
        confidence_threshold: float = 0.5,
        allowed_types: list[str] | None = None,
        custom_patterns: list[CustomPattern] | None = None,
    ):
        """Initialize PII detector with Presidio.

        Args:
            enabled: Whether PII detection is enabled
            confidence_threshold: Minimum confidence for detection (0.0-1.0)
            allowed_types: If set, only detect these PII types (None = all types)
            custom_patterns: Custom regex patterns to detect
        """
        self.enabled = enabled
        self.confidence_threshold = confidence_threshold
        # Normalize to lowercase for comparison
        self.allowed_types = [t.lower() for t in allowed_types] if allowed_types else None
        self.custom_patterns = custom_patterns or []

        # Configure NLP engine (use small model for speed)
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }

        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()

        # Initialize analyzer with custom registry
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        
        # Add custom pattern recognizers
        for cp in self.custom_patterns:
            if cp.enabled:
                try:
                    pattern = Pattern(
                        name=cp.name,
                        regex=cp.pattern,
                        score=0.8,  # High confidence for custom patterns
                    )
                    recognizer = PatternRecognizer(
                        supported_entity=f"CUSTOM_{cp.name.upper()}",
                        patterns=[pattern],
                    )
                    registry.add_recognizer(recognizer)
                    logger.info(f"Added custom PII pattern: {cp.name}")
                except Exception as e:
                    logger.warning(f"Failed to add custom pattern {cp.name}: {e}")

        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
        self.anonymizer = AnonymizerEngine()

        logger.info(
            "PII detector initialized",
            enabled=enabled,
            threshold=confidence_threshold,
            nlp_model="en_core_web_sm",
            allowed_types=self.allowed_types,
            custom_patterns_count=len(self.custom_patterns),
        )
    
    def configure(
        self,
        allowed_types: list[str] | None = None,
        custom_patterns: list[CustomPattern] | None = None,
    ) -> None:
        """Update configuration at runtime.
        
        Args:
            allowed_types: If set, only detect these PII types (None = all types)
            custom_patterns: Custom regex patterns to detect
        """
        if allowed_types is not None:
            self.allowed_types = [t.lower() for t in allowed_types]
        
        if custom_patterns is not None:
            self.custom_patterns = custom_patterns
            # Re-add custom recognizers would require re-initializing the analyzer
            # For now, custom patterns are only applied at initialization
            logger.info(
                "PII detector config updated",
                allowed_types=self.allowed_types,
            )
    
    def _filter_by_allowed_types(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter findings to only include allowed types.
        
        Args:
            findings: All detected findings
            
        Returns:
            Filtered findings (only allowed types)
        """
        if self.allowed_types is None:
            return findings  # No filter - return all
        
        filtered = [f for f in findings if f["type"].lower() in self.allowed_types]
        
        if len(filtered) != len(findings):
            logger.debug(
                "PII findings filtered by allowed types",
                original_count=len(findings),
                filtered_count=len(filtered),
                allowed_types=self.allowed_types,
            )
        
        return filtered

    def scan(self, text: str | dict[str, Any], filter_types: bool = True) -> list[dict[str, Any]]:
        """Scan text or dict for PII using Presidio.

        Args:
            text: Text or dict to scan
            filter_types: Whether to filter by allowed_types (default True)

        Returns:
            List of PII findings with type, value, position, confidence
        """
        if not self.enabled:
            return []

        # Convert dict to JSON string
        if isinstance(text, dict):
            text = json.dumps(text)

        # Analyze with Presidio
        results = self.analyzer.analyze(
            text=text,
            language="en",
            score_threshold=self.confidence_threshold,
        )

        findings = []
        for result in results:
            findings.append(
                {
                    "type": result.entity_type.lower(),
                    "value": text[result.start : result.end],
                    "start": result.start,
                    "end": result.end,
                    "confidence": result.score,
                }
            )

        # Filter by allowed types if configured
        if filter_types:
            findings = self._filter_by_allowed_types(findings)

        if findings:
            logger.warning(
                "PII detected",
                count=len(findings),
                types=list(set(f["type"] for f in findings)),
            )

        return findings

    def detect(self, text: str | dict[str, Any]) -> PIIDetectionResult:
        """Detect PII in text and return structured result.

        Args:
            text: Text or dict to scan

        Returns:
            PIIDetectionResult with detection details and counts per type
        """
        findings = self.scan(text)
        
        if not findings:
            return PIIDetectionResult(
                detected=False,
                count=0,
                types=[],
                counts_per_type={},
                unique_values_per_type={},
                findings=[],
            )
        
        # Count occurrences per type
        type_counts = Counter(f["type"] for f in findings)
        
        # Count unique values per type (deduplicate by normalized value)
        unique_per_type: dict[str, set[str]] = {}
        for f in findings:
            pii_type = f["type"]
            # Normalize value for deduplication (lowercase, strip whitespace)
            normalized_value = f["value"].lower().strip()
            if pii_type not in unique_per_type:
                unique_per_type[pii_type] = set()
            unique_per_type[pii_type].add(normalized_value)
        
        unique_counts = {t: len(values) for t, values in unique_per_type.items()}
        
        return PIIDetectionResult(
            detected=True,
            count=len(findings),
            types=list(type_counts.keys()),
            counts_per_type=dict(type_counts),
            unique_values_per_type=unique_counts,
            findings=findings,
        )

    def has_pii(self, text: str | dict[str, Any]) -> bool:
        """Check if text contains PII.

        Args:
            text: Text or dict to check

        Returns:
            True if PII detected
        """
        return len(self.scan(text)) > 0

    def redact(self, text: str | dict[str, Any]) -> tuple[str | dict, list[dict[str, Any]]]:
        """Scan and redact PII using Presidio anonymizer.
        
        Only redacts PII types that are in allowed_types (if configured).

        Args:
            text: Text or dict to redact

        Returns:
            (redacted_content, findings)
        """
        is_dict = isinstance(text, dict)
        original_text = json.dumps(text) if is_dict else text

        # Analyze for PII
        findings_raw = self.analyzer.analyze(
            text=original_text,
            language="en",
            score_threshold=self.confidence_threshold,
        )

        if not findings_raw:
            return text, []
        
        # Filter by allowed types if configured
        if self.allowed_types is not None:
            findings_raw = [
                f for f in findings_raw 
                if f.entity_type.lower() in self.allowed_types
            ]
            
            if not findings_raw:
                return text, []

        # Anonymize with Presidio - create operator per entity type for proper labeling
        operators = {}
        for result in findings_raw:
            entity_type = result.entity_type
            operators[entity_type] = OperatorConfig(
                "replace", {"new_value": f"[REDACTED-{entity_type}]"}
            )
        
        anonymized = self.anonymizer.anonymize(
            text=original_text,
            analyzer_results=findings_raw,
            operators=operators,
        )

        # Convert findings
        findings = []
        for result in findings_raw:
            findings.append(
                {
                    "type": result.entity_type.lower(),
                    "value": original_text[result.start : result.end],
                    "start": result.start,
                    "end": result.end,
                    "confidence": result.score,
                }
            )

        logger.info(
            "PII redacted",
            count=len(findings),
            types=list(set(f["type"] for f in findings)),
            allowed_types=self.allowed_types,
        )

        # Convert back to dict if original was dict
        if is_dict:
            try:
                return json.loads(anonymized.text), findings
            except json.JSONDecodeError:
                logger.warning("Redaction broke JSON structure, returning original")
                return text, findings

        return anonymized.text, findings
