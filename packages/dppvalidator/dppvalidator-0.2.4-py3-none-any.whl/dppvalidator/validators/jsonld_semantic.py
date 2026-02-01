"""JSON-LD semantic validation layer using PyLD expansion."""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

from pyld import jsonld
from pyld.jsonld import JsonLdError

from dppvalidator.logging import get_logger
from dppvalidator.validators.results import ValidationError, ValidationResult

logger = get_logger(__name__)

# UNTP/UNCEFACT context URL patterns
UNTP_CONTEXT_PATTERNS = (
    "uncefact.org",
    "untp",
    "w3.org/ns/credentials",
)


class CachingDocumentLoader:
    """Document loader with LRU caching for remote contexts.

    Reduces network overhead by caching fetched JSON-LD contexts.
    """

    def __init__(self, cache_size: int = 32, timeout: float = 10.0) -> None:
        """Initialize caching document loader.

        Args:
            cache_size: Maximum number of contexts to cache
            timeout: HTTP request timeout in seconds
        """
        self._cache_size = cache_size
        self._timeout = timeout
        self._cache: dict[str, dict[str, Any]] = {}

    def __call__(self, url: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        """Load a remote document, using cache if available.

        Args:
            url: URL to fetch
            options: PyLD loader options

        Returns:
            Document dict with 'document' key containing parsed JSON
        """
        if url in self._cache:
            logger.debug("Context cache hit: %s", url)
            return self._cache[url]

        # Use PyLD's default loader for actual fetching
        result = jsonld.get_document_loader()(url, options)

        # Cache the result (LRU eviction)
        if len(self._cache) >= self._cache_size:
            # Remove oldest entry
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        self._cache[url] = result
        logger.debug("Context cached: %s", url)
        return result

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._cache.clear()


class JSONLDValidator:
    """JSON-LD semantic validation using PyLD expansion.

    Validates that:
    1. @context is present and valid (JLD001)
    2. All terms resolve during expansion (JLD002)
    3. Custom terms use proper namespacing (JLD003)

    Uses PyLD's expansion algorithm to detect undefined terms.
    """

    name: str = "jsonld"
    layer: str = "jsonld"

    def __init__(
        self,
        schema_version: str = "0.6.1",
        strict: bool = False,
        cache_contexts: bool = True,
    ) -> None:
        """Initialize JSON-LD validator.

        Args:
            schema_version: UNTP DPP schema version
            strict: If True, undefined terms are errors instead of warnings
            cache_contexts: If True, cache fetched remote contexts
        """
        self.schema_version = schema_version
        self.strict = strict
        self._document_loader = CachingDocumentLoader() if cache_contexts else None

    def validate(self, data: dict[str, Any]) -> ValidationResult:
        """Validate JSON-LD semantics via expansion.

        Args:
            data: Raw DPP JSON data with @context

        Returns:
            ValidationResult with semantic violations
        """
        start_time = time.perf_counter()

        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # JLD001: Check @context presence
        context_result = self._validate_context_presence(data)
        if context_result:
            errors.append(context_result)
            # Cannot proceed without valid context
            return ValidationResult(
                valid=False,
                errors=errors,
                schema_version=self.schema_version,
                validation_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Perform expansion to detect undefined terms
        try:
            options: dict[str, Any] = {}
            if self._document_loader:
                options["documentLoader"] = self._document_loader

            expanded = jsonld.expand(data, options)

            # JLD002: Detect dropped/undefined terms
            dropped_terms = self._find_dropped_terms(data, expanded)
            for term, path in dropped_terms:
                violation = ValidationError(
                    path=path,
                    message=f"Term '{term}' not defined in @context, dropped during expansion",
                    code="JLD002",
                    layer="jsonld",
                    severity="error" if self.strict else "warning",
                    suggestion=f"Add '{term}' to @context or use a prefixed term",
                )
                if self.strict:
                    errors.append(violation)
                else:
                    warnings.append(violation)

            # JLD003: Check for unprefixed custom terms
            unprefixed = self._find_unprefixed_custom_terms(data)
            for term, path in unprefixed:
                warnings.append(
                    ValidationError(
                        path=path,
                        message=f"Custom term '{term}' lacks namespace prefix",
                        code="JLD003",
                        layer="jsonld",
                        severity="warning",
                        suggestion="Use prefixed terms like 'ex:customField' for custom extensions",
                    )
                )

        except JsonLdError as e:
            errors.append(
                ValidationError(
                    path="$['@context']",
                    message=f"JSON-LD expansion failed: {e}",
                    code="JLD001",
                    layer="jsonld",
                    severity="error",
                )
            )
        except Exception as e:
            # Network errors, timeouts, etc.
            warnings.append(
                ValidationError(
                    path="$['@context']",
                    message=f"JSON-LD context resolution failed: {e}",
                    code="JLD004",
                    layer="jsonld",
                    severity="warning",
                    suggestion="Check network connectivity or use offline mode",
                )
            )

        validation_time = (time.perf_counter() - start_time) * 1000

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            schema_version=self.schema_version,
            validation_time_ms=validation_time,
        )

    def _validate_context_presence(self, data: dict[str, Any]) -> ValidationError | None:
        """Validate @context is present and appears valid.

        Args:
            data: Raw JSON data

        Returns:
            ValidationError if invalid, None if valid
        """
        context = data.get("@context")

        if context is None:
            return ValidationError(
                path="$",
                message="Missing @context: JSON-LD documents require @context",
                code="JLD001",
                layer="jsonld",
                severity="error",
                suggestion="Add @context with UNTP vocabulary URL",
            )

        # Check if context contains UNTP/W3C vocabulary
        context_str = str(context).lower()
        has_untp = any(pattern in context_str for pattern in UNTP_CONTEXT_PATTERNS)

        if not has_untp:
            return ValidationError(
                path="$['@context']",
                message="@context missing UNTP/W3C vocabulary references",
                code="JLD001",
                layer="jsonld",
                severity="error",
                suggestion="Include 'https://www.w3.org/ns/credentials/v2' and UNTP vocabulary",
            )

        return None

    def _find_dropped_terms(
        self,
        original: dict[str, Any],
        expanded: list[dict[str, Any]],
    ) -> list[tuple[str, str]]:
        """Find terms that were dropped during expansion.

        When PyLD expands JSON-LD, terms not defined in @context are dropped.
        This detects those dropped terms.

        Args:
            original: Original JSON data
            expanded: Expanded JSON-LD (list of objects)

        Returns:
            List of (term_name, json_path) tuples for dropped terms
        """
        dropped: list[tuple[str, str]] = []

        # Get all keys from original (excluding JSON-LD keywords)
        original_keys = self._collect_keys(original, "$")

        # Get all expanded IRIs
        expanded_iris: set[str] = set()
        if expanded:
            self._collect_expanded_iris(expanded[0] if expanded else {}, expanded_iris)

        # Check which original keys didn't expand
        for key, path in original_keys:
            if key.startswith("@"):
                continue  # Skip JSON-LD keywords

            # Check if key or a term ending with this key exists in expanded
            key_expanded = any(
                iri.endswith(f"/{key}") or iri.endswith(f"#{key}") or key in iri
                for iri in expanded_iris
            )

            if not key_expanded and key not in ("type", "id"):
                # Also check if it's a standard term that maps to @type or @id
                dropped.append((key, path))

        return dropped

    def _collect_keys(
        self,
        obj: Any,
        path: str,
    ) -> list[tuple[str, str]]:
        """Recursively collect all keys from an object.

        Args:
            obj: Object to traverse
            path: Current JSON path

        Returns:
            List of (key, path) tuples
        """
        keys: list[tuple[str, str]] = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                key_path = f"{path}['{key}']" if not path.endswith("$") else f"$.{key}"
                if not key.startswith("@"):
                    keys.append((key, key_path))
                keys.extend(self._collect_keys(value, key_path))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                keys.extend(self._collect_keys(item, f"{path}[{i}]"))

        return keys

    def _collect_expanded_iris(self, obj: Any, iris: set[str]) -> None:
        """Collect all IRIs from expanded JSON-LD.

        Args:
            obj: Expanded JSON-LD object
            iris: Set to add IRIs to (mutated)
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.startswith("http://") or key.startswith("https://"):
                    iris.add(key)
                self._collect_expanded_iris(value, iris)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_expanded_iris(item, iris)

    def _find_unprefixed_custom_terms(
        self,
        data: dict[str, Any],
    ) -> list[tuple[str, str]]:
        """Find custom terms that lack namespace prefixes.

        Terms not in the standard UNTP vocabulary should use prefixes
        to avoid namespace pollution.

        Args:
            data: Original JSON data

        Returns:
            List of (term_name, json_path) tuples
        """
        # Standard UNTP/VC terms (not exhaustive, common ones)
        standard_terms = frozenset(
            {
                "type",
                "id",
                "@context",
                "@type",
                "@id",
                "credentialSubject",
                "issuer",
                "validFrom",
                "validUntil",
                "proof",
                "credentialStatus",
                "credentialSchema",
                "name",
                "description",
                "image",
                "product",
                "manufacturer",
                "facility",
                "conformityClaim",
                "materialsProvenance",
                "circularityScorecard",
                "emissionsScorecard",
                "traceabilityInformation",
                "guaranteedUntil",
                "granularityLevel",
                "serialNumber",
                "batchNumber",
                "productCategory",
                "dimensions",
                "characteristics",
                "value",
                "unit",
                "code",
                "schemeId",
                "schemeName",
                "massFraction",
                "recycledContent",
                "recyclableContent",
                "hazardous",
                "materialSafetyInformation",
                "carbonFootprint",
                "operationalScope",
                "originCountry",
                "materialCode",
                "materialName",
            }
        )

        unprefixed: list[tuple[str, str]] = []
        all_keys = self._collect_keys(data, "$")

        for key, path in all_keys:
            if key.startswith("@"):
                continue
            if key in standard_terms:
                continue
            # Check if prefixed (contains colon but not URL)
            if ":" in key and not key.startswith("http"):
                continue
            # Likely a custom unprefixed term
            unprefixed.append((key, path))

        return unprefixed


@lru_cache(maxsize=1)
def _get_default_validator() -> JSONLDValidator:
    """Get default JSON-LD validator instance."""
    return JSONLDValidator()


def validate_jsonld(data: dict[str, Any]) -> ValidationResult:
    """Convenience function for JSON-LD validation.

    Args:
        data: DPP JSON data

    Returns:
        ValidationResult
    """
    validator = _get_default_validator()
    return validator.validate(data)
