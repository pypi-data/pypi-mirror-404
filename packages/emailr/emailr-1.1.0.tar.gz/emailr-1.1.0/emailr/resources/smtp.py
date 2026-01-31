"""
SMTP resource for getting SMTP credentials.
"""

from emailr.http import AsyncHttpClient, HttpClient
from emailr.types import SmtpCredentials


class SmtpResource:
    """Synchronous SMTP resource."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def get_credentials(self) -> SmtpCredentials:
        """
        Get SMTP credentials for sending emails.
        The password is your API key.

        Returns:
            SMTP credentials
        """
        data = self._http.get("/v1/smtp/credentials")
        return SmtpCredentials.from_dict(data)


class AsyncSmtpResource:
    """Asynchronous SMTP resource."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def get_credentials(self) -> SmtpCredentials:
        """Get SMTP credentials for sending emails."""
        data = await self._http.get("/v1/smtp/credentials")
        return SmtpCredentials.from_dict(data)
