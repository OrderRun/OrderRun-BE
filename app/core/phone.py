"""Phone normalization helpers."""

from __future__ import annotations


def normalize_phone(phone: str) -> str:
    """Normalize phone numbers for storage and lookup."""
    value = phone.strip().replace(" ", "").replace("-", "")
    if value.startswith("+82"):
        value = "0" + value[3:]
    return value
