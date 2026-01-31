"""
Email resource for sending and managing emails.
"""

from typing import Any, Dict, List, Optional, Union

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    Email,
    ForwardEmailRequest,
    ListEmailsParams,
    PaginatedResponse,
    Pagination,
    SendEmailRequest,
    SendEmailResponse,
)


class EmailsResource:
    """Synchronous email resource for sending and managing emails."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(
        self,
        to: Union[str, List[str]],
        *,
        from_: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Send an email to one or multiple recipients.

        Args:
            to: Recipient email address(es)
            from_: Sender email address
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            subject: Email subject
            html: HTML content
            text: Plain text content
            template_id: Template ID to use
            template_data: Data for template variables
            tags: Custom tags for tracking
            scheduled_at: ISO 8601 datetime to schedule sending

        Returns:
            SendEmailResponse with message_id and status
        """
        request = SendEmailRequest(
            to=to,
            from_=from_,
            cc=cc,
            bcc=bcc,
            subject=subject,
            html=html,
            text=text,
            template_id=template_id,
            template_data=template_data,
            tags=tags,
            scheduled_at=scheduled_at,
        )
        data = self._http.post("/v1/emails/send", request.to_dict())
        return SendEmailResponse.from_dict(data)


    def get(self, id: str) -> Email:
        """
        Get email by ID.

        Args:
            id: Email ID

        Returns:
            Email record
        """
        data = self._http.get(f"/v1/emails/{id}")
        return Email.from_dict(data)

    def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> PaginatedResponse[Email]:
        """
        List emails with pagination.

        Args:
            page: Page number
            limit: Number of items per page

        Returns:
            Paginated list of emails
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = self._http.get("/v1/emails", params=params)
        return PaginatedResponse(
            data=[Email.from_dict(e) for e in data["data"]],
            pagination=Pagination(**data["pagination"]),
        )

    def forward(
        self,
        email_id: str,
        to: Union[str, List[str]],
        *,
        message: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Forward an email to other recipients.

        Args:
            email_id: ID of the email to forward
            to: Recipient email address(es)
            message: Optional message to include

        Returns:
            SendEmailResponse with message_id and status
        """
        request = ForwardEmailRequest(email_id=email_id, to=to, message=message)
        data = self._http.post("/v1/emails/forward", request.to_dict())
        return SendEmailResponse.from_dict(data)


class AsyncEmailsResource:
    """Asynchronous email resource for sending and managing emails."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def send(
        self,
        to: Union[str, List[str]],
        *,
        from_: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        html: Optional[str] = None,
        text: Optional[str] = None,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        scheduled_at: Optional[str] = None,
    ) -> SendEmailResponse:
        """
        Send an email to one or multiple recipients.

        Args:
            to: Recipient email address(es)
            from_: Sender email address
            cc: CC recipient(s)
            bcc: BCC recipient(s)
            subject: Email subject
            html: HTML content
            text: Plain text content
            template_id: Template ID to use
            template_data: Data for template variables
            tags: Custom tags for tracking
            scheduled_at: ISO 8601 datetime to schedule sending

        Returns:
            SendEmailResponse with message_id and status
        """
        request = SendEmailRequest(
            to=to,
            from_=from_,
            cc=cc,
            bcc=bcc,
            subject=subject,
            html=html,
            text=text,
            template_id=template_id,
            template_data=template_data,
            tags=tags,
            scheduled_at=scheduled_at,
        )
        data = await self._http.post("/v1/emails/send", request.to_dict())
        return SendEmailResponse.from_dict(data)

    async def get(self, id: str) -> Email:
        """Get email by ID."""
        data = await self._http.get(f"/v1/emails/{id}")
        return Email.from_dict(data)

    async def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> PaginatedResponse[Email]:
        """List emails with pagination."""
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = await self._http.get("/v1/emails", params=params)
        return PaginatedResponse(
            data=[Email.from_dict(e) for e in data["data"]],
            pagination=Pagination(**data["pagination"]),
        )

    async def forward(
        self,
        email_id: str,
        to: Union[str, List[str]],
        *,
        message: Optional[str] = None,
    ) -> SendEmailResponse:
        """Forward an email to other recipients."""
        request = ForwardEmailRequest(email_id=email_id, to=to, message=message)
        data = await self._http.post("/v1/emails/forward", request.to_dict())
        return SendEmailResponse.from_dict(data)
