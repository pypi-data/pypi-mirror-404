"""
Tests for the synchronous Emailr client.
"""

import pytest
from unittest.mock import MagicMock, patch
import httpx

from emailr import Emailr
from emailr.errors import (
    EmailrError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestEmailrClient:
    """Tests for the Emailr sync client."""

    def test_create_client_with_api_key(self, api_key):
        """Should create a client with API key."""
        client = Emailr(api_key=api_key)
        
        assert client is not None
        assert client._api_key == api_key

    def test_create_client_with_custom_base_url(self, api_key, base_url):
        """Should create a client with custom base URL."""
        client = Emailr(api_key=api_key, base_url=base_url)
        
        assert client._base_url == base_url

    def test_client_has_resources(self, emailr_client):
        """Should have all resource accessors."""
        assert hasattr(emailr_client, 'emails')
        assert hasattr(emailr_client, 'contacts')
        assert hasattr(emailr_client, 'templates')
        assert hasattr(emailr_client, 'domains')
        assert hasattr(emailr_client, 'webhooks')
        assert hasattr(emailr_client, 'broadcasts')
        assert hasattr(emailr_client, 'segments')


class TestEmailsResource:
    """Tests for the emails resource."""

    @patch('emailr.http.httpx.Client')
    def test_send_email(self, mock_client_class, api_key, sample_email):
        """Should send an email."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = sample_email
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        result = client.emails.send(
            from_address="sender@example.com",
            to=["recipient@example.com"],
            subject="Test Email",
            html="<p>Hello!</p>"
        )

        assert result is not None
        mock_client.request.assert_called_once()

    @patch('emailr.http.httpx.Client')
    def test_get_email(self, mock_client_class, api_key, sample_email):
        """Should get an email by ID."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = sample_email
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        result = client.emails.get("email_123")

        assert result is not None

    @patch('emailr.http.httpx.Client')
    def test_list_emails(self, mock_client_class, api_key, sample_email):
        """Should list emails."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = {"data": [sample_email], "pagination": {}}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        result = client.emails.list()

        assert result is not None


class TestContactsResource:
    """Tests for the contacts resource."""

    @patch('emailr.http.httpx.Client')
    def test_create_contact(self, mock_client_class, api_key, sample_contact):
        """Should create a contact."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.is_success = True
        mock_response.json.return_value = sample_contact
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        result = client.contacts.create(
            email="user@example.com",
            first_name="John",
            last_name="Doe"
        )

        assert result is not None

    @patch('emailr.http.httpx.Client')
    def test_get_contact(self, mock_client_class, api_key, sample_contact):
        """Should get a contact by ID."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.is_success = True
        mock_response.json.return_value = sample_contact
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        result = client.contacts.get("contact_123")

        assert result is not None

    @patch('emailr.http.httpx.Client')
    def test_delete_contact(self, mock_client_class, api_key):
        """Should delete a contact."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.is_success = True
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        client.contacts.delete("contact_123")

        mock_client.request.assert_called_once()


class TestErrorHandling:
    """Tests for error handling in the client."""

    @patch('emailr.http.httpx.Client')
    def test_authentication_error(self, mock_client_class, api_key):
        """Should raise AuthenticationError for 401 response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.is_success = False
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        
        with pytest.raises(AuthenticationError):
            client.emails.list()

    @patch('emailr.http.httpx.Client')
    def test_not_found_error(self, mock_client_class, api_key):
        """Should raise NotFoundError for 404 response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.is_success = False
        mock_response.json.return_value = {"error": {"message": "Not found"}}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        
        with pytest.raises(NotFoundError):
            client.emails.get("nonexistent")

    @patch('emailr.http.httpx.Client')
    def test_rate_limit_error(self, mock_client_class, api_key):
        """Should raise RateLimitError for 429 response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.is_success = False
        mock_response.headers = {"Retry-After": "60"}
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        
        with pytest.raises(RateLimitError) as exc_info:
            client.emails.list()
        
        assert exc_info.value.retry_after == 60

    @patch('emailr.http.httpx.Client')
    def test_validation_error(self, mock_client_class, api_key):
        """Should raise ValidationError for 400 response."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.is_success = False
        mock_response.json.return_value = {
            "error": {
                "message": "Validation failed",
                "details": {"email": ["Invalid format"]}
            }
        }
        mock_client.request.return_value = mock_response
        mock_client_class.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_client_class.return_value.__exit__ = MagicMock(return_value=False)

        client = Emailr(api_key=api_key)
        
        with pytest.raises(ValidationError) as exc_info:
            client.contacts.create(email="invalid")
        
        assert exc_info.value.details == {"email": ["Invalid format"]}
