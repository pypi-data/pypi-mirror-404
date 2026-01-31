"""
Metrics resource for usage and email metrics.
"""

from typing import List, Optional

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import UsageMetric, EmailMetrics


class MetricsResource:
    """Synchronous metrics resource."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_usage(self, days: int = 30) -> List[UsageMetric]:
        """
        Get usage metrics for a specified number of days.

        Args:
            days: Number of days to get metrics for (default: 30)

        Returns:
            List of daily usage metrics
        """
        data = self._http.get("/v1/metrics/usage", params={"days": str(days)})
        if isinstance(data, list):
            return [UsageMetric.from_dict(m) for m in data]
        return [UsageMetric.from_dict(m) for m in data.get("data", data)]

    def get_email_metrics(self) -> EmailMetrics:
        """
        Get aggregated email delivery metrics.

        Returns:
            Email metrics
        """
        data = self._http.get("/v1/metrics/emails")
        return EmailMetrics.from_dict(data)


class AsyncMetricsResource:
    """Asynchronous metrics resource."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def get_usage(self, days: int = 30) -> List[UsageMetric]:
        """Get usage metrics for a specified number of days."""
        data = await self._http.get("/v1/metrics/usage", params={"days": str(days)})
        if isinstance(data, list):
            return [UsageMetric.from_dict(m) for m in data]
        return [UsageMetric.from_dict(m) for m in data.get("data", data)]

    async def get_email_metrics(self) -> EmailMetrics:
        """Get aggregated email delivery metrics."""
        data = await self._http.get("/v1/metrics/emails")
        return EmailMetrics.from_dict(data)
