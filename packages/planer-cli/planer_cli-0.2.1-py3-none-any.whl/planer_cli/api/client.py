"""Async HTTP client for Microsoft Graph API."""

import asyncio
import logging
from typing import Any

import httpx

from planer_cli.api.exceptions import (
    AuthenticationError,
    ETagMismatchError,
    PermissionDeniedError,
    PlannerAPIError,
    RateLimitError,
    ResourceNotFoundError,
)
from planer_cli.auth.manager import AuthManager
from planer_cli.config import get_settings

logger = logging.getLogger(__name__)


class GraphClient:
    """Async HTTP client for Microsoft Graph API with authentication."""

    def __init__(self, auth_manager: AuthManager | None = None) -> None:
        """Initialize the client.

        Args:
            auth_manager: AuthManager instance. Creates one if not provided.
        """
        self.settings = get_settings()
        self.auth_manager = auth_manager or AuthManager()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.settings.graph_endpoint,
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _get_headers(self, etag: str | None = None) -> dict[str, str]:
        """Get request headers with authentication.

        Args:
            etag: ETag for If-Match header (required for PATCH/DELETE).

        Returns:
            Headers dictionary.
        """
        token = self.auth_manager.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        if etag:
            headers["If-Match"] = etag
        return headers

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the API.

        Args:
            response: HTTP response.

        Raises:
            Appropriate exception based on status code.
        """
        status = response.status_code

        # Try to extract error message from response
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            message = error.get("message", response.text)
        except Exception:
            message = response.text or f"HTTP {status}"

        if status == 401:
            raise AuthenticationError(f"Authentication failed: {message}", status)
        elif status == 403:
            raise PermissionDeniedError(f"Permission denied: {message}")
        elif status == 404:
            raise ResourceNotFoundError(message)
        elif status == 409:
            raise ETagMismatchError(message)
        elif status == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            raise RateLimitError(f"Rate limited: {message}", retry_after)
        else:
            raise PlannerAPIError(message, status)

    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        etag: str | None = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        """Make a request with retry logic for rate limiting.

        Args:
            method: HTTP method.
            endpoint: API endpoint.
            data: Request body data.
            etag: ETag for If-Match header.
            max_retries: Maximum number of retries.

        Returns:
            HTTP response.

        Raises:
            RateLimitError: If rate limit exceeded after all retries.
        """
        client = await self._get_client()

        for attempt in range(max_retries):
            try:
                headers = self._get_headers(etag)

                if method == "GET":
                    response = await client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = await client.post(endpoint, headers=headers, json=data)
                elif method == "PATCH":
                    response = await client.patch(endpoint, headers=headers, json=data)
                elif method == "DELETE":
                    response = await client.delete(endpoint, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    if attempt < max_retries - 1:
                        wait_time = min(retry_after, 120)
                        logger.warning(
                            f"Rate limited. Waiting {wait_time}s before retry..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    raise RateLimitError(
                        "Rate limit exceeded after retries", retry_after
                    )

                return response

            except RateLimitError:
                raise
            except httpx.TimeoutException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Request timeout. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                raise PlannerAPIError(f"Request timeout: {e}")

        raise PlannerAPIError("Max retries exceeded")

    async def get(self, endpoint: str) -> dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint.

        Returns:
            Response data.
        """
        response = await self._request_with_retry("GET", endpoint)

        if response.status_code >= 400:
            self._handle_error_response(response)

        return response.json()

    async def post(
        self, endpoint: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint.
            data: Request body data.

        Returns:
            Response data.
        """
        response = await self._request_with_retry("POST", endpoint, data=data)

        if response.status_code >= 400:
            self._handle_error_response(response)

        return response.json()

    async def patch(
        self,
        endpoint: str,
        data: dict[str, Any],
        etag: str,
    ) -> dict[str, Any]:
        """Make a PATCH request.

        Args:
            endpoint: API endpoint.
            data: Request body data.
            etag: ETag for If-Match header (required for Planner API).

        Returns:
            Response data.
        """
        response = await self._request_with_retry(
            "PATCH", endpoint, data=data, etag=etag
        )

        if response.status_code >= 400:
            self._handle_error_response(response)

        # Handle empty response (204 No Content)
        if response.status_code == 204 or not response.content:
            return {}

        return response.json()

    async def delete(self, endpoint: str, etag: str) -> bool:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint.
            etag: ETag for If-Match header (required for Planner API).

        Returns:
            True if successful.
        """
        response = await self._request_with_retry("DELETE", endpoint, etag=etag)

        if response.status_code >= 400:
            self._handle_error_response(response)

        return response.status_code == 204
