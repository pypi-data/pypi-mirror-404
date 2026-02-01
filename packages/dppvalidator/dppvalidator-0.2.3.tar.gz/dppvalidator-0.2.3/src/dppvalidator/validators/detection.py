"""Schema version auto-detection from DPP data."""

from __future__ import annotations

import re
from typing import Any

from dppvalidator.schemas.registry import DEFAULT_SCHEMA_VERSION, SCHEMA_REGISTRY

# Patterns for extracting version from URLs
_SCHEMA_URL_PATTERN = re.compile(r"untp-dpp-schema-(\d+\.\d+\.\d+)\.json")
_CONTEXT_URL_PATTERN = re.compile(r"/untp/dpp/(\d+\.\d+\.\d+)/?")

# Expected types for UNTP DPP
_DPP_TYPES = frozenset({"DigitalProductPassport", "VerifiableCredential"})


def detect_schema_version(data: dict[str, Any]) -> str:
    """Detect UNTP DPP schema version from data.

    Detection priority:
    1. `$schema` URL (explicit schema reference)
    2. `@context` URLs (JSON-LD context with version)
    3. `type` array (confirms DPP, uses default version)
    4. Falls back to default version

    Args:
        data: Raw DPP JSON data

    Returns:
        Detected schema version string (e.g., "0.6.1")
    """
    # Priority 1: Check $schema URL
    version = _detect_from_schema_url(data)
    if version:
        return version

    # Priority 2: Check @context URLs
    version = _detect_from_context(data)
    if version:
        return version

    # Priority 3: Check type array for DPP marker, use default
    if _is_dpp_type(data):
        return DEFAULT_SCHEMA_VERSION

    # Fallback to default
    return DEFAULT_SCHEMA_VERSION


def _detect_from_schema_url(data: dict[str, Any]) -> str | None:
    """Extract version from $schema URL.

    Args:
        data: Raw DPP JSON data

    Returns:
        Version string or None if not found/invalid
    """
    schema_url = data.get("$schema")
    if not isinstance(schema_url, str):
        return None

    match = _SCHEMA_URL_PATTERN.search(schema_url)
    if match:
        version = match.group(1)
        if version in SCHEMA_REGISTRY:
            return version

    return None


def _detect_from_context(data: dict[str, Any]) -> str | None:
    """Extract version from @context URLs.

    Args:
        data: Raw DPP JSON data

    Returns:
        Version string or None if not found/invalid
    """
    context = data.get("@context")
    if context is None:
        return None

    # Normalize to list
    if isinstance(context, str):
        urls = [context]
    elif isinstance(context, list):
        urls = [u for u in context if isinstance(u, str)]
    else:
        return None

    # Search for version pattern in any context URL
    for url in urls:
        match = _CONTEXT_URL_PATTERN.search(url)
        if match:
            version = match.group(1)
            if version in SCHEMA_REGISTRY:
                return version

    return None


def _is_dpp_type(data: dict[str, Any]) -> bool:
    """Check if data has DigitalProductPassport type.

    Args:
        data: Raw DPP JSON data

    Returns:
        True if type array contains DigitalProductPassport
    """
    type_value = data.get("type")
    if type_value is None:
        return False

    if isinstance(type_value, str):
        return type_value in _DPP_TYPES

    if isinstance(type_value, list):
        return any(t in _DPP_TYPES for t in type_value if isinstance(t, str))

    return False


def is_dpp_document(data: dict[str, Any]) -> bool:
    """Check if data appears to be a Digital Product Passport.

    Checks for presence of:
    - `type` containing "DigitalProductPassport"
    - `@context` with UNTP vocabulary
    - `credentialSubject` field

    Args:
        data: Raw JSON data

    Returns:
        True if data appears to be a DPP
    """
    if not isinstance(data, dict):
        return False

    # Check for DPP type
    if _is_dpp_type(data):
        return True

    # Check for credentialSubject (VC structure)
    if "credentialSubject" in data:
        return True

    # Check for UNTP context
    context = data.get("@context")
    if context:
        context_str = str(context)
        if "untp" in context_str.lower() or "uncefact" in context_str.lower():
            return True

    return False
