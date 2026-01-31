"""
Resource modules for the Emailr SDK.

Each resource provides both synchronous and asynchronous methods
for interacting with the corresponding API endpoints.
"""

from emailr.resources.broadcasts import AsyncBroadcastsResource, BroadcastsResource
from emailr.resources.contacts import AsyncContactsResource, ContactsResource
from emailr.resources.domains import AsyncDomainsResource, DomainsResource
from emailr.resources.emails import AsyncEmailsResource, EmailsResource
from emailr.resources.segments import AsyncSegmentsResource, SegmentsResource
from emailr.resources.templates import AsyncTemplatesResource, TemplatesResource
from emailr.resources.webhooks import AsyncWebhooksResource, WebhooksResource
from emailr.resources.api_keys import AsyncApiKeysResource, ApiKeysResource
from emailr.resources.smtp import AsyncSmtpResource, SmtpResource
from emailr.resources.settings import AsyncSettingsResource, SettingsResource
from emailr.resources.metrics import AsyncMetricsResource, MetricsResource
from emailr.resources.forwarding_rules import AsyncForwardingRulesResource, ForwardingRulesResource

__all__ = [
    # Sync resources
    "EmailsResource",
    "ContactsResource",
    "TemplatesResource",
    "DomainsResource",
    "WebhooksResource",
    "BroadcastsResource",
    "SegmentsResource",
    "ApiKeysResource",
    "SmtpResource",
    "SettingsResource",
    "MetricsResource",
    "ForwardingRulesResource",
    # Async resources
    "AsyncEmailsResource",
    "AsyncContactsResource",
    "AsyncTemplatesResource",
    "AsyncDomainsResource",
    "AsyncWebhooksResource",
    "AsyncBroadcastsResource",
    "AsyncSegmentsResource",
    "AsyncApiKeysResource",
    "AsyncSmtpResource",
    "AsyncSettingsResource",
    "AsyncMetricsResource",
    "AsyncForwardingRulesResource",
]
