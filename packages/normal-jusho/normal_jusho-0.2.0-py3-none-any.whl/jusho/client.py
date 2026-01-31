"""Synchronous client for the Jusho address normalization API.

Usage::

    from jusho import Jusho

    client = Jusho()
    result = client.normalize("東京都渋谷区道玄坂1-2-3")
    print(result.address.full)
    print(result.codes.post_code)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

import httpx

from .errors import (
    APIError,
    JushoError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .models import (
    BatchResult,
    NormalizeResult,
    PostalResult,
    ReverseResult,
    SuggestResult,
    ValidationResult,
    _parse_batch_result,
    _parse_normalize_result,
    _parse_postal_result,
    _parse_reverse_result,
    _parse_suggest_result,
    _parse_validation_result,
)

_DEFAULT_BASE_URL = "https://api.jusho.dev"
_DEFAULT_TIMEOUT = 10.0
_USER_AGENT = "jusho-python/0.1.0"


class Jusho:
    """Synchronous client for the Jusho API.

    Args:
        base_url: API base URL.  Defaults to ``https://api.jusho.dev``.
        timeout: Request timeout in seconds.  Defaults to ``10.0``.
        headers: Additional HTTP headers to include in every request.
        http_client: An existing :class:`httpx.Client` instance.  When
            provided, *base_url*, *timeout*, and *headers* are ignored and
            the caller is responsible for closing the client.

    Example::

        client = Jusho()
        result = client.normalize("東京都千代田区千代田1-1")
        print(result.codes.post_code)  # "1000001"
    """

    def __init__(
        self,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        self._owns_client = http_client is None
        if http_client is not None:
            self._client = http_client
        else:
            merged_headers = {"User-Agent": _USER_AGENT}
            if headers:
                merged_headers.update(headers)
            self._client = httpx.Client(
                base_url=base_url,
                timeout=timeout,
                headers=merged_headers,
            )

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "Jusho":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client.

        Only closes the client if it was created internally (i.e. not
        passed via *http_client*).
        """
        if self._owns_client:
            self._client.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def normalize(self, address: str) -> NormalizeResult:
        """Normalize a Japanese address string.

        Args:
            address: Raw Japanese address to normalize.

        Returns:
            A :class:`~jusho.models.NormalizeResult` containing the
            structured, normalized address.

        Raises:
            NotFoundError: If the address cannot be resolved.
            ValidationError: If the request is malformed.
            RateLimitError: If the API rate limit has been exceeded.
            NetworkError: On network-level failures.
            TimeoutError: If the request times out.
            APIError: On other unexpected API errors.
        """
        data = self._request("POST", "/normalize", json={"address": address})
        return _parse_normalize_result(data)

    def normalize_batch(self, addresses: Sequence[str]) -> BatchResult:
        """Normalize multiple addresses in a single request.

        Args:
            addresses: A list of raw Japanese address strings (max 100).

        Returns:
            A :class:`~jusho.models.BatchResult` containing per-address
            results.

        Raises:
            ValidationError: If the request is malformed or exceeds 100
                addresses.
            RateLimitError: If the API rate limit has been exceeded.
            NetworkError: On network-level failures.
            TimeoutError: If the request times out.
            APIError: On other unexpected API errors.
        """
        data = self._request(
            "POST", "/normalize/batch", json={"addresses": list(addresses)}
        )
        return _parse_batch_result(data)

    def postal(self, code: str) -> PostalResult:
        """Look up addresses by postal code.

        Args:
            code: A Japanese postal code (e.g. ``"1500043"``).

        Returns:
            A :class:`~jusho.models.PostalResult` with matching addresses.

        Raises:
            NotFoundError: If no addresses match the postal code.
            RateLimitError: If the API rate limit has been exceeded.
            NetworkError: On network-level failures.
            TimeoutError: If the request times out.
            APIError: On other unexpected API errors.
        """
        data = self._request("GET", f"/postal/{code}")
        return _parse_postal_result(data)

    def suggest(self, query: str) -> SuggestResult:
        """Get address suggestions for a partial query.

        Args:
            query: Partial address text for autocomplete.

        Returns:
            A :class:`~jusho.models.SuggestResult` containing matching
            address suggestions.

        Raises:
            RateLimitError: If the API rate limit has been exceeded.
            NetworkError: On network-level failures.
            TimeoutError: If the request times out.
            APIError: On other unexpected API errors.
        """
        data = self._request("GET", "/suggest", params={"q": query})
        return _parse_suggest_result(data)

    def validate(self, address: str) -> ValidationResult:
        """Validate whether an address is recognized.

        Args:
            address: Address string to validate.

        Returns:
            A :class:`~jusho.models.ValidationResult` indicating
            whether the address is valid.

        Raises:
            RateLimitError: If the API rate limit has been exceeded.
            NetworkError: On network-level failures.
            TimeoutError: If the request times out.
            APIError: On other unexpected API errors.
        """
        data = self._request("GET", "/validate", params={"address": address})
        return _parse_validation_result(data)

    def reverse(self, address: str) -> ReverseResult:
        """Reverse-lookup an address.

        Args:
            address: Address string to reverse-look up.

        Returns:
            A :class:`~jusho.models.ReverseResult` with resolved address
            details.

        Raises:
            NotFoundError: If the address cannot be resolved.
            RateLimitError: If the API rate limit has been exceeded.
            NetworkError: On network-level failures.
            TimeoutError: If the request times out.
            APIError: On other unexpected API errors.
        """
        data = self._request("GET", "/reverse", params={"address": address})
        return _parse_reverse_result(data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send an HTTP request and return the parsed JSON response.

        All API-level error handling is centralised here.
        """
        try:
            response = self._client.request(
                method, path, params=params, json=json
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"Request to {path} timed out") from exc
        except httpx.HTTPError as exc:
            raise NetworkError(f"Network error during request to {path}: {exc}") from exc

        return _handle_response(response, path)


def _handle_response(response: httpx.Response, path: str) -> Dict[str, Any]:
    """Inspect an HTTP response and raise appropriate errors or return JSON."""
    if response.is_success:
        return response.json()  # type: ignore[no-any-return]

    # Try to parse an error body
    body: Optional[Dict[str, Any]] = None
    try:
        body = response.json()
    except Exception:
        pass

    detail = ""
    if body:
        detail = body.get("detail", body.get("error", ""))

    status = response.status_code

    if status == 404:
        raise NotFoundError(detail or f"Not found: {path}", body=body)

    if status == 422:
        raise ValidationError(detail or "Validation error", body=body)

    if status == 429:
        retry_after: Optional[int] = None
        retry_header = response.headers.get("Retry-After")
        if retry_header is not None:
            try:
                retry_after = int(retry_header)
            except ValueError:
                pass
        raise RateLimitError(
            detail or "Rate limit exceeded",
            retry_after=retry_after,
            body=body,
        )

    raise APIError(
        detail or f"API error ({status})",
        status_code=status,
        body=body,
    )
