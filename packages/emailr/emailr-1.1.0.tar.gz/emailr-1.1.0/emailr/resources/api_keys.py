"""
API Keys resource for managing API keys.
"""

from typing import Any, Dict, List

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    ApiKey,
    ApiKeyListItem,
    CreateApiKeyRequest,
    SuccessResponse,
)


class ApiKeysResource:
    """Synchronous API keys resource."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        *,
        permissions: List[str] | None = None,
    ) -> ApiKey:
        """
        Create a new API key.
        Note: The full key is only returned once upon creation.

        Args:
            name: Name for the API key
            permissions: Optional list of permissions

        Returns:
            Created API key with the full key value
        """
        request = CreateApiKeyRequest(name=name, permissions=permissions)
        data = self._http.post("/v1/api-keys", request.to_dict())
        return ApiKey.from_dict(data)

    def list(self) -> List[ApiKeyListItem]:
        """
        List all active API keys.
        Note: Full keys are not returned for security.

        Returns:
            List of API key metadata
        """
        data = self._http.get("/v1/api-keys")
        if isinstance(data, list):
            return [ApiKeyListItem.from_dict(k) for k in data]
        return [ApiKeyListItem.from_dict(k) for k in data.get("data", data)]

    def revoke(self, id: str) -> SuccessResponse:
        """
        Revoke an API key.

        Args:
            id: API key ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/api-keys/{id}")
        return SuccessResponse(success=data.get("success", True))


class AsyncApiKeysResource:
    """Asynchronous API keys resource."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        *,
        permissions: List[str] | None = None,
    ) -> ApiKey:
        """Create a new API key."""
        request = CreateApiKeyRequest(name=name, permissions=permissions)
        data = await self._http.post("/v1/api-keys", request.to_dict())
        return ApiKey.from_dict(data)

    async def list(self) -> List[ApiKeyListItem]:
        """List all active API keys."""
        data = await self._http.get("/v1/api-keys")
        if isinstance(data, list):
            return [ApiKeyListItem.from_dict(k) for k in data]
        return [ApiKeyListItem.from_dict(k) for k in data.get("data", data)]

    async def revoke(self, id: str) -> SuccessResponse:
        """Revoke an API key."""
        data = await self._http.delete(f"/v1/api-keys/{id}")
        return SuccessResponse(success=data.get("success", True))
