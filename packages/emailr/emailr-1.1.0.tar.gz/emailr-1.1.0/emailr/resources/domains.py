"""
Domain resource for managing email domains.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    AddDomainRequest,
    DnsVerificationStatus,
    Domain,
    DomainVerificationStatus,
    PaginatedResponse,
    Pagination,
    SuccessResponse,
    UpdateDomainRequest,
)


class DomainsResource:
    """Synchronous domain resource for managing email domains."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def add(
        self,
        domain: str,
        *,
        receiving_subdomain: Optional[str] = None,
    ) -> Domain:
        """
        Add a new domain.

        Args:
            domain: Domain name to add
            receiving_subdomain: Subdomain for receiving emails

        Returns:
            Created domain
        """
        request = AddDomainRequest(domain=domain, receiving_subdomain=receiving_subdomain)
        data = self._http.post("/v1/domains", request.to_dict())
        return Domain.from_dict(data)

    def get(self, id: str) -> Domain:
        """
        Get domain by ID.

        Args:
            id: Domain ID

        Returns:
            Domain record
        """
        data = self._http.get(f"/v1/domains/{id}")
        return Domain.from_dict(data)

    def list(self) -> List[Domain]:
        """
        List all domains.

        Returns:
            List of domains
        """
        data = self._http.get("/v1/domains")
        # API returns array directly
        if isinstance(data, list):
            return [Domain.from_dict(d) for d in data]
        # Or wrapped in data/pagination
        return [Domain.from_dict(d) for d in data.get("data", data)]


    def update(
        self,
        id: str,
        *,
        receiving_enabled: Optional[bool] = None,
    ) -> Domain:
        """
        Update domain settings.

        Args:
            id: Domain ID
            receiving_enabled: Whether to enable receiving emails

        Returns:
            Updated domain
        """
        request = UpdateDomainRequest(receiving_enabled=receiving_enabled)
        data = self._http.put(f"/v1/domains/{id}", request.to_dict())
        return Domain.from_dict(data)

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a domain.

        Args:
            id: Domain ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/domains/{id}")
        return SuccessResponse(success=data.get("success", True))

    def verify(self, id: str) -> DomainVerificationStatus:
        """
        Verify domain DNS records.

        Args:
            id: Domain ID

        Returns:
            Domain verification status
        """
        data = self._http.post(f"/v1/domains/{id}/verify")
        return DomainVerificationStatus.from_dict(data)

    def check_dns(self, id: str) -> DnsVerificationStatus:
        """
        Check DNS verification status.

        Args:
            id: Domain ID

        Returns:
            DNS verification status for all records
        """
        data = self._http.get(f"/v1/domains/{id}/dns-status")
        return DnsVerificationStatus.from_dict(data)


class AsyncDomainsResource:
    """Asynchronous domain resource for managing email domains."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def add(
        self,
        domain: str,
        *,
        receiving_subdomain: Optional[str] = None,
    ) -> Domain:
        """Add a new domain."""
        request = AddDomainRequest(domain=domain, receiving_subdomain=receiving_subdomain)
        data = await self._http.post("/v1/domains", request.to_dict())
        return Domain.from_dict(data)

    async def get(self, id: str) -> Domain:
        """Get domain by ID."""
        data = await self._http.get(f"/v1/domains/{id}")
        return Domain.from_dict(data)

    async def list(self) -> List[Domain]:
        """List all domains."""
        data = await self._http.get("/v1/domains")
        # API returns array directly
        if isinstance(data, list):
            return [Domain.from_dict(d) for d in data]
        # Or wrapped in data/pagination
        return [Domain.from_dict(d) for d in data.get("data", data)]

    async def update(
        self,
        id: str,
        *,
        receiving_enabled: Optional[bool] = None,
    ) -> Domain:
        """Update domain settings."""
        request = UpdateDomainRequest(receiving_enabled=receiving_enabled)
        data = await self._http.put(f"/v1/domains/{id}", request.to_dict())
        return Domain.from_dict(data)

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a domain."""
        data = await self._http.delete(f"/v1/domains/{id}")
        return SuccessResponse(success=data.get("success", True))

    async def verify(self, id: str) -> DomainVerificationStatus:
        """Verify domain DNS records."""
        data = await self._http.post(f"/v1/domains/{id}/verify")
        return DomainVerificationStatus.from_dict(data)

    async def check_dns(self, id: str) -> DnsVerificationStatus:
        """Check DNS verification status."""
        data = await self._http.get(f"/v1/domains/{id}/dns-status")
        return DnsVerificationStatus.from_dict(data)
