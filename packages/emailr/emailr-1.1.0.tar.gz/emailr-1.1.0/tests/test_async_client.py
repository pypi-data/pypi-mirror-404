"""
Tests for the asynchronous AsyncEmailr client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from emailr import AsyncEmailr
from emailr.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestAsyncEmailrClient:
    """Tests for the AsyncEmailr async client."""

    def test_create_client_with_api_key(self, api_key):
        """Should create an async client with API key."""
        client = AsyncEmailr(api_key=api_key)
        
        assert client is not None

    def test_create_client_with_custom_base_url(self, api_key, base_url):
        """Should create an async client with custom base URL."""
        client = AsyncEmailr(api_key=api_key, base_url=base_url)
        
        assert client is not None

    def test_client_has_resources(self, async_emailr_client):
        """Should have all resource accessors."""
        assert hasattr(async_emailr_client, 'emails')
        assert hasattr(async_emailr_client, 'contacts')
        assert hasattr(async_emailr_client, 'templates')
        assert hasattr(async_emailr_client, 'domains')
        assert hasattr(async_emailr_client, 'webhooks')
        assert hasattr(async_emailr_client, 'broadcasts')
        assert hasattr(async_emailr_client, 'segments')

    @pytest.mark.asyncio
    async def test_context_manager(self, api_key):
        """Should work as async context manager."""
        async with AsyncEmailr(api_key=api_key) as client:
            assert client is not None


class TestAsyncEmailsResource:
    """Tests for the async emails resource."""

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_send_email(self, mock_client_class, api_key, sample_email):
        """Should send an email asynchronously."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = sample_email
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        result = await client.emails.send(
            from_address="sender@example.com",
            to=["recipient@example.com"],
            subject="Test Email",
            html="<p>Hello!</p>"
        )

        assert result is not None
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_get_email(self, mock_client_class, api_key, sample_email):
        """Should get an email by ID asynchronously."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = sample_email
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        result = await client.emails.get("email_123")

        assert result is not None

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_list_emails(self, mock_client_class, api_key, sample_email):
        """Should list emails asynchronously."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"data": [sample_email], "pagination": {}}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        result = await client.emails.list()

        assert result is not None


class TestAsyncContactsResource:
    """Tests for the async contacts resource."""

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_create_contact(self, mock_client_class, api_key, sample_contact):
        """Should create a contact asynchronously."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json.return_value = sample_contact
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        result = await client.contacts.create(
            email="user@example.com",
            first_name="John",
            last_name="Doe"
        )

        assert result is not None

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_get_contact(self, mock_client_class, api_key, sample_contact):
        """Should get a contact by ID asynchronously."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = sample_contact
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        result = await client.contacts.get("contact_123")

        assert result is not None

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_delete_contact(self, mock_client_class, api_key):
        """Should delete a contact asynchronously."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.is_success = True
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        await client.contacts.delete("contact_123")

        mock_client.request.assert_called_once()


class TestAsyncErrorHandling:
    """Tests for error handling in the async client."""

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_authentication_error(self, mock_client_class, api_key):
        """Should raise AuthenticationError for 401 response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.is_success = False
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        
        with pytest.raises(AuthenticationError):
            await client.emails.list()

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_not_found_error(self, mock_client_class, api_key):
        """Should raise NotFoundError for 404 response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_success = False
        mock_response.json.return_value = {"error": {"message": "Not found"}}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        
        with pytest.raises(NotFoundError):
            await client.emails.get("nonexistent")

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_rate_limit_error(self, mock_client_class, api_key):
        """Should raise RateLimitError for 429 response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.is_success = False
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        
        with pytest.raises(RateLimitError) as exc_info:
            await client.emails.list()
        
        assert exc_info.value.retry_after == 60

    @pytest.mark.asyncio
    @patch('emailr.http.httpx.AsyncClient')
    async def test_validation_error(self, mock_client_class, api_key):
        """Should raise ValidationError for 400 response."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.is_success = False
        mock_response.json.return_value = {
            "error": {
                "message": "Validation failed",
                "details": {"email": ["Invalid format"]}
            }
        }
        mock_client.request = AsyncMock(return_value=mock_response)
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        client = AsyncEmailr(api_key=api_key)
        
        with pytest.raises(ValidationError) as exc_info:
            await client.contacts.create(email="invalid")
        
        assert exc_info.value.details == {"email": ["Invalid format"]}
