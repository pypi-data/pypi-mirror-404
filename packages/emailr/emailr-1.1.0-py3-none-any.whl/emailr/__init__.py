"""
Emailr SDK for Python

Official Python SDK for the Emailr email API service.
Provides both synchronous and asynchronous clients for sending emails,
managing contacts, templates, domains, webhooks, broadcasts, and segments.

Example usage:
    >>> from emailr import Emailr
    >>> client = Emailr(api_key="your-api-key")
    >>> result = client.emails.send(
    ...     to="recipient@example.com",
    ...     from_="sender@yourdomain.com",
    ...     subject="Hello!",
    ...     html="<h1>Hello World</h1>"
    ... )

For async usage:
    >>> from emailr import AsyncEmailr
    >>> async with AsyncEmailr(api_key="your-api-key") as client:
    ...     result = await client.emails.send(
    ...         to="recipient@example.com",
    ...         from_="sender@yourdomain.com",
    ...         subject="Hello!",
    ...         html="<h1>Hello World</h1>"
    ...     )
"""

from emailr.client import AsyncEmailr, Emailr
from emailr.errors import (
    AuthenticationError,
    EmailrError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from emailr.types import (
    AddDomainRequest,
    ApiKey,
    Attachment,
    Broadcast,
    BroadcastStats,
    BulkCreateContactsRequest,
    BulkCreateContactsResponse,
    Contact,
    ContactListResponse,
    CreateApiKeyRequest,
    CreateBroadcastRequest,
    CreateContactRequest,
    CreateForwardingRuleRequest,
    CreateSegmentRequest,
    CreateTemplateRequest,
    CreateWebhookRequest,
    DnsRecord,
    DnsVerificationStatus,
    Domain,
    DomainDnsRecords,
    DomainVerificationStatus,
    Email,
    ForwardEmailRequest,
    ForwardingRule,
    ListApiKeysParams,
    ListBroadcastsParams,
    ListContactsParams,
    ListEmailsParams,
    ListSegmentsParams,
    ListTemplatesParams,
    ListWebhooksParams,
    PaginatedResponse,
    Pagination,
    ReplyTo,
    Segment,
    SegmentContactsResponse,
    SegmentCountResponse,
    SendBroadcastResponse,
    SendEmailRequest,
    SendEmailResponse,
    SuccessResponse,
    Template,
    UpdateBroadcastRequest,
    UpdateContactRequest,
    UpdateDomainRequest,
    UpdateSegmentRequest,
    UpdateTemplateRequest,
    UpdateWebhookRequest,
    Webhook,
    WebhookDelivery,
    WebhookToggleResponse,
)

__version__ = "1.0.0"

__all__ = [
    # Clients
    "Emailr",
    "AsyncEmailr",
    # Errors
    "EmailrError",
    "NetworkError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    # Types - Common
    "PaginatedResponse",
    "Pagination",
    "SuccessResponse",
    # Types - Email
    "Attachment",
    "ReplyTo",
    "SendEmailRequest",
    "SendEmailResponse",
    "Email",
    "ListEmailsParams",
    "ForwardEmailRequest",
    "ForwardingRule",
    "CreateForwardingRuleRequest",
    # Types - Contact
    "Contact",
    "CreateContactRequest",
    "UpdateContactRequest",
    "ListContactsParams",
    "ContactListResponse",
    "BulkCreateContactsRequest",
    "BulkCreateContactsResponse",
    # Types - Template
    "Template",
    "CreateTemplateRequest",
    "UpdateTemplateRequest",
    "ListTemplatesParams",
    # Types - Domain
    "DnsRecord",
    "DomainDnsRecords",
    "Domain",
    "AddDomainRequest",
    "UpdateDomainRequest",
    "DomainVerificationStatus",
    "DnsVerificationStatus",
    # Types - Webhook
    "Webhook",
    "CreateWebhookRequest",
    "UpdateWebhookRequest",
    "WebhookToggleResponse",
    "WebhookDelivery",
    "ListWebhooksParams",
    # Types - Broadcast
    "Broadcast",
    "BroadcastStats",
    "CreateBroadcastRequest",
    "UpdateBroadcastRequest",
    "SendBroadcastResponse",
    "ListBroadcastsParams",
    # Types - Segment
    "Segment",
    "SegmentContactsResponse",
    "SegmentCountResponse",
    "CreateSegmentRequest",
    "UpdateSegmentRequest",
    "ListSegmentsParams",
    # Types - API Key
    "ApiKey",
    "CreateApiKeyRequest",
    "ListApiKeysParams",
]
