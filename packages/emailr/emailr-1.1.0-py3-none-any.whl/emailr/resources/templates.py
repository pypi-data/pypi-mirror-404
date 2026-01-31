"""
Template resource for managing email templates.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    CreateTemplateRequest,
    PaginatedResponse,
    Pagination,
    SuccessResponse,
    Template,
    UpdateTemplateRequest,
)


class TemplatesResource:
    """Synchronous template resource for managing email templates."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        subject: str,
        *,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        variables: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        preview_text: Optional[str] = None,
    ) -> Template:
        """
        Create a new template.

        Args:
            name: Template name
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            variables: List of variable names
            from_email: Default sender email
            reply_to: Default reply-to email
            preview_text: Email preview text

        Returns:
            Created template
        """
        request = CreateTemplateRequest(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            variables=variables,
            from_email=from_email,
            reply_to=reply_to,
            preview_text=preview_text,
        )
        data = self._http.post("/v1/templates", request.to_dict())
        return Template.from_dict(data)


    def get(self, id: str) -> Template:
        """
        Get template by ID.

        Args:
            id: Template ID

        Returns:
            Template record
        """
        data = self._http.get(f"/v1/templates/{id}")
        return Template.from_dict(data)

    def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Template]:
        """
        List templates with pagination.

        Args:
            page: Page number
            limit: Number of items per page

        Returns:
            List of templates
        """
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = self._http.get("/v1/templates", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Template.from_dict(t) for t in data]
        # Or wrapped in data/pagination
        return [Template.from_dict(t) for t in data.get("data", data)]

    def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        subject: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        variables: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        preview_text: Optional[str] = None,
    ) -> Template:
        """
        Update a template.

        Args:
            id: Template ID
            name: New template name
            subject: New email subject
            html_content: New HTML content
            text_content: New plain text content
            variables: New list of variable names
            from_email: New default sender email
            reply_to: New default reply-to email
            preview_text: New email preview text

        Returns:
            Updated template
        """
        request = UpdateTemplateRequest(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            variables=variables,
            from_email=from_email,
            reply_to=reply_to,
            preview_text=preview_text,
        )
        data = self._http.put(f"/v1/templates/{id}", request.to_dict())
        return Template.from_dict(data)

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a template.

        Args:
            id: Template ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/templates/{id}")
        return SuccessResponse(success=data.get("success", True))

    def duplicate(self, id: str) -> Template:
        """
        Duplicate a template.

        Args:
            id: Template ID to duplicate

        Returns:
            New duplicated template
        """
        data = self._http.post(f"/v1/templates/{id}/duplicate")
        return Template.from_dict(data)


class AsyncTemplatesResource:
    """Asynchronous template resource for managing email templates."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        subject: str,
        *,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        variables: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        preview_text: Optional[str] = None,
    ) -> Template:
        """Create a new template."""
        request = CreateTemplateRequest(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            variables=variables,
            from_email=from_email,
            reply_to=reply_to,
            preview_text=preview_text,
        )
        data = await self._http.post("/v1/templates", request.to_dict())
        return Template.from_dict(data)

    async def get(self, id: str) -> Template:
        """Get template by ID."""
        data = await self._http.get(f"/v1/templates/{id}")
        return Template.from_dict(data)

    async def list(
        self,
        *,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Template]:
        """List templates with pagination."""
        params: Dict[str, Any] = {}
        if page is not None:
            params["page"] = page
        if limit is not None:
            params["limit"] = limit

        data = await self._http.get("/v1/templates", params=params)
        # API returns array directly
        if isinstance(data, list):
            return [Template.from_dict(t) for t in data]
        # Or wrapped in data/pagination
        return [Template.from_dict(t) for t in data.get("data", data)]

    async def update(
        self,
        id: str,
        *,
        name: Optional[str] = None,
        subject: Optional[str] = None,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        variables: Optional[List[str]] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        preview_text: Optional[str] = None,
    ) -> Template:
        """Update a template."""
        request = UpdateTemplateRequest(
            name=name,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            variables=variables,
            from_email=from_email,
            reply_to=reply_to,
            preview_text=preview_text,
        )
        data = await self._http.put(f"/v1/templates/{id}", request.to_dict())
        return Template.from_dict(data)

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a template."""
        data = await self._http.delete(f"/v1/templates/{id}")
        return SuccessResponse(success=data.get("success", True))

    async def duplicate(self, id: str) -> Template:
        """Duplicate a template."""
        data = await self._http.post(f"/v1/templates/{id}/duplicate")
        return Template.from_dict(data)
