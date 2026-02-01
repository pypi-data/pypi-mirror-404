# Aegis Preflight Core

[![PyPI version](https://img.shields.io/pypi/v/aegis-preflight-core.svg)](https://pypi.org/project/aegis-preflight-core/)
[![Python versions](https://img.shields.io/pypi/pyversions/aegis-preflight-core.svg)](https://pypi.org/project/aegis-preflight-core/)

**Core detection and masking engine for PII protection.**

> **Note**: This is a dependency package. Install [`aegis-sdk`](https://pypi.org/project/aegis-sdk/) for the full SDK with LLM integrations and enterprise features.

## Installation

```bash
pip install aegis-sdk  # Recommended - includes this package
```

## Quick Example

```python
from aegis_core import detect, mask_text

# Detect PII
items = detect("Contact john@example.com at 555-123-4567")
# [DetectedItem(type='EMAIL', count=1), DetectedItem(type='PHONE', count=1)]

# Mask PII
masked = mask_text("Contact john@example.com at 555-123-4567")
# "Contact j***@example.com at XXX-XXX-4567"
```

## Detection Types

`EMAIL` | `PHONE` | `SSN` | `CREDIT_CARD` | `API_SECRET` | `IBAN` | `PHI_KEYWORD`

## License

Proprietary - [Aegis Preflight](https://www.aegispreflight.com/)
