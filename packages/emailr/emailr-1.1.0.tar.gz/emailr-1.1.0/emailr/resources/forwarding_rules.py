"""
Forwarding rules resource for managing email forwarding rules.
"""

from typing import Any, Dict, List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import (
    CreateForwardingRuleRequest,
    ForwardingRule,
    SuccessResponse,
)


class ForwardingRulesResource:
    """Synchronous forwarding rules resource."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        name: str,
        from_pattern: str,
        to_addresses: List[str],
        *,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Create an email forwarding rule.

        Args:
            name: Rule name
            from_pattern: Pattern to match sender
            to_addresses: Addresses to forward to
            active: Whether the rule is active

        Returns:
            Dict with id and success status
        """
        request = CreateForwardingRuleRequest(
            name=name,
            from_pattern=from_pattern,
            to_addresses=to_addresses,
            active=active,
        )
        return self._http.post("/v1/forwarding-rules", request.to_dict())

    def list(self) -> List[ForwardingRule]:
        """
        List all forwarding rules.

        Returns:
            List of forwarding rules
        """
        data = self._http.get("/v1/forwarding-rules")
        return [ForwardingRule.from_dict(r) for r in data["data"]]

    def delete(self, id: str) -> SuccessResponse:
        """
        Delete a forwarding rule.

        Args:
            id: Forwarding rule ID

        Returns:
            Success response
        """
        data = self._http.delete(f"/v1/forwarding-rules/{id}")
        return SuccessResponse(success=data.get("success", True))


class AsyncForwardingRulesResource:
    """Asynchronous forwarding rules resource."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def create(
        self,
        name: str,
        from_pattern: str,
        to_addresses: List[str],
        *,
        active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Create an email forwarding rule."""
        request = CreateForwardingRuleRequest(
            name=name,
            from_pattern=from_pattern,
            to_addresses=to_addresses,
            active=active,
        )
        return await self._http.post("/v1/forwarding-rules", request.to_dict())

    async def list(self) -> List[ForwardingRule]:
        """List all forwarding rules."""
        data = await self._http.get("/v1/forwarding-rules")
        return [ForwardingRule.from_dict(r) for r in data["data"]]

    async def delete(self, id: str) -> SuccessResponse:
        """Delete a forwarding rule."""
        data = await self._http.delete(f"/v1/forwarding-rules/{id}")
        return SuccessResponse(success=data.get("success", True))
