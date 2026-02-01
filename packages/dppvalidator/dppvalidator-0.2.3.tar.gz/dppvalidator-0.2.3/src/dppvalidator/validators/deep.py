"""Deep/Recursive validation for Digital Product Passports.

This module provides async crawling and validation of linked DPP documents,
enabling full supply chain traceability validation.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

from dppvalidator.logging import get_logger
from dppvalidator.validators.results import ValidationError, ValidationResult

logger = get_logger(__name__)


# Default link paths to follow in DPP documents
DEFAULT_LINK_PATHS = [
    "credentialSubject.traceabilityEvents",
    "credentialSubject.conformityClaim",
    "credentialSubject.product.traceabilityInfo",
    "credentialSubject.materialsProvenance",
]


@dataclass
class LinkInfo:
    """Information about a discovered link."""

    url: str
    path: str
    depth: int
    parent_url: str | None = None


@dataclass
class DeepValidationResult:
    """Result of deep/recursive validation.

    Attributes:
        root_result: Validation result for the root document
        link_graph: Map of URL to ValidationResult for all fetched documents
        visited_urls: Set of all visited URLs
        failed_urls: Map of URL to error message for failed fetches
        total_documents: Total number of documents processed
        max_depth_reached: Maximum depth reached during traversal
        cycle_detected: Whether any cycles were detected
        elapsed_time_ms: Total time for deep validation

    """

    root_result: ValidationResult
    link_graph: dict[str, ValidationResult] = field(default_factory=dict)
    visited_urls: set[str] = field(default_factory=set)
    failed_urls: dict[str, str] = field(default_factory=dict)
    total_documents: int = 1
    max_depth_reached: int = 0
    cycle_detected: bool = False
    elapsed_time_ms: float = 0.0

    @property
    def valid(self) -> bool:
        """Check if all validated documents are valid."""
        if not self.root_result.valid:
            return False
        return all(r.valid for r in self.link_graph.values())

    @property
    def all_errors(self) -> list[tuple[str, ValidationError]]:
        """Get all errors from all documents with their source URL."""
        errors = [("root", e) for e in self.root_result.errors]
        for url, result in self.link_graph.items():
            errors.extend((url, e) for e in result.errors)
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "root_result": self.root_result.to_dict(),
            "link_graph": {url: r.to_dict() for url, r in self.link_graph.items()},
            "visited_urls": list(self.visited_urls),
            "failed_urls": self.failed_urls,
            "total_documents": self.total_documents,
            "max_depth_reached": self.max_depth_reached,
            "cycle_detected": self.cycle_detected,
            "elapsed_time_ms": self.elapsed_time_ms,
        }


@dataclass
class RateLimiter:
    """Simple rate limiter for HTTP requests."""

    requests_per_second: float = 10.0
    _last_request_time: float = field(default=0.0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    async def acquire(self) -> None:
        """Wait until a request can be made."""
        async with self._lock:
            now = time.monotonic()
            min_interval = 1.0 / self.requests_per_second
            elapsed = now - self._last_request_time

            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

            self._last_request_time = time.monotonic()


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number."""
        delay = self.base_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


