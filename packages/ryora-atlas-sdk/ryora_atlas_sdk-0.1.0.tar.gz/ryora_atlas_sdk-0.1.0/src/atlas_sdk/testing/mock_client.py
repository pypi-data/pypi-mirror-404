"""Mock HTTP client for testing.

This module provides MockHTTPClient, a testing utility that implements
the HTTPClientProtocol interface. It allows you to configure mock responses
and record all HTTP requests for verification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Pattern, Self
from uuid import uuid4

import httpx

from atlas_sdk.exceptions import AtlasAPIError


@dataclass
class MockRequest:
    """Record of a request made to the mock client.

    Attributes:
        method: HTTP method (GET, POST, etc.)
        url: Request URL path
        headers: Request headers
        json_body: Parsed JSON body (if present)
        params: Query parameters
        request_id: X-Request-ID header value
    """

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    json_body: dict[str, Any] | None = None
    params: dict[str, Any] | None = None
    request_id: str | None = None


@dataclass
class MockResponse:
    """Configuration for a mock response.

    Attributes:
        status_code: HTTP status code to return
        json_body: JSON response body
        headers: Response headers
        raise_exception: Optional exception to raise instead of returning response
    """

    status_code: int = 200
    json_body: dict[str, Any] | list[Any] | None = None
    headers: dict[str, str] = field(default_factory=dict)
    raise_exception: Exception | None = None


class MockHTTPClient:
    """Mock HTTP client for testing Atlas SDK clients.

    This client implements the HTTPClientProtocol interface and can be injected
    into SDK clients for testing. It allows you to:
    - Configure responses for specific URL patterns
    - Record all requests made for later verification
    - Simulate various error conditions

    The mock client supports:
    - Exact URL matching
    - Regex pattern matching
    - Response queues for the same endpoint
    - Exception simulation

    Example:
        ```python
        from atlas_sdk.testing import MockHTTPClient
        from atlas_sdk import ControlPlaneClient

        mock = MockHTTPClient()

        # Add a successful response
        mock.add_response("GET", "/api/v1/health", {"status": "healthy"})

        # Add a 404 error response
        mock.add_response("GET", "/api/v1/agent-classes/invalid", status_code=404)

        # Use with the real client
        client = ControlPlaneClient(base_url="http://test", http_client=mock)
        async with client:
            result = await client.health()

        # Verify requests were made
        assert len(mock.requests) == 1
        assert mock.requests[0].method == "GET"
        assert mock.requests[0].url == "/api/v1/health"
        ```

    Example with regex patterns:
        ```python
        import re
        mock = MockHTTPClient()

        # Match any UUID in the URL
        mock.add_response(
            "GET",
            re.compile(r"/api/v1/agent-classes/[a-f0-9-]+"),
            {"id": "...", "name": "TestClass"}
        )
        ```

    Example with response queues:
        ```python
        mock = MockHTTPClient()

        # First call returns 503, second returns success
        mock.add_response("GET", "/api/v1/health", status_code=503)
        mock.add_response("GET", "/api/v1/health", {"status": "healthy"})
        ```
    """

    def __init__(self, base_url: str = "http://mock-service") -> None:
        """Initialize the mock client.

        Args:
            base_url: Base URL for the mock service (used for logging/debugging)
        """
        self.base_url = base_url
        self._responses: list[tuple[str, str | Pattern[str], MockResponse]] = []
        self._requests: list[MockRequest] = []
        self._default_response: MockResponse | None = None
        self._closed = False

    @property
    def requests(self) -> list[MockRequest]:
        """Get all recorded requests.

        Returns:
            List of MockRequest objects in order they were made.
        """
        return self._requests.copy()

    def add_response(
        self,
        method: str,
        url_pattern: str | Pattern[str],
        json_body: dict[str, Any] | list[Any] | None = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> MockHTTPClient:
        """Add a mock response for a specific request.

        Responses are matched in LIFO order (last added, first matched).
        Once a response is matched, it is removed from the queue.

        Args:
            method: HTTP method to match (GET, POST, etc.)
            url_pattern: URL path to match (exact string or regex pattern)
            json_body: JSON response body
            status_code: HTTP status code (default 200)
            headers: Additional response headers

        Returns:
            Self for method chaining.

        Example:
            ```python
            mock.add_response("GET", "/api/v1/health", {"status": "ok"})
            mock.add_response("POST", "/api/v1/agent-classes", {"id": "..."}, status_code=201)
            ```
        """
        response = MockResponse(
            status_code=status_code,
            json_body=json_body,
            headers=headers or {},
        )
        self._responses.append((method.upper(), url_pattern, response))
        return self

    def add_error_response(
        self,
        method: str,
        url_pattern: str | Pattern[str],
        status_code: int,
        detail: str = "Error",
    ) -> MockHTTPClient:
        """Add a mock error response.

        This is a convenience method for adding error responses with a
        standard error body format.

        Args:
            method: HTTP method to match
            url_pattern: URL path to match
            status_code: HTTP error status code (4xx or 5xx)
            detail: Error message detail

        Returns:
            Self for method chaining.
        """
        return self.add_response(
            method,
            url_pattern,
            {"detail": detail},
            status_code=status_code,
        )

    def add_exception(
        self,
        method: str,
        url_pattern: str | Pattern[str],
        exception: Exception,
    ) -> MockHTTPClient:
        """Add a mock that raises an exception.

        Use this to simulate network errors, timeouts, etc.

        Args:
            method: HTTP method to match
            url_pattern: URL path to match
            exception: Exception to raise when matched

        Returns:
            Self for method chaining.

        Example:
            ```python
            import httpx
            mock.add_exception("GET", "/api/v1/health", httpx.ConnectError("Connection refused"))
            ```
        """
        response = MockResponse(raise_exception=exception)
        self._responses.append((method.upper(), url_pattern, response))
        return self

    def set_default_response(
        self,
        json_body: dict[str, Any] | list[Any] | None = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
    ) -> MockHTTPClient:
        """Set a default response for unmatched requests.

        By default, unmatched requests raise an error. This method allows
        you to set a fallback response.

        Args:
            json_body: Default JSON response body
            status_code: Default HTTP status code
            headers: Default response headers

        Returns:
            Self for method chaining.
        """
        self._default_response = MockResponse(
            status_code=status_code,
            json_body=json_body,
            headers=headers or {},
        )
        return self

    def clear(self) -> None:
        """Clear all recorded requests and configured responses."""
        self._responses.clear()
        self._requests.clear()
        self._default_response = None

    def reset_requests(self) -> None:
        """Clear only recorded requests, keeping configured responses."""
        self._requests.clear()

    def _find_response(self, method: str, url: str) -> MockResponse | None:
        """Find and remove a matching response.

        Args:
            method: HTTP method
            url: Request URL path

        Returns:
            Matching MockResponse or None if no match found.
        """
        for i in range(len(self._responses) - 1, -1, -1):
            resp_method, url_pattern, response = self._responses[i]
            if resp_method != method.upper():
                continue

            if isinstance(url_pattern, str):
                if url_pattern == url:
                    self._responses.pop(i)
                    return response
            else:
                # Regex pattern
                if url_pattern.match(url):
                    self._responses.pop(i)
                    return response

        return self._default_response

    async def _request(
        self,
        method: str,
        url: str,
        request_id: str | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make a mock HTTP request.

        This method implements the HTTPClientProtocol interface.

        Args:
            method: HTTP method
            url: Request URL path
            request_id: Optional request ID for tracing
            **kwargs: Additional request arguments (json, params, headers)

        Returns:
            Mock httpx.Response object

        Raises:
            ValueError: If no matching response is configured
            Exception: If the matching response is configured to raise an exception
        """
        if self._closed:
            raise RuntimeError("Mock client is closed")

        # Record the request
        headers = kwargs.get("headers", {})
        if request_id is None:
            request_id = headers.get("X-Request-ID", str(uuid4()))

        mock_request = MockRequest(
            method=method.upper(),
            url=url,
            headers=headers,
            json_body=kwargs.get("json"),
            params=kwargs.get("params"),
            request_id=request_id,
        )
        self._requests.append(mock_request)

        # Find matching response
        response = self._find_response(method, url)
        if response is None:
            raise ValueError(
                f"No mock response configured for {method.upper()} {url}. "
                f"Recorded requests: {[f'{r.method} {r.url}' for r in self._requests]}"
            )

        if response.raise_exception is not None:
            raise response.raise_exception

        # Build response
        response_headers = {
            "content-type": "application/json",
            "x-request-id": request_id,
            **response.headers,
        }

        content = b""
        if response.json_body is not None:
            content = json.dumps(response.json_body).encode()
            response_headers["content-length"] = str(len(content))

        # Create httpx.Response
        return httpx.Response(
            status_code=response.status_code,
            headers=response_headers,
            content=content,
            request=httpx.Request(method, f"{self.base_url}{url}"),
        )

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate Atlas error if response indicates failure.

        This method implements the HTTPClientProtocol interface.

        Args:
            response: The HTTP response to check

        Raises:
            AtlasAPIError: If the response indicates an error
        """
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise AtlasAPIError.from_response(response, e.request) from e

    async def __aenter__(self) -> Self:
        """Enter async context manager."""
        self._closed = False
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit async context manager."""
        self._closed = True

    async def close(self) -> None:
        """Close the mock client."""
        self._closed = True

    # Utility methods for common assertions

    def assert_request_made(
        self,
        method: str,
        url: str | Pattern[str],
        *,
        times: int | None = None,
    ) -> None:
        """Assert that a specific request was made.

        Args:
            method: HTTP method to check
            url: URL pattern to match (exact string or regex)
            times: If specified, assert exactly this many matching requests

        Raises:
            AssertionError: If the assertion fails
        """
        matching = self._count_matching_requests(method, url)

        if times is not None:
            if matching != times:
                raise AssertionError(
                    f"Expected {times} request(s) to {method} {url}, found {matching}"
                )
        elif matching == 0:
            raise AssertionError(
                f"Expected request to {method} {url}, but none found. "
                f"Recorded: {[f'{r.method} {r.url}' for r in self._requests]}"
            )

    def assert_no_requests(self) -> None:
        """Assert that no requests were made.

        Raises:
            AssertionError: If any requests were recorded
        """
        if self._requests:
            raise AssertionError(
                f"Expected no requests, but found: "
                f"{[f'{r.method} {r.url}' for r in self._requests]}"
            )

    def _count_matching_requests(self, method: str, url: str | Pattern[str]) -> int:
        """Count requests matching method and URL pattern."""
        count = 0
        for req in self._requests:
            if req.method != method.upper():
                continue
            if isinstance(url, str):
                if req.url == url:
                    count += 1
            else:
                if url.match(req.url):
                    count += 1
        return count

    def get_request_body(self, index: int = -1) -> dict[str, Any] | None:
        """Get the JSON body of a recorded request.

        Args:
            index: Request index (default -1 for last request)

        Returns:
            JSON body dict or None if no body

        Raises:
            IndexError: If index is out of range
        """
        return self._requests[index].json_body

    def get_last_request(self) -> MockRequest:
        """Get the last recorded request.

        Returns:
            The last MockRequest

        Raises:
            IndexError: If no requests were recorded
        """
        if not self._requests:
            raise IndexError("No requests recorded")
        return self._requests[-1]
