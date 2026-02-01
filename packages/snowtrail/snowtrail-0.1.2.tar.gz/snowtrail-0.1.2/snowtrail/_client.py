"""
Base HTTP client for Snowtrail Research API.

Internal module - use the Snowtrail class from snowtrail/__init__.py instead.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests


class SnowtrailError(Exception):
    """Base exception for Snowtrail SDK errors."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(SnowtrailError):
    """
    Raised when API key is invalid or missing.

    Common causes:
    - API key not provided
    - API key is invalid or expired
    - API key doesn't have access to the requested resource
    """

    pass


class RateLimitError(SnowtrailError):
    """
    Raised when rate limit is exceeded.

    The SDK automatically retries rate-limited requests with exponential backoff.
    This error is raised only after all retries are exhausted.
    """

    pass


class NotFoundError(SnowtrailError):
    """
    Raised when a resource is not found.

    Common causes:
    - Invalid endpoint path
    - Resource doesn't exist
    - Product ID is incorrect
    """

    pass


class APIError(SnowtrailError):
    """Raised for general API errors (server errors, network issues, etc.)."""

    pass


def _get_version() -> str:
    """Get the SDK version from the package."""
    try:
        from snowtrail import __version__

        return __version__
    except ImportError:
        return "0.1.0"


class HTTPClient:
    """
    Low-level HTTP client for Snowtrail API.

    Handles authentication, retries, and error handling.
    """

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
    INITIAL_BACKOFF = 1.0  # seconds
    MAX_BACKOFF = 30.0  # seconds

    def __init__(
        self,
        base_url: str = "https://api.snowtrail.ai",
        api_key: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize the HTTP client.

        Args:
            base_url: API base URL (default: https://api.snowtrail.ai)
            api_key: API key for authentication. If not provided, will check
                     SNOWTRAIL_API_KEY environment variable.
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        # Check environment variable if api_key not provided
        if api_key is None:
            api_key = os.environ.get("SNOWTRAIL_API_KEY")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": f"snowtrail-python/{_get_version()}",
            }
        )

        if api_key:
            self._session.headers.update({"x-api-key": api_key})

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """
        Make a GET request to the API with automatic retries.

        Args:
            path: API endpoint path (e.g., "/gbsi_us/system_stress")
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: If API key is invalid
            RateLimitError: If rate limit exceeded after retries
            NotFoundError: If resource not found
            APIError: For other API errors
        """
        url = f"{self.base_url}{path}"

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        last_error: Exception | None = None
        backoff = self.INITIAL_BACKOFF

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self._session.get(url, params=params, timeout=self.timeout)

                # Check if we should retry
                if response.status_code in self.RETRY_STATUS_CODES and attempt < self.MAX_RETRIES:
                    # For rate limits, check Retry-After header
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            try:
                                backoff = min(float(retry_after), self.MAX_BACKOFF)
                            except ValueError:
                                pass

                    time.sleep(backoff)
                    backoff = min(backoff * 2, self.MAX_BACKOFF)
                    continue

                return self._handle_response(response)

            except requests.exceptions.Timeout:
                last_error = APIError(
                    f"Request timed out after {self.timeout}s. "
                    "Try increasing the timeout or check your network connection."
                )
                if attempt < self.MAX_RETRIES:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, self.MAX_BACKOFF)
                    continue
                raise last_error from None

            except requests.exceptions.ConnectionError as e:
                # Extract the root cause for a cleaner message
                error_msg = str(e)
                if "NameResolutionError" in error_msg or "getaddrinfo failed" in error_msg:
                    last_error = APIError(
                        f"Could not connect to {self.base_url}. "
                        "Please check the URL and your network connection."
                    )
                elif "Connection refused" in error_msg:
                    last_error = APIError(
                        f"Connection refused by {self.base_url}. The service may be unavailable."
                    )
                else:
                    last_error = APIError(
                        f"Network error connecting to API. Please check your internet connection."
                    )

                if attempt < self.MAX_RETRIES:
                    time.sleep(backoff)
                    backoff = min(backoff * 2, self.MAX_BACKOFF)
                    continue
                raise last_error from None

        # Should not reach here, but just in case
        if last_error:
            raise last_error
        raise APIError("Request failed after retries")

    def _handle_response(self, response: requests.Response) -> Any:
        """Parse response and raise appropriate exceptions for errors."""
        if response.status_code == 200:
            return response.json()

        # Extract error detail from response
        detail = self._extract_error_detail(response)

        if response.status_code == 401:
            raise AuthenticationError(
                f"Invalid API key. Please check your credentials.",
                status_code=401,
                response=response,
            )
        elif response.status_code == 403:
            raise AuthenticationError(
                f"Access denied. Your API key may not have permission for this resource.",
                status_code=403,
                response=response,
            )
        elif response.status_code == 404:
            raise NotFoundError(
                f"Resource not found: {response.request.path_url}",
                status_code=404,
                response=response,
            )
        elif response.status_code == 429:
            raise RateLimitError(
                f"Rate limit exceeded. Please wait before making more requests.",
                status_code=429,
                response=response,
            )
        elif response.status_code >= 500:
            raise APIError(
                f"Server error ({response.status_code}). Please try again later.",
                status_code=response.status_code,
                response=response,
            )
        else:
            raise APIError(
                f"API error ({response.status_code}): {detail}",
                status_code=response.status_code,
                response=response,
            )

    def _extract_error_detail(self, response: requests.Response) -> str:
        """Extract a clean error message from the response."""
        try:
            error_data = response.json()
            # Handle various error response formats
            if isinstance(error_data, dict):
                # FastAPI format: {"detail": "message"}
                if "detail" in error_data:
                    detail = error_data["detail"]
                    if isinstance(detail, str):
                        return detail
                    elif isinstance(detail, list) and detail:
                        # Validation errors
                        return "; ".join(
                            f"{e.get('loc', ['?'])[-1]}: {e.get('msg', '?')}" for e in detail
                        )
                # API Gateway format: {"message": "Forbidden"}
                if "message" in error_data:
                    return error_data["message"]
            return str(error_data)
        except Exception:
            return response.text or response.reason or "Unknown error"

    def health(self, deep: bool = False) -> dict[str, Any]:
        """Check API health status."""
        params = {"deep": "true"} if deep else None
        return self.get("/health", params=params)

    def list_products(self) -> list[dict[str, Any]]:
        """List all available products."""
        return self.get("/products")
