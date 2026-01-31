"""
Settings resource for organization and unsubscribe settings.
"""

from typing import List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    Organization,
    UpdateOrganizationRequest,
    TeamMember,
    UnsubscribeSettings,
    UpdateUnsubscribeSettingsRequest,
)


class SettingsResource:
    """Synchronous settings resource."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_organization(self) -> Organization:
        """
        Get organization settings.

        Returns:
            Organization settings
        """
        data = self._http.get("/v1/settings/organization")
        return Organization.from_dict(data)

    def update_organization(
        self,
        *,
        name: Optional[str] = None,
        billing_email: Optional[str] = None,
    ) -> Organization:
        """
        Update organization settings.

        Args:
            name: Organization name
            billing_email: Billing email address

        Returns:
            Updated organization
        """
        request = UpdateOrganizationRequest(name=name, billing_email=billing_email)
        data = self._http.put("/v1/settings/organization", request.to_dict())
        return Organization.from_dict(data)

    def get_team(self) -> List[TeamMember]:
        """
        Get team members.

        Returns:
            List of team members
        """
        data = self._http.get("/v1/settings/team")
        if isinstance(data, list):
            return [TeamMember.from_dict(m) for m in data]
        return [TeamMember.from_dict(m) for m in data.get("data", data)]

    def get_unsubscribe_settings(self) -> UnsubscribeSettings:
        """
        Get unsubscribe settings.

        Returns:
            Unsubscribe settings
        """
        data = self._http.get("/v1/settings/unsubscribe")
        return UnsubscribeSettings.from_dict(data)

    def update_unsubscribe_settings(
        self,
        *,
        custom_message: Optional[str] = None,
        redirect_url: Optional[str] = None,
        one_click_enabled: Optional[bool] = None,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> UnsubscribeSettings:
        """
        Update unsubscribe settings.

        Args:
            custom_message: Custom unsubscribe message
            redirect_url: Redirect URL after unsubscribe
            one_click_enabled: Enable one-click unsubscribe
            logo_url: Logo URL for branding
            primary_color: Primary color (hex format)
            company_name: Company name for branding

        Returns:
            Updated unsubscribe settings
        """
        request = UpdateUnsubscribeSettingsRequest(
            custom_message=custom_message,
            redirect_url=redirect_url,
            one_click_enabled=one_click_enabled,
            logo_url=logo_url,
            primary_color=primary_color,
            company_name=company_name,
        )
        data = self._http.put("/v1/settings/unsubscribe", request.to_dict())
        return UnsubscribeSettings.from_dict(data)


class AsyncSettingsResource:
    """Asynchronous settings resource."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def get_organization(self) -> Organization:
        """Get organization settings."""
        data = await self._http.get("/v1/settings/organization")
        return Organization.from_dict(data)

    async def update_organization(
        self,
        *,
        name: Optional[str] = None,
        billing_email: Optional[str] = None,
    ) -> Organization:
        """Update organization settings."""
        request = UpdateOrganizationRequest(name=name, billing_email=billing_email)
        data = await self._http.put("/v1/settings/organization", request.to_dict())
        return Organization.from_dict(data)

    async def get_team(self) -> List[TeamMember]:
        """Get team members."""
        data = await self._http.get("/v1/settings/team")
        if isinstance(data, list):
            return [TeamMember.from_dict(m) for m in data]
        return [TeamMember.from_dict(m) for m in data.get("data", data)]

    async def get_unsubscribe_settings(self) -> UnsubscribeSettings:
        """Get unsubscribe settings."""
        data = await self._http.get("/v1/settings/unsubscribe")
        return UnsubscribeSettings.from_dict(data)

    async def update_unsubscribe_settings(
        self,
        *,
        custom_message: Optional[str] = None,
        redirect_url: Optional[str] = None,
        one_click_enabled: Optional[bool] = None,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        company_name: Optional[str] = None,
    ) -> UnsubscribeSettings:
        """Update unsubscribe settings."""
        request = UpdateUnsubscribeSettingsRequest(
            custom_message=custom_message,
            redirect_url=redirect_url,
            one_click_enabled=one_click_enabled,
            logo_url=logo_url,
            primary_color=primary_color,
            company_name=company_name,
        )
        data = await self._http.put("/v1/settings/unsubscribe", request.to_dict())
        return UnsubscribeSettings.from_dict(data)
