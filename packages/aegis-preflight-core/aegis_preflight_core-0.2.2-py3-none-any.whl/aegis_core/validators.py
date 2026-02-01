"""Validation utilities for sensitive data detection.

This module provides validation functions used during detection,
such as the Luhn algorithm for credit card validation.
"""


def luhn_check(card_number: str) -> bool:
    """Validate credit card number using Luhn algorithm.

    The Luhn algorithm (also known as mod-10 algorithm) is a checksum
    formula used to validate credit card numbers, IMEI numbers, and
    other identification numbers.

    Args:
        card_number: The card number to validate (can contain spaces/dashes)

    Returns:
        True if valid according to Luhn algorithm, False otherwise

    Example:
        >>> luhn_check("4111-1111-1111-1111")
        True
        >>> luhn_check("1234-5678-9012-3456")
        False
    """
    # Extract only digits
    digits = [int(d) for d in card_number if d.isdigit()]

    # Valid credit card numbers are between 13 and 19 digits
    if len(digits) < 13 or len(digits) > 19:
        return False

    # Luhn algorithm
    total = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit

    return total % 10 == 0


def validate_iban_checksum(iban: str) -> bool:
    """Validate IBAN checksum.

    Validates the checksum of an International Bank Account Number
    using the ISO 13616 standard.

    Args:
        iban: The IBAN to validate (can contain spaces)

    Returns:
        True if valid IBAN checksum, False otherwise

    Note:
        This performs basic format and checksum validation.
        It does not verify the bank/branch codes.
    """
    # Remove spaces and convert to uppercase
    iban = iban.replace(" ", "").upper()

    # Basic length check (minimum 15, maximum 34)
    if len(iban) < 15 or len(iban) > 34:
        return False

    # Move first 4 characters to end
    rearranged = iban[4:] + iban[:4]

    # Convert letters to numbers (A=10, B=11, ..., Z=35)
    numeric = ""
    for char in rearranged:
        if char.isdigit():
            numeric += char
        elif char.isalpha():
            numeric += str(ord(char) - ord("A") + 10)
        else:
            return False

    # Check if modulo 97 equals 1
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def is_valid_email_format(email: str) -> bool:
    """Basic email format validation.

    Performs a simple check that the email has the expected format.
    This is not a comprehensive RFC 5322 validation.

    Args:
        email: The email address to validate

    Returns:
        True if the email has a valid basic format
    """
    if not email or "@" not in email:
        return False

    local, _, domain = email.partition("@")

    # Basic checks
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False

    return True


def is_valid_phone_format(phone: str) -> bool:
    """Basic phone number format validation.

    Checks that the phone number has a reasonable number of digits.

    Args:
        phone: The phone number to validate

    Returns:
        True if the phone has a valid format
    """
    digits = [c for c in phone if c.isdigit()]
    return 7 <= len(digits) <= 15


def is_valid_ssn_format(ssn: str) -> bool:
    """Validate US Social Security Number format.

    Checks basic SSN format rules (XXX-XX-XXXX).

    Args:
        ssn: The SSN to validate

    Returns:
        True if the SSN has a valid format
    """
    digits = [c for c in ssn if c.isdigit()]
    if len(digits) != 9:
        return False

    # Area number (first 3 digits) cannot be 000, 666, or 900-999
    area = int("".join(digits[:3]))
    if area == 0 or area == 666 or 900 <= area <= 999:
        return False

    # Group number (middle 2 digits) cannot be 00
    group = int("".join(digits[3:5]))
    if group == 0:
        return False

    # Serial number (last 4 digits) cannot be 0000
    serial = int("".join(digits[5:]))
    if serial == 0:
        return False

    return True
