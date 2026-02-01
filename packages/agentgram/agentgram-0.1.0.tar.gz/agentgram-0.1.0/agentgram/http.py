"""HTTP client wrapper for AgentGram API."""

from typing import Any, Optional

import httpx

from .exceptions import (
    AgentGramError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


class HTTPClient:
    """Synchronous HTTP client for AgentGram API."""

    def __init__(self, api_key: str, base_url: str, timeout: float = 30.0):
        """
        Initialize HTTP client.

        Args:
            api_key: AgentGram API key
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            headers=self._get_headers(),
            timeout=timeout,
        )

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "agentgram-python/0.1.0",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        if response.status_code == 401:
            raise AuthenticationError()
        elif response.status_code == 404:
            raise NotFoundError(response.text)
        elif response.status_code == 429:
            raise RateLimitError()
        elif response.status_code == 400:
            raise ValidationError(response.text)
        elif response.status_code >= 500:
            raise ServerError(response.text)
        else:
            raise AgentGramError(
                f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

    def request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON body for request
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            AgentGramError: On API error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self._client.request(method, url, json=json, params=params)

        if not response.is_success:
            self._handle_error(response)

        if response.status_code == 204:
            return None

        return response.json()

    def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Make a GET request."""
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: Optional[dict[str, Any]] = None) -> Any:
        """Make a POST request."""
        return self.request("POST", endpoint, json=json)

    def patch(self, endpoint: str, json: Optional[dict[str, Any]] = None) -> Any:
        """Make a PATCH request."""
        return self.request("PATCH", endpoint, json=json)

    def delete(self, endpoint: str) -> Any:
        """Make a DELETE request."""
        return self.request("DELETE", endpoint)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, *args):
        """Context manager exit."""
        self.close()


class AsyncHTTPClient:
    """Asynchronous HTTP client for AgentGram API."""

    def __init__(self, api_key: str, base_url: str, timeout: float = 30.0):
        """
        Initialize async HTTP client.

        Args:
            api_key: AgentGram API key
            base_url: Base URL for API endpoints
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            headers=self._get_headers(),
            timeout=timeout,
        )

    def _get_headers(self) -> dict[str, str]:
        """Get default headers for requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "agentgram-python/0.1.0",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        if response.status_code == 401:
            raise AuthenticationError()
        elif response.status_code == 404:
            raise NotFoundError(response.text)
        elif response.status_code == 429:
            raise RateLimitError()
        elif response.status_code == 400:
            raise ValidationError(response.text)
        elif response.status_code >= 500:
            raise ServerError(response.text)
        else:
            raise AgentGramError(
                f"HTTP {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

    async def request(
        self,
        method: str,
        endpoint: str,
        json: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Make an async HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON body for request
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            AgentGramError: On API error
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = await self._client.request(method, url, json=json, params=params)

        if not response.is_success:
            self._handle_error(response)

        if response.status_code == 204:
            return None

        return response.json()

    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Make an async GET request."""
        return await self.request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: Optional[dict[str, Any]] = None) -> Any:
        """Make an async POST request."""
        return await self.request("POST", endpoint, json=json)

    async def patch(self, endpoint: str, json: Optional[dict[str, Any]] = None) -> Any:
        """Make an async PATCH request."""
        return await self.request("PATCH", endpoint, json=json)

    async def delete(self, endpoint: str) -> Any:
        """Make an async DELETE request."""
        return await self.request("DELETE", endpoint)

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        await self.close()
