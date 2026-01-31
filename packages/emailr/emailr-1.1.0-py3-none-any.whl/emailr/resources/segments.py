"""
Segment resource for managing contact segments.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    CreateSegmentRequest,
    Segment,
    SegmentContactsResponse,
    SegmentCountResponse,
    SuccessResponse,
    UpdateSegmentRequest,
)


class SegmentsResource:
    """Synchronous segment resource for managing contact segments."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        conditions: Dict[str, Any],
        *,
        description: Optional[str] = None,
    ) -> Segment:
        """
        Create a new segment.

        Args:
            name: Segment name
            conditions: Segment conditions/filters
            description: Segment description

        Returns:
            Created segment
        """
        request = CreateSegmentRequest(
            name=name,
            conditions=conditions,
            description=description,
        )
        data = self._http.post("/v1/segments", request.to_dict())
        return Segment.from_dict(data)

    def get(self, id: str) -> Segment:
        """
        Get segment by ID.

        Args:
            id: Segment ID

        Returns:
            Segment record
        """
        data = self._http.get(f"/v1/segments/{id}")
        return Segment.from_dict(data)

    def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Segment]:
        """
        List segments.

        Args:
            page: Page number
            limit: Number of items per page

        Returns:
            List of segments
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = self._http.get("/v1/segments", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Segment.from_dict(s) for s in data]
        return [Segment.from_dict(s) for s in data.get("data", data)]


    def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Segment:
        """
        Update a segment.

        Args:
            id: Segment ID
            name: New segment name
            description: New segment description
            conditions: New segment conditions

        Returns:
            Updated segment
        """
        request = UpdateSegmentRequest(
            name=name,
            description=description,
            conditions=conditions,
        )
        data = self._http.put(f"/v1/segments/{id}", request.to_dict())
        return Segment.from_dict(data)

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a segment.

        Args:
            id: Segment ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/segments/{id}")
        return SuccessResponse(success=data.get("success", True))

    def get_contacts(
        self,
        id: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> SegmentContactsResponse:
        """
        Get contacts in a segment.

        Args:
            id: Segment ID
            limit: Number of contacts to return
            offset: Number of contacts to skip

        Returns:
            Segment contacts response
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        data = self._http.get(f"/v1/segments/{id}/contacts", params=params)
        return SegmentContactsResponse.from_dict(data)

    def get_count(self, id: str) -> SegmentCountResponse:
        """
        Get segment contact count.

        Args:
            id: Segment ID

        Returns:
            Segment count response
        """
        data = self._http.get(f"/v1/segments/{id}/count")
        return SegmentCountResponse.from_dict(data)


class AsyncSegmentsResource:
    """Asynchronous segment resource for managing contact segments."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        conditions: Dict[str, Any],
        *,
        description: Optional[str] = None,
    ) -> Segment:
        """Create a new segment."""
        request = CreateSegmentRequest(
            name=name,
            conditions=conditions,
            description=description,
        )
        data = await self._http.post("/v1/segments", request.to_dict())
        return Segment.from_dict(data)

    async def get(self, id: str) -> Segment:
        """Get segment by ID."""
        data = await self._http.get(f"/v1/segments/{id}")
        return Segment.from_dict(data)

    async def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Segment]:
        """List segments."""
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = await self._http.get("/v1/segments", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Segment.from_dict(s) for s in data]
        return [Segment.from_dict(s) for s in data.get("data", data)]

    async def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
    ) -> Segment:
        """Update a segment."""
        request = UpdateSegmentRequest(
            name=name,
            description=description,
            conditions=conditions,
        )
        data = await self._http.put(f"/v1/segments/{id}", request.to_dict())
        return Segment.from_dict(data)

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a segment."""
        data = await self._http.delete(f"/v1/segments/{id}")
        return SuccessResponse(success=data.get("success", True))

    async def get_contacts(
        self,
        id: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> SegmentContactsResponse:
        """Get contacts in a segment."""
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        data = await self._http.get(f"/v1/segments/{id}/contacts", params=params)
        return SegmentContactsResponse.from_dict(data)

    async def get_count(self, id: str) -> SegmentCountResponse:
        """Get segment contact count."""
        data = await self._http.get(f"/v1/segments/{id}/count")
        return SegmentCountResponse.from_dict(data)