class DeepValidator:
    """Async crawler for deep/recursive DPP validation.

    Follows links in DPP documents and validates each linked document,
    building a complete validation graph of the supply chain.
    """

    def __init__(
        self,
        validator_factory: Callable[[], Any] | None = None,
        max_depth: int = 3,
        follow_links: list[str] | None = None,
        rate_limiter: RateLimiter | None = None,
        retry_config: RetryConfig | None = None,
        timeout: float = 30.0,
        auth_header: dict[str, str] | None = None,
    ) -> None:
        """Initialize the deep validator.

        Args:
            validator_factory: Factory to create ValidationEngine instances
            max_depth: Maximum depth to traverse (0 = root only)
            follow_links: JSON paths to follow for links
            rate_limiter: Rate limiter for HTTP requests
            retry_config: Retry configuration for failed requests
            timeout: HTTP request timeout in seconds
            auth_header: Authorization headers for requests

        """
        self._validator_factory = validator_factory
        self.max_depth = max_depth
        self.follow_links = follow_links or DEFAULT_LINK_PATHS
        self.rate_limiter = rate_limiter or RateLimiter()
        self.retry_config = retry_config or RetryConfig()
        self.timeout = timeout
        self.auth_header = auth_header or {}

        # State for current validation run
        self._visited: set[str] = set()
        self._pending: asyncio.Queue[LinkInfo] = asyncio.Queue()
        self._results: dict[str, ValidationResult] = {}
        self._failed: dict[str, str] = {}
        self._cycle_detected = False
        self._max_depth_reached = 0

    async def validate(
        self,
        root_data: dict[str, Any],
        root_url: str | None = None,
    ) -> DeepValidationResult:
        """Perform deep validation starting from root document.

        Args:
            root_data: The root DPP document data
            root_url: Optional URL of the root document (for cycle detection)

        Returns:
            DeepValidationResult with all validation results

        """
        start_time = time.monotonic()

        # Reset state
        self._visited = set()
        self._results = {}
        self._failed = {}
        self._cycle_detected = False
        self._max_depth_reached = 0

        # Create validator
        if self._validator_factory:
            validator = self._validator_factory()
        else:
            from dppvalidator.validators.engine import ValidationEngine

            validator = ValidationEngine()

        # Validate root document
        root_result = validator.validate(root_data)

        # Mark root as visited
        if root_url:
            self._visited.add(root_url)

        # Extract and queue links from root
        links = self._extract_links(root_data, depth=0, parent_url=root_url)
        for link in links:
            if link.url not in self._visited:
                await self._pending.put(link)

        # Process queue
        await self._process_queue(validator)

        elapsed = (time.monotonic() - start_time) * 1000

        return DeepValidationResult(
            root_result=root_result,
            link_graph=self._results,
            visited_urls=self._visited,
            failed_urls=self._failed,
            total_documents=1 + len(self._results),
            max_depth_reached=self._max_depth_reached,
            cycle_detected=self._cycle_detected,
            elapsed_time_ms=elapsed,
        )

    async def _process_queue(self, validator: Any) -> None:
        """Process the pending links queue."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while not self._pending.empty():
                link = await self._pending.get()

                # Check depth limit
                if link.depth > self.max_depth:
                    continue

                # Check for cycles
                if link.url in self._visited:
                    self._cycle_detected = True
                    continue

                # Track max depth
                self._max_depth_reached = max(self._max_depth_reached, link.depth)

                # Mark as visited
                self._visited.add(link.url)

                # Fetch and validate
                try:
                    data = await self._fetch_with_retry(client, link.url)
                    if data:
                        result = validator.validate(data)
                        self._results[link.url] = result

                        # Extract and queue more links
                        new_links = self._extract_links(
                            data,
                            depth=link.depth + 1,
                            parent_url=link.url,
                        )
                        for new_link in new_links:
                            if new_link.url not in self._visited:
                                await self._pending.put(new_link)

                except Exception as e:
                    self._failed[link.url] = str(e)
                    logger.warning("Failed to process %s: %s", link.url, e)

    async def _fetch_with_retry(
        self,
        client: Any,
        url: str,
    ) -> dict[str, Any] | None:
        """Fetch a URL with rate limiting and retries."""
        for attempt in range(self.retry_config.max_retries):
            try:
                # Rate limit
                await self.rate_limiter.acquire()

                # Make request
                headers = {"Accept": "application/json", **self.auth_header}
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503):
                    # Rate limited or service unavailable - retry
                    delay = self.retry_config.get_delay(attempt)
                    logger.debug("Rate limited, retrying in %.1fs", delay)
                    await asyncio.sleep(delay)
                else:
                    # Other HTTP error - don't retry
                    raise

            except httpx.RequestError:
                # Network error - retry
                delay = self.retry_config.get_delay(attempt)
                await asyncio.sleep(delay)

        return None

    def _extract_links(
        self,
        data: dict[str, Any],
        depth: int,
        parent_url: str | None = None,
    ) -> list[LinkInfo]:
        """Extract links from a DPP document based on configured paths."""
        links = []

        for path in self.follow_links:
            urls = self._get_urls_at_path(data, path)
            for url in urls:
                if self._is_valid_url(url):
                    links.append(
                        LinkInfo(
                            url=url,
                            path=path,
                            depth=depth + 1,
                            parent_url=parent_url,
                        )
                    )

        return links

    def _get_urls_at_path(self, data: dict[str, Any], path: str) -> list[str]:
        """Get URLs from a JSON path in the data."""
        urls = []
        parts = path.split(".")
        current = data

        for part in parts:
            if current is None:
                break
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                # Handle arrays - collect from all items
                results = []
                for item in current:
                    if isinstance(item, dict):
                        val = item.get(part)
                        if val is not None:
                            results.append(val)
                current = results if results else None
            else:
                current = None

        # Extract URLs from the final value
        if current is not None:
            urls.extend(self._extract_urls_from_value(current))

        return urls

    def _extract_urls_from_value(self, value: Any) -> list[str]:
        """Extract URLs from a value (string, dict, or list)."""
        urls = []

        if isinstance(value, str):
            if self._is_valid_url(value):
                urls.append(value)
        elif isinstance(value, dict):
            # Check common URL fields
            for key in ("id", "url", "href", "linkURL", "linkUrl"):
                if key in value and isinstance(value[key], str) and self._is_valid_url(value[key]):
                    urls.append(value[key])
                    break
        elif isinstance(value, list):
            for item in value:
                urls.extend(self._extract_urls_from_value(item))

        return urls

    def _is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid HTTP(S) URL."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False


async def validate_deep(
    data: dict[str, Any],
    max_depth: int = 3,
    follow_links: list[str] | None = None,
    timeout: float = 30.0,
    auth_header: dict[str, str] | None = None,
) -> DeepValidationResult:
    """Perform deep validation with default settings.

    Args:
        data: Root DPP document data
        max_depth: Maximum depth to traverse
        follow_links: JSON paths to follow for links
        timeout: HTTP request timeout
        auth_header: Authorization headers

    Returns:
        DeepValidationResult

    """
    validator = DeepValidator(
        max_depth=max_depth,
        follow_links=follow_links,
        timeout=timeout,
        auth_header=auth_header,
    )
    return await validator.validate(data)
