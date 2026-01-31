"""
Broadcast resource for managing broadcast campaigns.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    Broadcast,
    BroadcastStats,
    CreateBroadcastRequest,
    SendBroadcastResponse,
    SuccessResponse,
    UpdateBroadcastRequest,
)


class BroadcastsResource:
    """Synchronous broadcast resource for managing broadcast campaigns."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        subject: str,
        from_email: str,
        *,
        template_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        scheduled_at: Optional[str] = None,
    ) -> Broadcast:
        """
        Create a new broadcast.

        Args:
            name: Broadcast name
            subject: Email subject
            from_email: Sender email address
            template_id: Template ID to use
            segment_id: Segment ID to target
            html_content: HTML content (if not using template)
            text_content: Plain text content
            scheduled_at: ISO 8601 datetime to schedule

        Returns:
            Created broadcast
        """
        request = CreateBroadcastRequest(
            name=name,
            subject=subject,
            from_email=from_email,
            template_id=template_id,
            segment_id=segment_id,
            html_content=html_content,
            text_content=text_content,
            scheduled_at=scheduled_at,
        )
        data = self._http.post("/v1/broadcasts", request.to_dict())
        return Broadcast.from_dict(data)


    def get(self, id: str) -> Broadcast:
        """
        Get broadcast by ID.

        Args:
            id: Broadcast ID

        Returns:
            Broadcast record
        """
        data = self._http.get(f"/v1/broadcasts/{id}")
        return Broadcast.from_dict(data)

    def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Broadcast]:
        """
        List broadcasts.

        Args:
            page: Page number
            limit: Number of items per page
            status: Filter by status

        Returns:
            List of broadcasts
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if status is not None:
            params["status"] = status

        data = self._http.get("/v1/broadcasts", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Broadcast.from_dict(b) for b in data]
        return [Broadcast.from_dict(b) for b in data.get("data", data)]

    def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        template_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        scheduled_at: Optional[str] = None,
    ) -> Broadcast:
        """
        Update a broadcast.

        Args:
            id: Broadcast ID
            name: New broadcast name
            subject: New email subject
            from_email: New sender email
            template_id: New template ID
            segment_id: New segment ID
            html_content: New HTML content
            text_content: New plain text content
            scheduled_at: New scheduled datetime

        Returns:
            Updated broadcast
        """
        request = UpdateBroadcastRequest(
            name=name,
            subject=subject,
            from_email=from_email,
            template_id=template_id,
            segment_id=segment_id,
            html_content=html_content,
            text_content=text_content,
            scheduled_at=scheduled_at,
        )
        data = self._http.put(f"/v1/broadcasts/{id}", request.to_dict())
        return Broadcast.from_dict(data)

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a broadcast.

        Args:
            id: Broadcast ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/broadcasts/{id}")
        return SuccessResponse(success=data.get("success", True))

    def send(self, id: str) -> SendBroadcastResponse:
        """
        Send a broadcast immediately.

        Args:
            id: Broadcast ID

        Returns:
            Send response with counts
        """
        data = self._http.post(f"/v1/broadcasts/{id}/send")
        return SendBroadcastResponse.from_dict(data)

    def schedule(self, id: str, scheduled_at: str) -> Broadcast:
        """
        Schedule a broadcast.

        Args:
            id: Broadcast ID
            scheduled_at: ISO 8601 datetime to schedule

        Returns:
            Updated broadcast
        """
        data = self._http.post(f"/v1/broadcasts/{id}/schedule", {"scheduled_at": scheduled_at})
        return Broadcast.from_dict(data)

    def cancel(self, id: str) -> SuccessResponse:
        """
        Cancel a scheduled broadcast.

        Args:
            id: Broadcast ID

        Returns:
            Success response
        """
        data = self._http.post(f"/v1/broadcasts/{id}/cancel")
        return SuccessResponse(success=data.get("success", True))

    def get_stats(self, id: str) -> BroadcastStats:
        """
        Get broadcast statistics.

        Args:
            id: Broadcast ID

        Returns:
            Broadcast statistics
        """
        data = self._http.get(f"/v1/broadcasts/{id}/stats")
        return BroadcastStats.from_dict(data)


class AsyncBroadcastsResource:
    """Asynchronous broadcast resource for managing broadcast campaigns."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        subject: str,
        from_email: str,
        *,
        template_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        scheduled_at: Optional[str] = None,
    ) -> Broadcast:
        """Create a new broadcast."""
        request = CreateBroadcastRequest(
            name=name,
            subject=subject,
            from_email=from_email,
            template_id=template_id,
            segment_id=segment_id,
            html_content=html_content,
            text_content=text_content,
            scheduled_at=scheduled_at,
        )
        data = await self._http.post("/v1/broadcasts", request.to_dict())
        return Broadcast.from_dict(data)

    async def get(self, id: str) -> Broadcast:
        """Get broadcast by ID."""
        data = await self._http.get(f"/v1/broadcasts/{id}")
        return Broadcast.from_dict(data)

    async def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Broadcast]:
        """List broadcasts."""
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit
        if status is not None:
            params["status"] = status

        data = await self._http.get("/v1/broadcasts", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Broadcast.from_dict(b) for b in data]
        return [Broadcast.from_dict(b) for b in data.get("data", data)]

    async def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        subject: Optional[str] = None,
        from_email: Optional[str] = None,
        template_id: Optional[str] = None,
        segment_id: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        scheduled_at: Optional[str] = None,
    ) -> Broadcast:
        """Update a broadcast."""
        request = UpdateBroadcastRequest(
            name=name,
            subject=subject,
            from_email=from_email,
            template_id=template_id,
            segment_id=segment_id,
            html_content=html_content,
            text_content=text_content,
            scheduled_at=scheduled_at,
        )
        data = await self._http.put(f"/v1/broadcasts/{id}", request.to_dict())
        return Broadcast.from_dict(data)

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a broadcast."""
        data = await self._http.delete(f"/v1/broadcasts/{id}")
        return SuccessResponse(success=data.get("success", True))

    async def send(self, id: str) -> SendBroadcastResponse:
        """Send a broadcast immediately."""
        data = await self._http.post(f"/v1/broadcasts/{id}/send")
        return SendBroadcastResponse.from_dict(data)

    async def schedule(self, id: str, scheduled_at: str) -> Broadcast:
        """Schedule a broadcast."""
        data = await self._http.post(
            f"/v1/broadcasts/{id}/schedule", {"scheduled_at": scheduled_at}
        )
        return Broadcast.from_dict(data)

    async def cancel(self, id: str) -> SuccessResponse:
        """Cancel a scheduled broadcast."""
        data = await self._http.post(f"/v1/broadcasts/{id}/cancel")
        return SuccessResponse(success=data.get("success", True))

    async def get_stats(self, id: str) -> BroadcastStats:
        """Get broadcast statistics."""
        data = await self._http.get(f"/v1/broadcasts/{id}/stats")
        return BroadcastStats.from_dict(data)
