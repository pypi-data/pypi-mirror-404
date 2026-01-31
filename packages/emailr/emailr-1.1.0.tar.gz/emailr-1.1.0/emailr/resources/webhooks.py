"""
Webhook resource for managing webhooks.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    CreateWebhookRequest,
    PaginatedResponse,
    Pagination,
    SuccessResponse,
    UpdateWebhookRequest,
    Webhook,
    WebhookDelivery,
    WebhookToggleResponse,
)


class WebhooksResource:
    """Synchronous webhook resource for managing webhooks."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        url: str,
        events: List[str],
    ) -> Webhook:
        """
        Create a new webhook.

        Args:
            name: Webhook name
            url: Webhook URL
            events: List of events to subscribe to

        Returns:
            Created webhook
        """
        request = CreateWebhookRequest(name=name, url=url, events=events)
        data = self._http.post("/v1/webhooks", request.to_dict())
        return Webhook.from_dict(data)

    def get(self, id: str) -> Webhook:
        """
        Get webhook by ID.

        Args:
            id: Webhook ID

        Returns:
            Webhook record
        """
        data = self._http.get(f"/v1/webhooks/{id}")
        return Webhook.from_dict(data)

    def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Webhook]:
        """
        List webhooks.

        Args:
            page: Page number
            limit: Number of items per page

        Returns:
            List of webhooks
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = self._http.get("/v1/webhooks", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Webhook.from_dict(w) for w in data]
        # Handle paginated response format
        return [Webhook.from_dict(w) for w in data.get("data", data)]


    def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
    ) -> Webhook:
        """
        Update a webhook.

        Args:
            id: Webhook ID
            name: New webhook name
            url: New webhook URL
            events: New list of events

        Returns:
            Updated webhook
        """
        request = UpdateWebhookRequest(name=name, url=url, events=events)
        data = self._http.put(f"/v1/webhooks/{id}", request.to_dict())
        return Webhook.from_dict(data)

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a webhook.

        Args:
            id: Webhook ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/webhooks/{id}")
        return SuccessResponse(success=data.get("success", True))

    def enable(self, id: str) -> WebhookToggleResponse:
        """
        Enable a webhook.

        Args:
            id: Webhook ID

        Returns:
            Toggle response with new active status
        """
        data = self._http.post(f"/v1/webhooks/{id}/enable")
        return WebhookToggleResponse.from_dict(data)

    def disable(self, id: str) -> WebhookToggleResponse:
        """
        Disable a webhook.

        Args:
            id: Webhook ID

        Returns:
            Toggle response with new active status
        """
        data = self._http.post(f"/v1/webhooks/{id}/disable")
        return WebhookToggleResponse.from_dict(data)

    def list_deliveries(self, id: str) -> List[WebhookDelivery]:
        """
        List webhook deliveries.

        Args:
            id: Webhook ID

        Returns:
            List of webhook deliveries
        """
        data = self._http.get(f"/v1/webhooks/{id}/deliveries")
        # API returns array directly
        if isinstance(data, list):
            return [WebhookDelivery.from_dict(d) for d in data]
        return [WebhookDelivery.from_dict(d) for d in data.get("data", data)]

    def retry_delivery(self, webhook_id: str, delivery_id: str) -> SuccessResponse:
        """
        Retry a failed webhook delivery.

        Args:
            webhook_id: Webhook ID
            delivery_id: Delivery ID

        Returns:
            Success response
        """
        data = self._http.post(f"/v1/webhooks/{webhook_id}/deliveries/{delivery_id}/retry")
        return SuccessResponse(success=data.get("success", True))


class AsyncWebhooksResource:
    """Asynchronous webhook resource for managing webhooks."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        url: str,
        events: List[str],
    ) -> Webhook:
        """Create a new webhook."""
        request = CreateWebhookRequest(name=name, url=url, events=events)
        data = await self._http.post("/v1/webhooks", request.to_dict())
        return Webhook.from_dict(data)

    async def get(self, id: str) -> Webhook:
        """Get webhook by ID."""
        data = await self._http.get(f"/v1/webhooks/{id}")
        return Webhook.from_dict(data)

    async def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Webhook]:
        """List webhooks."""
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = await self._http.get("/v1/webhooks", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Webhook.from_dict(w) for w in data]
        return [Webhook.from_dict(w) for w in data.get("data", data)]

    async def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
    ) -> Webhook:
        """Update a webhook."""
        request = UpdateWebhookRequest(name=name, url=url, events=events)
        data = await self._http.put(f"/v1/webhooks/{id}", request.to_dict())
        return Webhook.from_dict(data)

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a webhook."""
        data = await self._http.delete(f"/v1/webhooks/{id}")
        return SuccessResponse(success=data.get("success", True))

    async def enable(self, id: str) -> WebhookToggleResponse:
        """Enable a webhook."""
        data = await self._http.post(f"/v1/webhooks/{id}/enable")
        return WebhookToggleResponse.from_dict(data)

    async def disable(self, id: str) -> WebhookToggleResponse:
        """Disable a webhook."""
        data = await self._http.post(f"/v1/webhooks/{id}/disable")
        return WebhookToggleResponse.from_dict(data)

    async def list_deliveries(self, id: str) -> List[WebhookDelivery]:
        """List webhook deliveries."""
        data = await self._http.get(f"/v1/webhooks/{id}/deliveries")
        # API returns array directly
        if isinstance(data, list):
            return [WebhookDelivery.from_dict(d) for d in data]
        return [WebhookDelivery.from_dict(d) for d in data.get("data", data)]

    async def retry_delivery(self, webhook_id: str, delivery_id: str) -> SuccessResponse:
        """Retry a failed webhook delivery."""
        data = await self._http.post(
            f"/v1/webhooks/{webhook_id}/deliveries/{delivery_id}/retry"
        )
        return SuccessResponse(success=data.get("success", True))
