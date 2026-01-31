"""Generic REST API client with retry and authentication support."""

from typing import Any

from rclco.core.exceptions import APIError, ConfigurationError
from rclco.core.logging import get_logger

logger = get_logger("connectors.api.client")


class RESTClient:
    """Generic REST API client for making HTTP requests.

    Supports GET and POST requests with optional authentication,
    automatic retry, and timeout handling.

    Example:
        # Create a client with API key authentication
        client = RESTClient(
            base_url="https://api.example.com/v1",
            api_key="your-api-key"
        )

        # Make requests
        data = client.get("users", params={"page": 1})
        result = client.post("users", json={"name": "John"})

        # Clean up
        client.close()

        # Or use as context manager
        with RESTClient(base_url="https://api.example.com") as client:
            data = client.get("endpoint")
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ):
        """Initialize the REST client.

        Args:
            base_url: Base URL for the API (e.g., "https://api.example.com/v1")
            api_key: Optional API key for Bearer / Api-Key token authentication (add the "Bearer " or "Api-Key " prefix to the key)
            timeout: Request timeout in seconds (default: 30)
            headers: Optional additional headers to include in all requests
        """
        try:
            import httpx
        except ImportError as e:
            raise ConfigurationError(
                "httpx not installed. Run: pip install httpx"
            ) from e

        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

        # Build default headers
        self._headers = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = api_key
        if headers:
            self._headers.update(headers)

        # Create the HTTP client
        self._client = httpx.Client(
            timeout=timeout,
            headers=self._headers,
        )

        logger.debug(f"Created REST client for {self._base_url}")

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if self._client:
            self._client.close()
            logger.debug("Closed REST client")

    def __enter__(self) -> "RESTClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager."""
        self.close()

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint.

        Args:
            endpoint: API endpoint (e.g., "users" or "/users")

        Returns:
            Full URL
        """
        endpoint = endpoint.lstrip("/")
        return f"{self._base_url}/{endpoint}"

    def _handle_response(self, response) -> dict[str, Any]:
        """Handle HTTP response, raising errors for non-2xx status codes.

        Args:
            response: httpx Response object

        Returns:
            Response JSON as dictionary

        Raises:
            APIError: If the response status is not successful
        """
        if response.status_code >= 400:
            try:
                body = response.text
            except Exception:
                body = None

            raise APIError(
                f"API request failed with status {response.status_code}: {response.reason_phrase}",
                status_code=response.status_code,
                response_body=body,
            )

        # Handle empty responses
        if response.status_code == 204 or not response.content:
            return {}

        try:
            return response.json()
        except Exception:
            # Return text content wrapped in a dict if not JSON
            return {"content": response.text}

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            headers: Optional additional headers for this request

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the request fails
        """
        url = self._build_url(endpoint)

        try:
            response = self._client.get(url, params=params, headers=headers)
            logger.debug(f"GET {url} -> {response.status_code}")
            return self._handle_response(response)
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"GET request to {url} failed: {e}") from e

    def post(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request.

        Args:
            endpoint: API endpoint path
            json: Optional JSON body (will be serialized)
            data: Optional form data
            headers: Optional additional headers for this request

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the request fails
        """
        url = self._build_url(endpoint)

        try:
            response = self._client.post(url, json=json, data=data, headers=headers)
            logger.debug(f"POST {url} -> {response.status_code}")
            return self._handle_response(response)
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"POST request to {url} failed: {e}") from e

    def put(
        self,
        endpoint: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a PUT request.

        Args:
            endpoint: API endpoint path
            json: Optional JSON body
            headers: Optional additional headers for this request

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the request fails
        """
        url = self._build_url(endpoint)

        try:
            response = self._client.put(url, json=json, headers=headers)
            logger.debug(f"PUT {url} -> {response.status_code}")
            return self._handle_response(response)
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"PUT request to {url} failed: {e}") from e

    def delete(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Make a DELETE request.

        Args:
            endpoint: API endpoint path
            headers: Optional additional headers for this request

        Returns:
            Response data as dictionary

        Raises:
            APIError: If the request fails
        """
        url = self._build_url(endpoint)

        try:
            response = self._client.delete(url, headers=headers)
            logger.debug(f"DELETE {url} -> {response.status_code}")
            return self._handle_response(response)
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"DELETE request to {url} failed: {e}") from e
