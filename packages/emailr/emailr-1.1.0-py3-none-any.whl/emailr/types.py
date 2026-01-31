"""
Type definitions for the Emailr SDK.

All types are implemented as dataclasses with full type hints.
These types correspond to the API request and response schemas.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

T = TypeVar("T")


# ============================================================================
# Common Types
# ============================================================================


@dataclass
class Pagination:
    """Pagination information for list responses."""

    page: int
    limit: int
    total: int
    pages: int


@dataclass
class PaginatedResponse(Generic[T]):
    """Generic paginated response wrapper."""

    data: List[T]
    pagination: Pagination


@dataclass
class SuccessResponse:
    """Simple success response."""

    success: bool


# ============================================================================
# Email Types
# ============================================================================


@dataclass
class Attachment:
    """Email attachment."""

    filename: str
    content: str  # Base64 encoded
    content_type: Optional[str] = None


@dataclass
class ReplyTo:
    """Reply-to configuration for threading."""

    in_reply_to: Optional[str] = None
    thread_id: Optional[str] = None
    parent_email_id: Optional[str] = None


@dataclass
class SendEmailRequest:
    """Request payload for sending an email."""

    to: Union[str, List[str]]
    from_: Optional[str] = None
    cc: Optional[Union[str, List[str]]] = None
    bcc: Optional[Union[str, List[str]]] = None
    subject: Optional[str] = None
    html: Optional[str] = None
    text: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, str]] = None
    attachments: Optional[List[Attachment]] = None
    reply_to: Optional[ReplyTo] = None
    reply_to_email: Optional[str] = None
    preview_text: Optional[str] = None
    scheduled_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"to": self.to}
        if self.from_ is not None:
            data["from"] = self.from_
        if self.cc is not None:
            data["cc"] = self.cc
        if self.bcc is not None:
            data["bcc"] = self.bcc
        if self.subject is not None:
            data["subject"] = self.subject
        if self.html is not None:
            data["html"] = self.html
        if self.text is not None:
            data["text"] = self.text
        if self.template_id is not None:
            data["template_id"] = self.template_id
        if self.template_data is not None:
            data["template_data"] = self.template_data
        if self.tags is not None:
            data["tags"] = self.tags
        if self.attachments is not None:
            data["attachments"] = [
                {
                    "filename": a.filename,
                    "content": a.content,
                    "contentType": a.content_type,
                }
                for a in self.attachments
            ]
        if self.reply_to is not None:
            data["replyTo"] = {
                "in_reply_to": self.reply_to.in_reply_to,
                "thread_id": self.reply_to.thread_id,
                "parent_email_id": self.reply_to.parent_email_id,
            }
        if self.reply_to_email is not None:
            data["reply_to_email"] = self.reply_to_email
        if self.preview_text is not None:
            data["preview_text"] = self.preview_text
        if self.scheduled_at is not None:
            data["scheduled_at"] = self.scheduled_at
        return data


@dataclass
class SendEmailResponse:
    """Response from sending an email."""

    success: bool
    message_id: str
    recipients: int
    status: str
    scheduled_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SendEmailResponse":
        """Create from API response dictionary."""
        return cls(
            success=data["success"],
            message_id=data["message_id"],
            recipients=data["recipients"],
            status=data["status"],
            scheduled_at=data.get("scheduled_at"),
        )


@dataclass
class Email:
    """Email record."""

    id: str
    organization_id: str
    message_id: str
    from_email: str
    to_email: str
    subject: Optional[str]
    html_content: Optional[str]
    text_content: Optional[str]
    template_id: Optional[str]
    status: str
    ses_message_id: Optional[str]
    broadcast_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    sent_at: Optional[str]
    delivered_at: Optional[str]
    opened_at: Optional[str]
    clicked_at: Optional[str]
    bounced_at: Optional[str]
    complained_at: Optional[str]
    scheduled_at: Optional[str]
    created_at: str
    thread_id: Optional[str]
    parent_email_id: Optional[str]
    attachments: Optional[List[Any]]
    clicked_links: Optional[List[Any]]
    opens: Optional[List[Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Email":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            message_id=data["message_id"],
            from_email=data["from_email"],
            to_email=data["to_email"],
            subject=data.get("subject"),
            html_content=data.get("html_content"),
            text_content=data.get("text_content"),
            template_id=data.get("template_id"),
            status=data["status"],
            ses_message_id=data.get("ses_message_id"),
            broadcast_id=data.get("broadcast_id"),
            metadata=data.get("metadata"),
            sent_at=data.get("sent_at"),
            delivered_at=data.get("delivered_at"),
            opened_at=data.get("opened_at"),
            clicked_at=data.get("clicked_at"),
            bounced_at=data.get("bounced_at"),
            complained_at=data.get("complained_at"),
            scheduled_at=data.get("scheduled_at"),
            created_at=data["created_at"],
            thread_id=data.get("thread_id"),
            parent_email_id=data.get("parent_email_id"),
            attachments=data.get("attachments"),
            clicked_links=data.get("clicked_links"),
            opens=data.get("opens"),
        )


@dataclass
class ListEmailsParams:
    """Parameters for listing emails."""

    page: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class ForwardEmailRequest:
    """Request payload for forwarding an email."""

    email_id: str
    to: Union[str, List[str]]
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"email_id": self.email_id, "to": self.to}
        if self.message is not None:
            data["message"] = self.message
        return data


@dataclass
class ForwardingRule:
    """Email forwarding rule."""

    id: str
    name: str
    from_pattern: str
    to_addresses: List[str]
    active: bool
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForwardingRule":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            from_pattern=data["from_pattern"],
            to_addresses=data["to_addresses"],
            active=data["active"],
            created_at=data["created_at"],
        )


@dataclass
class CreateForwardingRuleRequest:
    """Request payload for creating a forwarding rule."""

    name: str
    from_pattern: str
    to_addresses: List[str]
    active: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {
            "name": self.name,
            "from_pattern": self.from_pattern,
            "to_addresses": self.to_addresses,
        }
        if self.active is not None:
            data["active"] = self.active
        return data


# ============================================================================
# Contact Types
# ============================================================================


@dataclass
class Contact:
    """Contact record."""

    id: str
    organization_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    metadata: Optional[Dict[str, Any]]
    subscribed: bool
    unsubscribed_at: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            email=data["email"],
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            metadata=data.get("metadata"),
            subscribed=data["subscribed"],
            unsubscribed_at=data.get("unsubscribed_at"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class CreateContactRequest:
    """Request payload for creating a contact."""

    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    subscribed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"email": self.email}
        if self.first_name is not None:
            data["first_name"] = self.first_name
        if self.last_name is not None:
            data["last_name"] = self.last_name
        if self.subscribed is not None:
            data["subscribed"] = self.subscribed
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return data


@dataclass
class UpdateContactRequest:
    """Request payload for updating a contact."""

    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    subscribed: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.email is not None:
            data["email"] = self.email
        if self.first_name is not None:
            data["first_name"] = self.first_name
        if self.last_name is not None:
            data["last_name"] = self.last_name
        if self.subscribed is not None:
            data["subscribed"] = self.subscribed
        if self.metadata is not None:
            data["metadata"] = self.metadata
        return data


@dataclass
class ListContactsParams:
    """Parameters for listing contacts."""

    limit: Optional[int] = None
    offset: Optional[int] = None
    subscribed: Optional[bool] = None


@dataclass
class ContactListResponse:
    """Response from listing contacts."""

    contacts: List[Contact]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContactListResponse":
        """Create from API response dictionary."""
        return cls(
            contacts=[Contact.from_dict(c) for c in data["contacts"]],
            total=data["total"],
            limit=data["limit"],
            offset=data["offset"],
        )


@dataclass
class BulkCreateContactsRequest:
    """Request payload for bulk creating contacts."""

    contacts: List[CreateContactRequest]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {"contacts": [c.to_dict() for c in self.contacts]}


@dataclass
class BulkCreateContactsResponse:
    """Response from bulk creating contacts."""

    imported: int
    total: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BulkCreateContactsResponse":
        """Create from API response dictionary."""
        return cls(imported=data["imported"], total=data["total"])


# ============================================================================
# Template Types
# ============================================================================


@dataclass
class Template:
    """Email template record."""

    id: str
    organization_id: str
    name: str
    subject: str
    html_content: Optional[str]
    text_content: Optional[str]
    variables: Optional[List[str]]
    from_email: Optional[str]
    reply_to: Optional[str]
    preview_text: Optional[str]
    created_by: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Template":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            name=data["name"],
            subject=data["subject"],
            html_content=data.get("html_content"),
            text_content=data.get("text_content"),
            variables=data.get("variables"),
            from_email=data.get("from_email"),
            reply_to=data.get("reply_to"),
            preview_text=data.get("preview_text"),
            created_by=data.get("created_by"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class CreateTemplateRequest:
    """Request payload for creating a template."""

    name: str
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[List[str]] = None
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    preview_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"name": self.name, "subject": self.subject}
        if self.html_content is not None:
            data["html_content"] = self.html_content
        if self.text_content is not None:
            data["text_content"] = self.text_content
        if self.variables is not None:
            data["variables"] = self.variables
        if self.from_email is not None:
            data["from_email"] = self.from_email
        if self.reply_to is not None:
            data["reply_to"] = self.reply_to
        if self.preview_text is not None:
            data["preview_text"] = self.preview_text
        return data


@dataclass
class UpdateTemplateRequest:
    """Request payload for updating a template."""

    name: Optional[str] = None
    subject: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    variables: Optional[List[str]] = None
    from_email: Optional[str] = None
    reply_to: Optional[str] = None
    preview_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.subject is not None:
            data["subject"] = self.subject
        if self.html_content is not None:
            data["html_content"] = self.html_content
        if self.text_content is not None:
            data["text_content"] = self.text_content
        if self.variables is not None:
            data["variables"] = self.variables
        if self.from_email is not None:
            data["from_email"] = self.from_email
        if self.reply_to is not None:
            data["reply_to"] = self.reply_to
        if self.preview_text is not None:
            data["preview_text"] = self.preview_text
        return data


@dataclass
class ListTemplatesParams:
    """Parameters for listing templates."""

    page: Optional[int] = None
    limit: Optional[int] = None


# ============================================================================
# Domain Types
# ============================================================================


@dataclass
class DnsRecord:
    """DNS record for domain verification."""

    type: str  # 'TXT' | 'MX' | 'CNAME'
    name: str
    value: str
    priority: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DnsRecord":
        """Create from API response dictionary."""
        return cls(
            type=data["type"],
            name=data["name"],
            value=data["value"],
            priority=data.get("priority"),
        )


@dataclass
class DomainDnsRecords:
    """DNS records for domain configuration."""

    dkim: DnsRecord
    spf: DnsRecord
    dmarc: DnsRecord
    mail_from_mx: DnsRecord
    mail_from_spf: DnsRecord
    receiving_mx: DnsRecord

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainDnsRecords":
        """Create from API response dictionary."""
        return cls(
            dkim=DnsRecord.from_dict(data["dkim"]),
            spf=DnsRecord.from_dict(data["spf"]),
            dmarc=DnsRecord.from_dict(data["dmarc"]),
            mail_from_mx=DnsRecord.from_dict(data["mailFromMx"]),
            mail_from_spf=DnsRecord.from_dict(data["mailFromSpf"]),
            receiving_mx=DnsRecord.from_dict(data["receivingMx"]),
        )


@dataclass
class Domain:
    """Domain record."""

    id: str
    organization_id: str
    domain: str
    status: str
    verification_token: Optional[str]
    dkim_verified: bool
    spf_verified: bool
    dmarc_verified: bool
    cloudflare_zone_id: Optional[str]
    ses_identity_arn: Optional[str]
    created_at: str
    verified_at: Optional[str]
    dkim_tokens: Optional[List[str]]
    dns_records: Optional[DomainDnsRecords]
    dkim_selector: Optional[str]
    mail_from_subdomain: Optional[str]
    mail_from_verified: Optional[bool]
    receiving_enabled: Optional[bool]
    receiving_subdomain: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Domain":
        """Create from API response dictionary."""
        dns_records = None
        if data.get("dns_records"):
            dns_records = DomainDnsRecords.from_dict(data["dns_records"])
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            domain=data["domain"],
            status=data["status"],
            verification_token=data.get("verification_token"),
            dkim_verified=data["dkim_verified"],
            spf_verified=data["spf_verified"],
            dmarc_verified=data["dmarc_verified"],
            cloudflare_zone_id=data.get("cloudflare_zone_id"),
            ses_identity_arn=data.get("ses_identity_arn"),
            created_at=data["created_at"],
            verified_at=data.get("verified_at"),
            dkim_tokens=data.get("dkim_tokens"),
            dns_records=dns_records,
            dkim_selector=data.get("dkim_selector"),
            mail_from_subdomain=data.get("mail_from_subdomain"),
            mail_from_verified=data.get("mail_from_verified"),
            receiving_enabled=data.get("receiving_enabled"),
            receiving_subdomain=data.get("receiving_subdomain"),
        )


@dataclass
class AddDomainRequest:
    """Request payload for adding a domain."""

    domain: str
    receiving_subdomain: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"domain": self.domain}
        if self.receiving_subdomain is not None:
            data["receivingSubdomain"] = self.receiving_subdomain
        return data


@dataclass
class UpdateDomainRequest:
    """Request payload for updating a domain."""

    receiving_enabled: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.receiving_enabled is not None:
            data["receiving_enabled"] = self.receiving_enabled
        return data


@dataclass
class DomainVerificationStatus:
    """Domain verification status."""

    verified: bool
    status: str
    dkim_status: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainVerificationStatus":
        """Create from API response dictionary."""
        return cls(
            verified=data["verified"],
            status=data["status"],
            dkim_status=data.get("dkimStatus"),
        )


@dataclass
class DnsVerificationStatus:
    """DNS verification status for all records."""

    records: Dict[str, Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DnsVerificationStatus":
        """Create from API response dictionary."""
        return cls(records=data)


# ============================================================================
# Webhook Types
# ============================================================================


@dataclass
class Webhook:
    """Webhook record."""

    id: str
    organization_id: str
    name: str
    url: str
    events: List[str]
    secret: str
    active: bool
    created_by: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Webhook":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            name=data["name"],
            url=data["url"],
            events=data["events"],
            secret=data["secret"],
            active=data["active"],
            created_by=data.get("created_by"),
            created_at=data["created_at"],
        )


@dataclass
class CreateWebhookRequest:
    """Request payload for creating a webhook."""

    name: str
    url: str
    events: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {"name": self.name, "url": self.url, "events": self.events}


@dataclass
class UpdateWebhookRequest:
    """Request payload for updating a webhook."""

    name: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.url is not None:
            data["url"] = self.url
        if self.events is not None:
            data["events"] = self.events
        return data


@dataclass
class WebhookToggleResponse:
    """Response from enabling/disabling a webhook."""

    success: bool
    active: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookToggleResponse":
        """Create from API response dictionary."""
        return cls(success=data["success"], active=data["active"])


@dataclass
class WebhookDelivery:
    """Webhook delivery record."""

    id: str
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    response_status: Optional[int]
    response_body: Optional[str]
    attempt_count: int
    delivered_at: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebhookDelivery":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            webhook_id=data["webhook_id"],
            event_type=data["event_type"],
            payload=data["payload"],
            response_status=data.get("response_status"),
            response_body=data.get("response_body"),
            attempt_count=data["attempt_count"],
            delivered_at=data.get("delivered_at"),
            created_at=data["created_at"],
        )


@dataclass
class ListWebhooksParams:
    """Parameters for listing webhooks."""

    page: Optional[int] = None
    limit: Optional[int] = None


# ============================================================================
# Broadcast Types
# ============================================================================


@dataclass
class Broadcast:
    """Broadcast campaign record."""

    id: str
    organization_id: str
    name: str
    subject: str
    from_email: str
    template_id: Optional[str]
    segment_id: Optional[str]
    status: str
    total_recipients: Optional[int]
    sent_count: Optional[int]
    delivered_count: Optional[int]
    opened_count: Optional[int]
    clicked_count: Optional[int]
    bounced_count: Optional[int]
    scheduled_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_by: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Broadcast":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            name=data["name"],
            subject=data["subject"],
            from_email=data["from_email"],
            template_id=data.get("template_id"),
            segment_id=data.get("segment_id"),
            status=data["status"],
            total_recipients=data.get("total_recipients"),
            sent_count=data.get("sent_count"),
            delivered_count=data.get("delivered_count"),
            opened_count=data.get("opened_count"),
            clicked_count=data.get("clicked_count"),
            bounced_count=data.get("bounced_count"),
            scheduled_at=data.get("scheduled_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            created_by=data.get("created_by"),
            created_at=data["created_at"],
        )


@dataclass
class CreateBroadcastRequest:
    """Request payload for creating a broadcast."""

    name: str
    subject: str
    from_email: str
    template_id: Optional[str] = None
    segment_id: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    scheduled_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {
            "name": self.name,
            "subject": self.subject,
            "from_email": self.from_email,
        }
        if self.template_id is not None:
            data["template_id"] = self.template_id
        if self.segment_id is not None:
            data["segment_id"] = self.segment_id
        if self.html_content is not None:
            data["html_content"] = self.html_content
        if self.text_content is not None:
            data["text_content"] = self.text_content
        if self.scheduled_at is not None:
            data["scheduled_at"] = self.scheduled_at
        return data


@dataclass
class UpdateBroadcastRequest:
    """Request payload for updating a broadcast."""

    name: Optional[str] = None
    subject: Optional[str] = None
    from_email: Optional[str] = None
    template_id: Optional[str] = None
    segment_id: Optional[str] = None
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    scheduled_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.subject is not None:
            data["subject"] = self.subject
        if self.from_email is not None:
            data["from_email"] = self.from_email
        if self.template_id is not None:
            data["template_id"] = self.template_id
        if self.segment_id is not None:
            data["segment_id"] = self.segment_id
        if self.html_content is not None:
            data["html_content"] = self.html_content
        if self.text_content is not None:
            data["text_content"] = self.text_content
        if self.scheduled_at is not None:
            data["scheduled_at"] = self.scheduled_at
        return data


@dataclass
class SendBroadcastResponse:
    """Response from sending a broadcast."""

    success: bool
    sent: int
    total: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SendBroadcastResponse":
        """Create from API response dictionary."""
        return cls(success=data["success"], sent=data["sent"], total=data["total"])


@dataclass
class ListBroadcastsParams:
    """Parameters for listing broadcasts."""

    page: Optional[int] = None
    limit: Optional[int] = None
    status: Optional[str] = None


@dataclass
class BroadcastStats:
    """Broadcast statistics."""

    total_recipients: int
    sent_count: int
    delivered_count: int
    opened_count: int
    clicked_count: int
    bounced_count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BroadcastStats":
        """Create from API response dictionary."""
        return cls(
            total_recipients=data["total_recipients"],
            sent_count=data["sent_count"],
            delivered_count=data["delivered_count"],
            opened_count=data["opened_count"],
            clicked_count=data["clicked_count"],
            bounced_count=data["bounced_count"],
        )


# ============================================================================
# Segment Types
# ============================================================================


@dataclass
class Segment:
    """Contact segment record."""

    id: str
    organization_id: str
    name: str
    description: Optional[str]
    conditions: Dict[str, Any]
    created_by: Optional[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Segment":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            name=data["name"],
            description=data.get("description"),
            conditions=data["conditions"],
            created_by=data.get("created_by"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )


@dataclass
class CreateSegmentRequest:
    """Request payload for creating a segment."""

    name: str
    conditions: Dict[str, Any]
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"name": self.name, "conditions": self.conditions}
        if self.description is not None:
            data["description"] = self.description
        return data


@dataclass
class UpdateSegmentRequest:
    """Request payload for updating a segment."""

    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.description is not None:
            data["description"] = self.description
        if self.conditions is not None:
            data["conditions"] = self.conditions
        return data


@dataclass
class ListSegmentsParams:
    """Parameters for listing segments."""

    page: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class SegmentContactsResponse:
    """Response from getting segment contacts."""

    contacts: List[Contact]
    total: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SegmentContactsResponse":
        """Create from API response dictionary."""
        return cls(
            contacts=[Contact.from_dict(c) for c in data["contacts"]],
            total=data["total"],
        )


@dataclass
class SegmentCountResponse:
    """Response from getting segment contact count."""

    count: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SegmentCountResponse":
        """Create from API response dictionary."""
        return cls(count=data["count"])


# ============================================================================
# API Key Types
# ============================================================================


@dataclass
class ApiKey:
    """API key record."""

    id: str
    organization_id: str
    name: str
    key: Optional[str]  # Only returned when creating
    permissions: Optional[List[str]]
    last_used_at: Optional[str]
    created_by: Optional[str]
    created_at: str
    revoked_at: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApiKey":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            name=data["name"],
            key=data.get("key"),
            permissions=data.get("permissions"),
            last_used_at=data.get("last_used_at"),
            created_by=data.get("created_by"),
            created_at=data["created_at"],
            revoked_at=data.get("revoked_at"),
        )


@dataclass
class CreateApiKeyRequest:
    """Request payload for creating an API key."""

    name: str
    permissions: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {"name": self.name}
        if self.permissions is not None:
            data["permissions"] = self.permissions
        return data


@dataclass
class ListApiKeysParams:
    """Parameters for listing API keys."""

    page: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class ApiKeyListItem:
    """API key list item (without full key)."""

    id: str
    name: str
    permissions: Optional[List[str]]
    last_used_at: Optional[str]
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApiKeyListItem":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            permissions=data.get("permissions"),
            last_used_at=data.get("last_used_at"),
            created_at=data["created_at"],
        )


# ============================================================================
# SMTP Types
# ============================================================================


@dataclass
class SmtpPorts:
    """SMTP port configuration."""

    tls: int
    ssl: int
    tls_alternative: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmtpPorts":
        """Create from API response dictionary."""
        return cls(
            tls=data["tls"],
            ssl=data["ssl"],
            tls_alternative=data["tls_alternative"],
        )


@dataclass
class SmtpCredentials:
    """SMTP credentials."""

    server: str
    ports: SmtpPorts
    username: str
    password: str
    encryption: str
    note: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmtpCredentials":
        """Create from API response dictionary."""
        return cls(
            server=data["server"],
            ports=SmtpPorts.from_dict(data["ports"]),
            username=data["username"],
            password=data["password"],
            encryption=data["encryption"],
            note=data["note"],
        )


# ============================================================================
# Settings Types
# ============================================================================


@dataclass
class Organization:
    """Organization record."""

    id: str
    name: str
    slug: str
    plan: Optional[str]
    billing_email: Optional[str]
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    usage_limit: Optional[int]
    created_at: str
    updated_at: str
    ses_configuration_set: Optional[str]
    ses_tenant_name: Optional[str]
    ses_tenant_id: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Organization":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            slug=data["slug"],
            plan=data.get("plan"),
            billing_email=data.get("billing_email"),
            stripe_customer_id=data.get("stripe_customer_id"),
            stripe_subscription_id=data.get("stripe_subscription_id"),
            usage_limit=data.get("usage_limit"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            ses_configuration_set=data.get("ses_configuration_set"),
            ses_tenant_name=data.get("ses_tenant_name"),
            ses_tenant_id=data.get("ses_tenant_id"),
        )


@dataclass
class UpdateOrganizationRequest:
    """Request payload for updating organization."""

    name: Optional[str] = None
    billing_email: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.name is not None:
            data["name"] = self.name
        if self.billing_email is not None:
            data["billing_email"] = self.billing_email
        return data


@dataclass
class Profile:
    """User profile."""

    id: str
    email: str
    full_name: Optional[str]
    avatar_url: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """Create from API response dictionary."""
        return cls(
            id=data["id"],
            email=data["email"],
            full_name=data.get("full_name"),
            avatar_url=data.get("avatar_url"),
        )


@dataclass
class TeamMember:
    """Team member record."""

    id: str
    organization_id: str
    user_id: str
    role: Optional[str]
    created_at: str
    profiles: Optional[Profile]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TeamMember":
        """Create from API response dictionary."""
        profiles = None
        if data.get("profiles"):
            profiles = Profile.from_dict(data["profiles"])
        return cls(
            id=data["id"],
            organization_id=data["organization_id"],
            user_id=data["user_id"],
            role=data.get("role"),
            created_at=data["created_at"],
            profiles=profiles,
        )


@dataclass
class UnsubscribeSettings:
    """Unsubscribe settings."""

    id: Optional[str] = None
    organization_id: Optional[str] = None
    custom_message: Optional[str] = None
    redirect_url: Optional[str] = None
    one_click_enabled: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    company_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnsubscribeSettings":
        """Create from API response dictionary."""
        return cls(
            id=data.get("id"),
            organization_id=data.get("organization_id"),
            custom_message=data.get("custom_message"),
            redirect_url=data.get("redirect_url"),
            one_click_enabled=data.get("one_click_enabled"),
            logo_url=data.get("logo_url"),
            primary_color=data.get("primary_color"),
            company_name=data.get("company_name"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


@dataclass
class UpdateUnsubscribeSettingsRequest:
    """Request payload for updating unsubscribe settings."""

    custom_message: Optional[str] = None
    redirect_url: Optional[str] = None
    one_click_enabled: Optional[bool] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    company_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        data: Dict[str, Any] = {}
        if self.custom_message is not None:
            data["custom_message"] = self.custom_message
        if self.redirect_url is not None:
            data["redirect_url"] = self.redirect_url
        if self.one_click_enabled is not None:
            data["one_click_enabled"] = self.one_click_enabled
        if self.logo_url is not None:
            data["logo_url"] = self.logo_url
        if self.primary_color is not None:
            data["primary_color"] = self.primary_color
        if self.company_name is not None:
            data["company_name"] = self.company_name
        return data


# ============================================================================
# Metrics Types
# ============================================================================


@dataclass
class UsageMetric:
    """Daily usage metric."""

    date: str
    emails_sent: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageMetric":
        """Create from API response dictionary."""
        return cls(
            date=data["date"],
            emails_sent=data["emails_sent"],
        )


@dataclass
class EmailMetrics:
    """Aggregated email metrics."""

    total: int
    sent: int
    delivered: int
    bounced: int
    complained: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailMetrics":
        """Create from API response dictionary."""
        return cls(
            total=data["total"],
            sent=data["sent"],
            delivered=data["delivered"],
            bounced=data["bounced"],
            complained=data["complained"],
        )
