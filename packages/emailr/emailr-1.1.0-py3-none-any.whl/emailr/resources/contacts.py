"""
Contact resource for managing contacts.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    BulkCreateContactsRequest,
    BulkCreateContactsResponse,
    Contact,
    ContactListResponse,
    CreateContactRequest,
    SuccessResponse,
    UpdateContactRequest,
)


class ContactsResource:
    """Synchronous contact resource for managing contacts."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        email: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        subscribed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Contact:
        """
        Create a new contact.

        Args:
            email: Contact email address
            first_name: Contact first name
            last_name: Contact last name
            subscribed: Whether contact is subscribed
            metadata: Custom metadata

        Returns:
            Created contact
        """
        request = CreateContactRequest(
            email=email,
            first_name=first_name,
            last_name=last_name,
            subscribed=subscribed,
            metadata=metadata,
        )
        data = self._http.post("/v1/contacts", request.to_dict())
        return Contact.from_dict(data)

    def get(self, id: str) -> Contact:
        """
        Get contact by ID.

        Args:
            id: Contact ID

        Returns:
            Contact record
        """
        data = self._http.get(f"/v1/contacts/{id}")
        return Contact.from_dict(data)


    def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        subscribed: Optional[bool] = None,
    ) -> ContactListResponse:
        """
        List contacts with optional filtering.

        Args:
            limit: Number of items to return
            offset: Number of items to skip
            subscribed: Filter by subscription status

        Returns:
            Contact list response with pagination info
        """
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if subscribed is not None:
            params["subscribed"] = subscribed

        data = self._http.get("/v1/contacts", params=params)
        return ContactListResponse.from_dict(data)

    def update(
        self,
        id: str,
        *,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        subscribed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Contact:
        """
        Update a contact.

        Args:
            id: Contact ID
            email: New email address
            first_name: New first name
            last_name: New last name
            subscribed: New subscription status
            metadata: New metadata

        Returns:
            Updated contact
        """
        request = UpdateContactRequest(
            email=email,
            first_name=first_name,
            last_name=last_name,
            subscribed=subscribed,
            metadata=metadata,
        )
        data = self._http.put(f"/v1/contacts/{id}", request.to_dict())
        return Contact.from_dict(data)

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a contact.

        Args:
            id: Contact ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/contacts/{id}")
        return SuccessResponse(success=data.get("success", True))

    def bulk_create(self, contacts: List[CreateContactRequest]) -> BulkCreateContactsResponse:
        """
        Bulk create contacts.

        Args:
            contacts: List of contacts to create

        Returns:
            Bulk create response with import count
        """
        request = BulkCreateContactsRequest(contacts=contacts)
        data = self._http.post("/v1/contacts/bulk", request.to_dict())
        return BulkCreateContactsResponse.from_dict(data)

    def unsubscribe(self, id: str) -> SuccessResponse:
        """
        Unsubscribe a contact.

        Args:
            id: Contact ID

        Returns:
            Success response
        """
        data = self._http.post(f"/v1/contacts/{id}/unsubscribe")
        return SuccessResponse(success=data.get("success", True))

    def resubscribe(self, id: str) -> SuccessResponse:
        """
        Resubscribe a contact.

        Args:
            id: Contact ID

        Returns:
            Success response
        """
        data = self._http.post(f"/v1/contacts/{id}/resubscribe")
        return SuccessResponse(success=data.get("success", True))


class AsyncContactsResource:
    """Asynchronous contact resource for managing contacts."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        email: str,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        subscribed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Contact:
        """Create a new contact."""
        request = CreateContactRequest(
            email=email,
            first_name=first_name,
            last_name=last_name,
            subscribed=subscribed,
            metadata=metadata,
        )
        data = await self._http.post("/v1/contacts", request.to_dict())
        return Contact.from_dict(data)

    async def get(self, id: str) -> Contact:
        """Get contact by ID."""
        data = await self._http.get(f"/v1/contacts/{id}")
        return Contact.from_dict(data)

    async def list(
        self,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        subscribed: Optional[bool] = None,
    ) -> ContactListResponse:
        """List contacts with optional filtering."""
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if subscribed is not None:
            params["subscribed"] = subscribed

        data = await self._http.get("/v1/contacts", params=params)
        return ContactListResponse.from_dict(data)

    async def update(
        self,
        id: str,
        *,
        email: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        subscribed: Optional[bool] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Contact:
        """Update a contact."""
        request = UpdateContactRequest(
            email=email,
            first_name=first_name,
            last_name=last_name,
            subscribed=subscribed,
            metadata=metadata,
        )
        data = await self._http.put(f"/v1/contacts/{id}", request.to_dict())
        return Contact.from_dict(data)

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a contact."""
        data = await self._http.delete(f"/v1/contacts/{id}")
        return SuccessResponse(success=data.get("success", True))

    async def bulk_create(
        self, contacts: List[CreateContactRequest]
    ) -> BulkCreateContactsResponse:
        """Bulk create contacts."""
        request = BulkCreateContactsRequest(contacts=contacts)
        data = await self._http.post("/v1/contacts/bulk", request.to_dict())
        return BulkCreateContactsResponse.from_dict(data)

    async def unsubscribe(self, id: str) -> SuccessResponse:
        """Unsubscribe a contact."""
        data = await self._http.post(f"/v1/contacts/{id}/unsubscribe")
        return SuccessResponse(success=data.get("success", True))

    async def resubscribe(self, id: str) -> SuccessResponse:
        """Resubscribe a contact."""
        data = await self._http.post(f"/v1/contacts/{id}/resubscribe")
        return SuccessResponse(success=data.get("success", True))
