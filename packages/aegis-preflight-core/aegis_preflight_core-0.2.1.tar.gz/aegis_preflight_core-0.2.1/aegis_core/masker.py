"""Sensitive data masking module.

This module provides format-preserving masking for detected sensitive
data. It is the unified masking engine used by both the Aegis API and SDK.
"""

import re
import uuid
from typing import Optional

from aegis_core.types import DetectionType, Finding
from aegis_core.detector import detect_patterns


def mask_email(email: str) -> str:
    """Mask an email address preserving format.

    Args:
        email: The email address to mask

    Returns:
        Masked email (e.g., "j***@example.com")
    """
    if "@" not in email:
        return "***@***.***"

    local, domain = email.split("@", 1)
    if len(local) > 0:
        return f"{local[0]}***@{domain}"
    return f"***@{domain}"


def mask_phone(phone: str) -> str:
    """Mask a phone number preserving format.

    Args:
        phone: The phone number to mask

    Returns:
        Masked phone (e.g., "XXX-XXX-4567")
    """
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) >= 4:
        return f"XXX-XXX-{digits[-4:]}"
    return "XXX-XXX-XXXX"


def mask_credit_card(card: str) -> str:
    """Mask a credit card number preserving format.

    Args:
        card: The credit card number to mask

    Returns:
        Masked card (e.g., "XXXX-XXXX-XXXX-1234")
    """
    digits = "".join(c for c in card if c.isdigit())
    if len(digits) >= 4:
        return f"XXXX-XXXX-XXXX-{digits[-4:]}"
    return "XXXX-XXXX-XXXX-XXXX"


def mask_ssn(ssn: str) -> str:
    """Mask a Social Security Number.

    Args:
        ssn: The SSN to mask

    Returns:
        Masked SSN (e.g., "XXX-XX-6789")
    """
    digits = "".join(c for c in ssn if c.isdigit())
    if len(digits) >= 4:
        return f"XXX-XX-{digits[-4:]}"
    return "XXX-XX-XXXX"


def mask_api_secret(secret: str) -> str:
    """Mask an API secret/key.

    Args:
        secret: The API secret to mask

    Returns:
        Masked secret showing only last 4 chars
    """
    if len(secret) > 4:
        return f"***{secret[-4:]}"
    return "****"


def mask_iban(iban: str) -> str:
    """Mask an IBAN.

    Args:
        iban: The IBAN to mask

    Returns:
        Masked IBAN (e.g., "DE**************1234")
    """
    if len(iban) > 6:
        return f"{iban[:2]}**************{iban[-4:]}"
    return "****"


def mask_value(value: str, detection_type: str) -> str:
    """Mask a detected value based on its type.

    Args:
        value: The value to mask
        detection_type: The type of sensitive data

    Returns:
        Appropriately masked value
    """
    if detection_type == DetectionType.EMAIL:
        return mask_email(value)
    elif detection_type == DetectionType.PHONE:
        return mask_phone(value)
    elif detection_type == DetectionType.CREDIT_CARD:
        return mask_credit_card(value)
    elif detection_type == DetectionType.SSN:
        return mask_ssn(value)
    elif detection_type == DetectionType.API_SECRET:
        return mask_api_secret(value)
    elif detection_type == DetectionType.IBAN:
        return mask_iban(value)
    elif detection_type == DetectionType.PHI_KEYWORD:
        # PHI keywords are context, not PII - return as-is
        return value
    else:
        # Default masking
        if len(value) > 2:
            return f"{value[:2]}***"
        return "***"


def mask_text(text: str, findings: Optional[list[Finding]] = None) -> str:
    """Mask all sensitive data in text.

    Detects and masks all sensitive data in the input text,
    replacing each occurrence with its masked equivalent.

    Args:
        text: The text to mask
        findings: Optional pre-computed findings (if None, will detect)

    Returns:
        Text with all sensitive data masked
    """
    if findings is None:
        findings = detect_patterns(text)

    if not findings:
        return text

    # Sort findings by position (reverse order for replacement)
    sorted_findings = sorted(findings, key=lambda f: f.start, reverse=True)

    result = text
    for finding in sorted_findings:
        masked = mask_value(finding.value, finding.detection_type)
        result = result[:finding.start] + masked + result[finding.end:]

    return result


def mask_text_reversible(
    text: str, findings: Optional[list[Finding]] = None
) -> tuple[str, dict[str, str]]:
    """Mask text with ability to reverse the masking.

    Creates unique placeholder tokens for each sensitive value,
    allowing the original values to be restored later.

    Args:
        text: The text to mask
        findings: Optional pre-computed findings

    Returns:
        Tuple of (masked_text, mask_map) where mask_map maps
        placeholders to original values

    Example:
        masked, mapping = mask_text_reversible("Email: john@test.com")
        # masked = "Email: [AEGIS_EMAIL_abc123]"
        # mapping = {"[AEGIS_EMAIL_abc123]": "john@test.com"}
    """
    if findings is None:
        findings = detect_patterns(text)

    if not findings:
        return text, {}

    mask_map: dict[str, str] = {}

    # Sort findings by position (reverse order for replacement)
    sorted_findings = sorted(findings, key=lambda f: f.start, reverse=True)

    result = text
    for finding in sorted_findings:
        # Create unique placeholder - use .value if enum, else string
        type_str = finding.detection_type.value if hasattr(finding.detection_type, 'value') else finding.detection_type
        token = f"[AEGIS_{type_str}_{uuid.uuid4().hex[:8]}]"
        mask_map[token] = finding.value
        result = result[:finding.start] + token + result[finding.end:]

    return result, mask_map


def unmask_text(text: str, mask_map: dict[str, str]) -> str:
    """Restore original values from masked text.

    Args:
        text: The masked text
        mask_map: Mapping of placeholders to original values

    Returns:
        Text with original values restored
    """
    result = text
    for placeholder, original in mask_map.items():
        result = result.replace(placeholder, original)
    return result


class Masker:
    """Masker class for object-oriented usage.

    This class wraps the module-level functions for use in contexts
    where an instantiated object is preferred.

    Example:
        masker = Masker()
        masked = masker.mask_text("Contact john@example.com")
    """

    def mask_text(self, text: str) -> str:
        """Mask all sensitive data in text.

        Args:
            text: The text to mask

        Returns:
            Text with sensitive data masked
        """
        return mask_text(text)

    def mask_value(self, value: str, detection_type: str) -> str:
        """Mask a single value.

        Args:
            value: The value to mask
            detection_type: The type of detection

        Returns:
            Masked value
        """
        return mask_value(value, detection_type)

    def mask_text_reversible(
        self, text: str
    ) -> tuple[str, dict[str, str]]:
        """Mask text with ability to reverse.

        Args:
            text: The text to mask

        Returns:
            Tuple of (masked_text, mask_map)
        """
        return mask_text_reversible(text)

    def unmask_text(self, text: str, mask_map: dict[str, str]) -> str:
        """Restore original values.

        Args:
            text: The masked text
            mask_map: Mapping from mask_text_reversible

        Returns:
            Text with originals restored
        """
        return unmask_text(text, mask_map)
