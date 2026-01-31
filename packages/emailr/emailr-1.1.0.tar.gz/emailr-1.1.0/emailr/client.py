"""
Main client classes for the Emailr SDK.

Provides both synchronous (Emailr) and asynchronous (AsyncEmailr) clients
for interacting with the Emailr API.
"""

from types import TracebackType
from typing import Optional, Type

from emailr.http import AsyncHttpClient, HttpClient
from emailr.resources import (
    AsyncBroadcastsResource,
    AsyncContactsResource,
    AsyncDomainsResource,
    AsyncEmailsResource,
    AsyncSegmentsResource,
    AsyncTemplatesResource,
    AsyncWebhooksResource,
    AsyncApiKeysResource,
    AsyncSmtpResource,
    AsyncSettingsResource,
    AsyncMetricsResource,
    AsyncForwardingRulesResource,
    BroadcastsResource,
    ContactsResource,
    DomainsResource,
    EmailsResource,
    SegmentsResource,
    TemplatesResource,
    WebhooksResource,
    ApiKeysResource,
    SmtpResource,
    SettingsResource,
    MetricsResource,
    ForwardingRulesResource,
)

DEFAULT_BASE_URL = "https://api.emailr.dev"
DEFAULT_TIMEOUT = 30.0


class Emailr:
    """
    Synchronous Emailr API client.

    Example usage:
        >>> from emailr import Emailr
        >>> client = Emailr(api_key="your-api-key")
        >>> result = client.emails.send(
        ...     to="recipient@example.com",
        ...     from_="sender@yourdomain.com",
        ...     subject="Hello!",
        ...     html="<h1>Hello World</h1>"
        ... )
        >>> print(result.message_id)

    Args:
        api_key: Your Emailr API key
        base_url: Base URL for the API (default: https://api.emailr.dev)
        timeout: Request timeout in seconds (default: 30.0)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("API key is required")

        self._http = HttpClient(api_key=api_key, base_url=base_url, timeout=timeout)

        # Initialize resources
        self.emails = EmailsResource(self._http)
        self.contacts = ContactsResource(self._http)
        self.templates = TemplatesResource(self._http)
        self.domains = DomainsResource(self._http)
        self.webhooks = WebhooksResource(self._http)
        self.broadcasts = BroadcastsResource(self._http)
        self.segments = SegmentsResource(self._http)
        self.api_keys = ApiKeysResource(self._http)
        self.smtp = SmtpResource(self._http)
        self.settings = SettingsResource(self._http)
        self.metrics = MetricsResource(self._http)
        self.forwarding_rules = ForwardingRulesResource(self._http)


    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._http.close()

    def __enter__(self) -> "Emailr":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit context manager and close client."""
        self.close()


class AsyncEmailr:
    """
    Asynchronous Emailr API client.

    Example usage:
        >>> from emailr import AsyncEmailr
        >>> async with AsyncEmailr(api_key="your-api-key") as client:
        ...     result = await client.emails.send(
        ...         to="recipient@example.com",
        ...         from_="sender@yourdomain.com",
        ...         subject="Hello!",
        ...         html="<h1>Hello World</h1>"
        ...     )
        ...     print(result.message_id)

    Args:
        api_key: Your Emailr API key
        base_url: Base URL for the API (default: https://api.emailr.dev)
        timeout: Request timeout in seconds (default: 30.0)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("API key is required")

        self._http = AsyncHttpClient(api_key=api_key, base_url=base_url, timeout=timeout)

        # Initialize resources
        self.emails = AsyncEmailsResource(self._http)
        self.contacts = AsyncContactsResource(self._http)
        self.templates = AsyncTemplatesResource(self._http)
        self.domains = AsyncDomainsResource(self._http)
        self.webhooks = AsyncWebhooksResource(self._http)
        self.broadcasts = AsyncBroadcastsResource(self._http)
        self.segments = AsyncSegmentsResource(self._http)
        self.api_keys = AsyncApiKeysResource(self._http)
        self.smtp = AsyncSmtpResource(self._http)
        self.settings = AsyncSettingsResource(self._http)
        self.metrics = AsyncMetricsResource(self._http)
        self.forwarding_rules = AsyncForwardingRulesResource(self._http)

    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._http.close()

    async def __aenter__(self) -> "AsyncEmailr":
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Exit async context manager and close client."""
        await self.close()
