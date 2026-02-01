"""Core types for Aegis detection and masking.

This module defines the shared types used across both the Aegis API
and the Aegis SDK for detection and masking operations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DetectionType(str, Enum):
    """Types of sensitive data that can be detected.

    Each type represents a category of sensitive information
    that Aegis can identify and mask.
    """

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    API_SECRET = "API_SECRET"
    PHI_KEYWORD = "PHI_KEYWORD"
    IBAN = "IBAN"
    ADDRESS = "ADDRESS"


class Decision(str, Enum):
    """Policy decision outcomes.

    These represent the possible outcomes when evaluating
    content against a policy.
    """

    ALLOWED = "ALLOWED"
    ALLOWED_WITH_MASKING = "ALLOWED_WITH_MASKING"
    BLOCKED = "BLOCKED"


class Destination(str, Enum):
    """Target destinations for content.

    Different destinations may have different policies
    for what content is allowed, masked, or blocked.
    """

    AI_TOOL = "AI_TOOL"
    VENDOR = "VENDOR"
    CUSTOMER = "CUSTOMER"


@dataclass
class Finding:
    """A single detection finding with position information.

    This represents a raw match found during pattern detection,
    including its exact position in the source text.

    Attributes:
        detection_type: The type of sensitive data detected
        value: The actual matched text
        start: Start position in the source text
        end: End position in the source text
    """

    detection_type: str
    value: str
    start: int
    end: int


@dataclass
class DetectedItem:
    """Aggregated detection result for a specific type.

    This represents the summary of all detections of a particular
    type, with a count and optional masked sample.

    Attributes:
        type: The detection type (e.g., "EMAIL", "PHONE")
        count: Number of occurrences found
        sample: Optional masked sample for display/logging
    """

    type: str
    count: int
    sample: Optional[str] = None


# PII types that identify individuals
PII_TYPES: set[str] = {
    DetectionType.EMAIL,
    DetectionType.PHONE,
    DetectionType.SSN,
    DetectionType.CREDIT_CARD,
    DetectionType.IBAN,
}


def is_pii_type(detection_type: str) -> bool:
    """Check if a detection type is considered PII.

    Args:
        detection_type: The detection type to check

    Returns:
        True if the type identifies individuals (PII)
    """
    return detection_type in PII_TYPES


def is_phi_type(detection_type: str) -> bool:
    """Check if a detection type is PHI-related.

    Args:
        detection_type: The detection type to check

    Returns:
        True if the type is PHI-related
    """
    return detection_type == DetectionType.PHI_KEYWORD
