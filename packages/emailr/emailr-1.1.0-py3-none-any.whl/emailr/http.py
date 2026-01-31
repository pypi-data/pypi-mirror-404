"""
HTTP client implementations for the Emailr SDK.

Provides both synchronous (HttpClient) and asynchronous (AsyncHttpClient)
HTTP clients using httpx.
"""

from typing import Any, Dict, Optional, TypeVar, Union

import httpx

from emailr.errors import (
    AuthenticationError,
    EmailrError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

T = TypeVar("T")


class HttpClient:
    """
    Synchronous HTTP client for making API requests.

    Uses httpx for HTTP requests with automatic error handling
    and response parsing.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create the httpx client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a GET request."""
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a POST request."""
        return self._request("POST", path, data=data, params=params)

    def put(
        self,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a PUT request."""
        return self._request("PUT", path, data=data, params=params)

    def patch(
        self,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a PATCH request."""
        return self._request("PATCH", path, data=data, params=params)

    def delete(
        self,
        path: str,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a DELETE request."""
        return self._request("DELETE", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make an HTTP request."""
        client = self._get_client()

        # Filter out None values from params
        filtered_params: Optional[Dict[str, Any]] = None
        if params:
            filtered_params = {k: v for k, v in params.items() if v is not None}

        try:
            response = client.request(
                method=method,
                url=path,
                json=data if data is not None else None,
                params=filtered_params,
            )
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timeout after {self._timeout}s", cause=e)
        except httpx.RequestError as e:
            raise NetworkError(str(e), cause=e)

        request_id = response.headers.get("x-request-id")

        if not response.is_success:
            self._handle_error_response(response, request_id)

        # Handle empty responses (204 No Content)
        if response.status_code == 204:
            return {}

        return response.json()

    def _handle_error_response(
        self,
        response: httpx.Response,
        request_id: Optional[str],
    ) -> None:
        """Handle error responses and raise appropriate exceptions."""
        try:
            error_data = response.json()
        except Exception:
            error_data = {"error": response.text or "Unknown error"}

        message = error_data.get("error", "An error occurred")
        details = error_data.get("details")
        code = error_data.get("code")

        if response.status_code == 400:
            raise ValidationError(message, details=details, request_id=request_id)
        elif response.status_code == 401:
            raise AuthenticationError(message, request_id=request_id)
        elif response.status_code == 404:
            raise NotFoundError(message, request_id=request_id)
        elif response.status_code == 429:
            retry_after_header = response.headers.get("retry-after")
            retry_after = int(retry_after_header) if retry_after_header else None
            raise RateLimitError(message, retry_after=retry_after, request_id=request_id)
        else:
            raise EmailrError(
                message,
                status_code=response.status_code,
                code=code,
                request_id=request_id,
            )


class AsyncHttpClient:
    """
    Asynchronous HTTP client for making API requests.

    Uses httpx for async HTTP requests with automatic error handling
    and response parsing.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: float,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a GET request."""
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a POST request."""
        return await self._request("POST", path, data=data, params=params)

    async def put(
        self,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a PUT request."""
        return await self._request("PUT", path, data=data, params=params)

    async def patch(
        self,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a PATCH request."""
        return await self._request("PATCH", path, data=data, params=params)

    async def delete(
        self,
        path: str,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make a DELETE request."""
        return await self._request("DELETE", path, params=params)

    async def _request(
        self,
        method: str,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, Union[str, int, bool, None]]] = None,
    ) -> Any:
        """Make an HTTP request."""
        client = await self._get_client()

        # Filter out None values from params
        filtered_params: Optional[Dict[str, Any]] = None
        if params:
            filtered_params = {k: v for k, v in params.items() if v is not None}

        try:
            response = await client.request(
                method=method,
                url=path,
                json=data if data is not None else None,
                params=filtered_params,
            )
        except httpx.TimeoutException as e:
            raise NetworkError(f"Request timeout after {self._timeout}s", cause=e)
        except httpx.RequestError as e:
            raise NetworkError(str(e), cause=e)

        request_id = response.headers.get("x-request-id")

        if not response.is_success:
            self._handle_error_response(response, request_id)

        # Handle empty responses (204 No Content)
        if response.status_code == 204:
            return {}

        return response.json()

    def _handle_error_response(
        self,
        response: httpx.Response,
        request_id: Optional[str],
    ) -> None:
        """Handle error responses and raise appropriate exceptions."""
        try:
            error_data = response.json()
        except Exception:
            error_data = {"error": response.text or "Unknown error"}

        message = error_data.get("error", "An error occurred")
        details = error_data.get("details")
        code = error_data.get("code")

        if response.status_code == 400:
            raise ValidationError(message, details=details, request_id=request_id)
        elif response.status_code == 401:
            raise AuthenticationError(message, request_id=request_id)
        elif response.status_code == 404:
            raise NotFoundError(message, request_id=request_id)
        elif response.status_code == 429:
            retry_after_header = response.headers.get("retry-after")
            retry_after = int(retry_after_header) if retry_after_header else None
            raise RateLimitError(message, retry_after=retry_after, request_id=request_id)
        else:
            raise EmailrError(
                message,
                status_code=response.status_code,
                code=code,
                request_id=request_id,
            )
