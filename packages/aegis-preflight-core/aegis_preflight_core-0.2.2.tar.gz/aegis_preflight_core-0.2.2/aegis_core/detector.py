"""Sensitive data detection module.

This module provides pattern-based detection of PII, PHI, and other
sensitive data. It is the unified detection engine used by both the
Aegis API and SDK.
"""

import re
from typing import Optional

from aegis_core.types import DetectedItem, DetectionType, Finding, PII_TYPES
from aegis_core.validators import luhn_check


# Regex patterns for detection
PATTERNS: dict[str, re.Pattern] = {
    DetectionType.EMAIL: re.compile(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        re.IGNORECASE,
    ),
    DetectionType.PHONE: re.compile(
        r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}",
    ),
    DetectionType.CREDIT_CARD: re.compile(
        r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    ),
    DetectionType.SSN: re.compile(
        r"\b\d{3}-\d{2}-\d{4}\b",
    ),
    DetectionType.API_SECRET: re.compile(
        r"(?:AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{20,}|(?:api[_-]?)?(?:key|secret|token)[_-]?[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?)",
        re.IGNORECASE,
    ),
    DetectionType.IBAN: re.compile(
        r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
        re.IGNORECASE,
    ),
}

# PHI keywords (case-insensitive)
PHI_KEYWORDS: set[str] = {
    "patient",
    "mrn",
    "medical record",
    "diagnosis",
    "icd",
    "phi",
    "dob",
    "date of birth",
    "health record",
    "prescription",
    "medication",
    "treatment",
    "hospital",
    "clinic",
    "physician",
    "doctor",
    "nurse",
    "hipaa",
}


def mask_sample(value: str, detection_type: str) -> str:
    """Create a masked sample of detected value for audit logs.

    This function creates a partially masked version of the detected
    value that can be safely stored in logs while still being useful
    for debugging and verification.

    Args:
        value: The detected value to mask
        detection_type: Type of detection

    Returns:
        Masked version showing only partial data
    """
    if not value:
        return ""

    if detection_type == DetectionType.EMAIL:
        if "@" in value:
            local, domain = value.split("@", 1)
            if len(local) > 0:
                return f"{local[0]}***@{domain}"
        return "***@***.***"

    elif detection_type == DetectionType.PHONE:
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) >= 4:
            return f"XXX-XXX-{digits[-4:]}"
        return "XXX-XXX-XXXX"

    elif detection_type == DetectionType.CREDIT_CARD:
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) >= 4:
            return f"XXXX-XXXX-XXXX-{digits[-4:]}"
        return "XXXX-XXXX-XXXX-XXXX"

    elif detection_type == DetectionType.SSN:
        digits = "".join(c for c in value if c.isdigit())
        if len(digits) >= 4:
            return f"XXX-XX-{digits[-4:]}"
        return "XXX-XX-XXXX"

    elif detection_type == DetectionType.API_SECRET:
        if len(value) > 4:
            return f"***{value[-4:]}"
        return "****"

    elif detection_type == DetectionType.PHI_KEYWORD:
        return value.lower()

    elif detection_type == DetectionType.IBAN:
        if len(value) > 6:
            return f"{value[:2]}**************{value[-4:]}"
        return "****"

    # Default: show first 2 chars only
    if len(value) > 2:
        return f"{value[:2]}***"
    return "***"


def detect_patterns(content: str) -> list[Finding]:
    """Detect all sensitive patterns in content.

    Scans the content for all known sensitive data patterns
    and returns a list of findings with position information.

    Args:
        content: Text content to scan

    Returns:
        List of Finding objects with position information
    """
    findings: list[Finding] = []

    # Regex-based patterns
    for detection_type, pattern in PATTERNS.items():
        for match in pattern.finditer(content):
            value = match.group()

            # Additional validation for credit cards (Luhn)
            if detection_type == DetectionType.CREDIT_CARD:
                if not luhn_check(value):
                    continue

            findings.append(
                Finding(
                    detection_type=detection_type,
                    value=value,
                    start=match.start(),
                    end=match.end(),
                )
            )

    # PHI keyword detection
    content_lower = content.lower()
    for keyword in PHI_KEYWORDS:
        start = 0
        while True:
            pos = content_lower.find(keyword, start)
            if pos == -1:
                break
            findings.append(
                Finding(
                    detection_type=DetectionType.PHI_KEYWORD,
                    value=keyword,
                    start=pos,
                    end=pos + len(keyword),
                )
            )
            start = pos + 1

    return findings


