"""Prompt injection detection using pattern-based heuristics.

Lightweight, fast detection without ML dependencies.
Baseline defense against common attack patterns.

Premium Features (Backend):
- LLM Guard: ML-based injection + jailbreak detection
- Toxicity detection
- Advanced attack pattern recognition
"""

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ManipulationDetectionResult:
    """Result of prompt manipulation detection scan."""
    detected: bool
    patterns: list[str]
    findings: list[dict[str, Any]] = field(default_factory=list)
    
    @property
    def count(self) -> int:
        """Total matches found."""
        return len(self.findings)


class PromptManipulationDetector:
    """Lightweight prompt injection detection using patterns.

    Detects common attack patterns:
    - Role switching ("ignore previous instructions")
    - System override ("you are now admin")
    - Delimiter abuse (excessive delimiters)
    - Encoding tricks (base64, decode)
    - Context escape ("end of system")
    - Instruction injection (special tokens)

    For premium ML-based detection (toxicity, advanced jailbreaks),
    use backend LLM Guard integration.
    """

    def __init__(self, enabled: bool = True, sensitivity: float = 0.7):
        """Initialize prompt manipulation detector.

        Args:
            enabled: Whether detection is enabled
            sensitivity: Detection sensitivity (0.0-1.0, higher = more strict)
        """
        self.enabled = enabled
        self.sensitivity = sensitivity
        self._compile_patterns()
        logger.info(
            "Prompt manipulation detector initialized (pattern-based, lightweight)",
            enabled=enabled,
            sensitivity=sensitivity,
        )

    def _compile_patterns(self) -> None:
        """Compile patterns for common prompt manipulation techniques."""
        self.patterns = {
            # Role switching / instruction negation
            "role_switch": re.compile(
                r"\b(ignore|disregard|forget|override|bypass)\s+"
                r"(previous|above|prior|all|any)\s+"
                r"(instructions?|rules?|constraints?|context|prompts?)\b",
                re.IGNORECASE,
            ),
            # System override / privilege escalation
            "system_override": re.compile(
                r"\b(you are now|act as|pretend to be|system message|"
                r"new instructions?|admin mode|developer mode|god mode)\b",
                re.IGNORECASE,
            ),
            # Delimiter abuse
            "delimiter_abuse": re.compile(r"(```|---|===|\*\*\*|###){3,}"),
            # Encoding tricks
            "encoding_tricks": re.compile(
                r"\b(base64|rot13|hex|decode|unescape|eval|exec)\s*[([]",
                re.IGNORECASE,
            ),
            # Context escape
            "context_escape": re.compile(
                r"\b(end of|start of|begin|finish)\s+(context|system|prompt|instructions?)\b",
                re.IGNORECASE,
            ),
            # Instruction injection (special tokens)
            "instruction_injection": re.compile(
                r"<\|?(im_start|im_end|system|assistant|user)\|?>",
                re.IGNORECASE,
            ),
        }

    def scan(self, text: str | dict[str, Any]) -> list[dict[str, Any]]:
        """Scan text for prompt manipulation patterns.

        Args:
            text: Text or dict to scan

        Returns:
            List of findings with pattern type and position
        """
        if not self.enabled:
            return []

        # Convert dict to JSON string for scanning
        if isinstance(text, dict):
            import json

            text = json.dumps(text)

        findings = []

        for pattern_name, pattern in self.patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                findings.append(
                    {
                        "type": pattern_name,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.7,  # Pattern-based has moderate confidence
                    }
                )

        # Filter by sensitivity threshold
        findings = [f for f in findings if f["confidence"] >= (1.0 - self.sensitivity)]

        if findings:
            logger.warning(
                "Prompt manipulation patterns detected (lightweight)",
                count=len(findings),
                patterns=list(set(f["type"] for f in findings)),
            )

        return findings

    def detect(self, text: str | dict[str, Any]) -> ManipulationDetectionResult:
        """Detect prompt manipulation and return structured result.

        Args:
            text: Text or dict to scan

        Returns:
            ManipulationDetectionResult with detection details
        """
        findings = self.scan(text)
        
        if not findings:
            return ManipulationDetectionResult(
                detected=False,
                patterns=[],
                findings=[],
            )
        
        patterns = list(set(f["type"] for f in findings))
        
        return ManipulationDetectionResult(
            detected=True,
            patterns=patterns,
            findings=findings,
        )

    def has_manipulation(self, text: str | dict[str, Any]) -> bool:
        """Check if text contains manipulation patterns.

        Args:
            text: Text or dict to check

        Returns:
            True if manipulation patterns detected
        """
        return len(self.scan(text)) > 0
