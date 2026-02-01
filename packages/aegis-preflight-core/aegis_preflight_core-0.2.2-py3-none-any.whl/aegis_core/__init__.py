"""Aegis Core - Detection and masking library for PII protection.

This package provides the core detection and masking functionality
shared between the Aegis API and SDK.

Example:
    >>> from aegis_core import detect, mask_text
    >>> items = detect("Email: john@example.com")
    >>> print(items[0].type, items[0].count)
    EMAIL 1
    >>> masked = mask_text("Email: john@example.com")
    >>> print(masked)
    Email: j***@example.com
"""

from aegis_core.types import (
    Decision,
    Destination,
    DetectedItem,
    DetectionType,
    Finding,
    PII_TYPES,
    is_pii_type,
    is_phi_type,
)

from aegis_core.detector import (
    PATTERNS,
    PHI_KEYWORDS,
    PatternDetector,
    aggregate_findings,
    detect,
    detect_patterns,
    get_pii_types,
    has_detection_type,
    has_phi,
    has_pii,
    mask_sample,
)

from aegis_core.masker import (
    Masker,
    mask_api_secret,
    mask_credit_card,
    mask_email,
    mask_iban,
    mask_phone,
    mask_ssn,
    mask_text,
    mask_text_reversible,
    mask_value,
    unmask_text,
)

from aegis_core.validators import (
    is_valid_email_format,
    is_valid_phone_format,
    is_valid_ssn_format,
    luhn_check,
    validate_iban_checksum,
)

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("aegis-preflight-core")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"  # Fallback for development

__all__ = [
    # Version
    "__version__",
    # Types
    "Decision",
    "Destination",
    "DetectedItem",
    "DetectionType",
    "Finding",
    "PII_TYPES",
    "is_pii_type",
    "is_phi_type",
    # Detection
    "PATTERNS",
    "PHI_KEYWORDS",
    "PatternDetector",
    "aggregate_findings",
    "detect",
    "detect_patterns",
    "get_pii_types",
    "has_detection_type",
    "has_phi",
    "has_pii",
    "mask_sample",
    # Masking
    "Masker",
    "mask_api_secret",
    "mask_credit_card",
    "mask_email",
    "mask_iban",
    "mask_phone",
    "mask_ssn",
    "mask_text",
    "mask_text_reversible",
    "mask_value",
    "unmask_text",
    # Validators
    "is_valid_email_format",
    "is_valid_phone_format",
    "is_valid_ssn_format",
    "luhn_check",
    "validate_iban_checksum",
]