def aggregate_findings(
    findings: list[Finding], include_samples: bool = True
) -> list[DetectedItem]:
    """Aggregate findings into detected items with counts.

    Takes a list of raw findings and aggregates them by type,
    counting occurrences and optionally including masked samples.

    Args:
        findings: List of raw findings
        include_samples: Whether to include masked samples (set False for GDPR)

    Returns:
        List of DetectedItem with aggregated counts
    """
    type_findings: dict[str, list[str]] = {}

    for finding in findings:
        if finding.detection_type not in type_findings:
            type_findings[finding.detection_type] = []
        type_findings[finding.detection_type].append(finding.value)

    detected_items: list[DetectedItem] = []
    for detection_type, values in type_findings.items():
        unique_values = list(set(values))
        sample = None
        if include_samples and unique_values:
            sample = mask_sample(unique_values[0], detection_type)

        detected_items.append(
            DetectedItem(
                type=detection_type,
                count=len(values),
                sample=sample,
            )
        )

    return detected_items


def detect(content: str, include_samples: bool = True) -> list[DetectedItem]:
    """Main detection entry point.

    This is the primary function for detecting sensitive data.
    It scans the content and returns aggregated results.

    Args:
        content: Text content to scan for sensitive data
        include_samples: Whether to include masked samples in results

    Returns:
        List of DetectedItem with type, count, and optional sample

    Example:
        >>> items = detect("Email: john@example.com, phone: 555-123-4567")
        >>> for item in items:
        ...     print(f"{item.type}: {item.count}")
        EMAIL: 1
        PHONE: 1
    """
    findings = detect_patterns(content)
    return aggregate_findings(findings, include_samples=include_samples)


def has_detection_type(detected: list[DetectedItem], *types: str) -> bool:
    """Check if any of the specified types are in detected items.

    Args:
        detected: List of detected items
        *types: Detection types to check for

    Returns:
        True if any of the types are present
    """
    detected_types = {item.type for item in detected}
    return bool(detected_types.intersection(types))


def get_pii_types() -> set[str]:
    """Get the set of PII detection types.

    Returns:
        Set of detection types that are considered PII
    """
    return PII_TYPES.copy()


def has_pii(detected: list[DetectedItem]) -> bool:
    """Check if any PII is detected.

    Args:
        detected: List of detected items

    Returns:
        True if any PII types are present
    """
    return any(item.type in PII_TYPES for item in detected)


def has_phi(detected: list[DetectedItem]) -> bool:
    """Check if any PHI keywords are detected.

    Args:
        detected: List of detected items

    Returns:
        True if PHI keywords are present
    """
    return has_detection_type(detected, DetectionType.PHI_KEYWORD)


class PatternDetector:
    """Detector class for object-oriented usage.

    This class wraps the module-level functions for use in contexts
    where an instantiated object is preferred.

    Example:
        detector = PatternDetector(include_samples=True)
        items = detector.detect("Contact john@example.com")
    """

    def __init__(self, include_samples: bool = True):
        """Initialize detector.

        Args:
            include_samples: Whether to include masked samples in results
        """
        self.include_samples = include_samples

    def detect(self, content: str) -> list[DetectedItem]:
        """Detect sensitive data in content.

        Args:
            content: Text content to scan

        Returns:
            List of DetectedItem with detection results
        """
        return detect(content, include_samples=self.include_samples)

    def detect_patterns(self, content: str) -> list[Finding]:
        """Detect patterns with position information.

        Args:
            content: Text content to scan

        Returns:
            List of Finding objects with positions
        """
        return detect_patterns(content)

    def has_pii(self, detected: list[DetectedItem]) -> bool:
        """Check if PII is present in detected items."""
        return has_pii(detected)

    def has_phi(self, detected: list[DetectedItem]) -> bool:
        """Check if PHI keywords are present in detected items."""
        return has_phi(detected)
