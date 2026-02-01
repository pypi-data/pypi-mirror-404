#!/usr/bin/env python3
"""
MCP Server for Sendook - AI Email Communication Platform.

This server provides tools to interact with Sendook's API, enabling AI agents
to send and receive emails, manage inboxes, handle conversation threads,
and configure webhooks for real-time notifications.

Environment Variables:
    SENDOOK_API_KEY: API key for Sendook authentication (required)
    SENDOOK_API_URL: Base URL for Sendook API (optional, defaults to production)
"""

import json
import os
import sys
from enum import Enum
from typing import Optional, List, Dict, Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Initialize the MCP server
mcp = FastMCP("sendook_mcp")

# Constants
API_BASE_URL = os.getenv("SENDOOK_API_URL", "https://api.sendook.com")
API_KEY = os.getenv("SENDOOK_API_KEY", "")
CHARACTER_LIMIT = 25000
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# Response format enum
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


# Webhook event types
class WebhookEvent(str, Enum):
    """Available webhook event types."""
    INBOX_CREATED = "inbox.created"
    INBOX_DELETED = "inbox.deleted"
    INBOX_UPDATED = "inbox.updated"
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_DELIVERED = "message.delivered"
    MESSAGE_BOUNCED = "message.bounced"
    MESSAGE_COMPLAINED = "message.complained"
    MESSAGE_REJECTED = "message.rejected"


# ============================================================================
# Pydantic Input Models
# ============================================================================

class CreateInboxInput(BaseModel):
    """Input for creating a new inbox."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: Optional[str] = Field(
        default=None,
        description="Display name for the inbox (e.g., 'Customer Support Bot')",
        max_length=255
    )
    email: Optional[str] = Field(
        default=None,
        description="Custom email address; auto-generated if omitted (e.g., 'support@agents.example.com')",
        max_length=255
    )


class InboxIdInput(BaseModel):
    """Input requiring an inbox ID."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox identifier (e.g., 'ibox_01J3ZKZ0BRQ9SSJK1GRSCX4N4Z')",
        min_length=1
    )


class ListInboxesInput(BaseModel):
    """Input for listing inboxes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class AttachmentInput(BaseModel):
    """Email attachment structure."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    content: str = Field(
        ...,
        description="Base64-encoded file content"
    )
    name: str = Field(
        ...,
        description="Filename with extension (e.g., 'document.pdf')",
        min_length=1,
        max_length=255
    )
    content_type: str = Field(
        ...,
        description="MIME type (e.g., 'application/pdf', 'image/png')",
        min_length=1
    )


class SendMessageInput(BaseModel):
    """Input for sending an email message."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox ID to send from",
        min_length=1
    )
    to: List[str] = Field(
        ...,
        description="Recipient email addresses (e.g., ['user@example.com'])",
        min_length=1,
        max_length=50
    )
    subject: str = Field(
        ...,
        description="Email subject line",
        min_length=1,
        max_length=998
    )
    text: Optional[str] = Field(
        default=None,
        description="Plain text version of the email body"
    )
    html: Optional[str] = Field(
        default=None,
        description="HTML version of the email body"
    )
    cc: Optional[List[str]] = Field(
        default=None,
        description="CC recipient email addresses",
        max_length=50
    )
    bcc: Optional[List[str]] = Field(
        default=None,
        description="BCC recipient email addresses",
        max_length=50
    )
    labels: Optional[List[str]] = Field(
        default=None,
        description="Custom labels for categorization (e.g., ['outbound', 'welcome'])",
        max_length=20
    )
    attachments: Optional[List[AttachmentInput]] = Field(
        default=None,
        description="File attachments (base64 encoded)",
        max_length=10
    )

    @field_validator("to", "cc", "bcc")
    @classmethod
    def validate_emails(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        for email in v:
            if "@" not in email:
                raise ValueError(f"Invalid email address: {email}")
        return v


class ReplyToMessageInput(BaseModel):
    """Input for replying to a message."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox ID containing the message",
        min_length=1
    )
    message_id: str = Field(
        ...,
        description="Message ID to reply to",
        min_length=1
    )
    text: Optional[str] = Field(
        default=None,
        description="Plain text reply body"
    )
    html: Optional[str] = Field(
        default=None,
        description="HTML reply body"
    )


class ListMessagesInput(BaseModel):
    """Input for listing messages in an inbox."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox ID to list messages from",
        min_length=1
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional filter expression to search messages"
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Maximum number of messages to return",
        ge=1,
        le=MAX_LIMIT
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetMessageInput(BaseModel):
    """Input for getting a specific message."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox ID containing the message",
        min_length=1
    )
    message_id: str = Field(
        ...,
        description="Message ID to retrieve",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class ListThreadsInput(BaseModel):
    """Input for listing threads in an inbox."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox ID to list threads from",
        min_length=1
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        description="Maximum number of threads to return",
        ge=1,
        le=MAX_LIMIT
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class GetThreadInput(BaseModel):
    """Input for getting a specific thread."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    inbox_id: str = Field(
        ...,
        description="Inbox ID containing the thread",
        min_length=1
    )
    thread_id: str = Field(
        ...,
        description="Thread ID to retrieve",
        min_length=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


class CreateWebhookInput(BaseModel):
    """Input for creating a webhook."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    url: str = Field(
        ...,
        description="HTTPS endpoint URL for webhook delivery",
        min_length=1
    )
    events: List[WebhookEvent] = Field(
        ...,
        description="Event types to subscribe to (e.g., ['message.received', 'message.delivered'])",
        min_length=1
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return v


class WebhookIdInput(BaseModel):
    """Input requiring a webhook ID."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    webhook_id: str = Field(
        ...,
        description="Webhook identifier",
        min_length=1
    )


class ListWebhooksInput(BaseModel):
    """Input for listing webhooks."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'"
    )


# ============================================================================
# Shared Utilities
# ============================================================================

def _get_headers() -> Dict[str, str]:
    """Get authorization headers for API requests."""
    if not API_KEY:
        raise ValueError(
            "SENDOOK_API_KEY environment variable is not set. "
            "Please set it to your Sendook API key."
        )
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an authenticated API request to Sendook.

    Args:
        endpoint: API endpoint path (e.g., 'v1/inboxes')
        method: HTTP method (GET, POST, DELETE)
        json_data: Request body for POST requests
        params: Query parameters for GET requests

    Returns:
        Parsed JSON response

    Raises:
        httpx.HTTPStatusError: For HTTP error responses
    """
    url = f"{API_BASE_URL}/{endpoint}"
    headers = _get_headers()

    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            json=json_data,
            params=params,
            timeout=30.0
        )
        response.raise_for_status()

        # Handle empty responses (204 No Content)
        if response.status_code == 204:
            return {}

        return response.json()


def _handle_api_error(e: Exception) -> str:
    """Format API errors into actionable messages.

    Args:
        e: The exception that occurred

    Returns:
        Human-readable error message with guidance
    """
    if isinstance(e, ValueError) and "SENDOOK_API_KEY" in str(e):
        return str(e)

    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code

        try:
            error_body = e.response.json()
            message = error_body.get("message", "Unknown error")
            code = error_body.get("code", "")
        except Exception:
            message = e.response.text or "Unknown error"
            code = ""

        if status == 400:
            return f"Error: Invalid request - {message}. Please check your input parameters."
        elif status == 401:
            return "Error: Authentication failed. Please verify your SENDOOK_API_KEY is valid and not expired."
        elif status == 403:
            return f"Error: Permission denied - {message}. Check your API key permissions."
        elif status == 404:
            return f"Error: Resource not found - {message}. Verify the ID exists and is accessible."
        elif status == 429:
            return "Error: Rate limit exceeded. Please wait a moment before retrying."
        elif status >= 500:
            return f"Error: Sendook server error ({status}). This is temporary; please retry."
        else:
            return f"Error: API request failed ({status}) - {message}"

    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. The Sendook API may be slow; please retry."

    elif isinstance(e, httpx.ConnectError):
        return "Error: Could not connect to Sendook API. Check your network connection."

    return f"Error: Unexpected error - {type(e).__name__}: {str(e)}"


def _format_timestamp(ts: Optional[str]) -> str:
    """Format ISO timestamp for display."""
    if not ts:
        return "N/A"
    # Return as-is since it's already ISO format
    return ts.replace("T", " ").replace("Z", " UTC")


def _format_inbox_markdown(inbox: Dict[str, Any]) -> str:
    """Format inbox details as Markdown."""
    lines = [
        f"## {inbox.get('name', 'Unnamed Inbox')}",
        f"- **ID**: `{inbox.get('id', 'N/A')}`",
        f"- **Email**: {inbox.get('email', 'N/A')}",
        f"- **Created**: {_format_timestamp(inbox.get('createdAt'))}",
        ""
    ]
    return "\n".join(lines)


def _format_message_markdown(msg: Dict[str, Any], include_body: bool = True) -> str:
    """Format message details as Markdown."""
    lines = [
        f"### {msg.get('subject', '(No Subject)')}",
        f"- **ID**: `{msg.get('id', 'N/A')}`",
        f"- **Labels**: {', '.join(msg.get('labels', [])) or 'None'}",
        f"- **Created**: {_format_timestamp(msg.get('createdAt'))}",
    ]

    if include_body:
        text = msg.get("text", "")
        if text:
            # Truncate long messages
            if len(text) > 500:
                text = text[:500] + "... (truncated)"
            lines.append(f"\n**Body:**\n```\n{text}\n```")

    lines.append("")
    return "\n".join(lines)


def _truncate_response(response: str, data_count: int) -> str:
    """Truncate response if it exceeds character limit."""
    if len(response) <= CHARACTER_LIMIT:
        return response

    truncated = response[:CHARACTER_LIMIT - 200]
    truncated += f"\n\n---\n**Response truncated** (showing partial results of {data_count} items). Use pagination or filters to see more."
    return truncated


def _text_to_html(text: str) -> str:
    """Convert plain text to basic HTML."""
    import html
    escaped = html.escape(text)
    # Convert newlines to <br> tags and wrap in paragraph
    paragraphs = escaped.split('\n\n')
    html_parts = []
    for p in paragraphs:
        p = p.replace('\n', '<br>\n')
        html_parts.append(f"<p>{p}</p>")
    return '\n'.join(html_parts)


def _html_to_text(html_content: str) -> str:
    """Strip HTML tags to get plain text."""
    import re
    # Replace <br> and </p> with newlines
    text = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
    text = re.sub(r'</p>\s*<p>', '\n\n', text, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    import html
    text = html.unescape(text)
    return text.strip()


# ============================================================================
# Inbox Tools
# ============================================================================

@mcp.tool(
    name="sendook_create_inbox",
    annotations={
        "title": "Create Sendook Inbox",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def sendook_create_inbox(params: CreateInboxInput) -> str:
    """Create a new inbox for an AI agent to send and receive emails.

    Creates a managed inbox with a unique email address. Each inbox has independent
    message storage and can have webhooks configured for real-time notifications.

    Args:
        params: CreateInboxInput containing:
            - name (Optional[str]): Display name for the inbox
            - email (Optional[str]): Custom email address; auto-generated if omitted

    Returns:
        str: JSON with the created inbox details including id, name, email, and createdAt

    Examples:
        - Create support inbox: name="Customer Support Bot"
        - Create with custom email: email="support@agents.example.com"
    """
    try:
        request_body: Dict[str, Any] = {}
        if params.name:
            request_body["name"] = params.name
        if params.email:
            request_body["email"] = params.email

        result = await _make_api_request("v1/inboxes", method="POST", json_data=request_body)

        return json.dumps({
            "success": True,
            "inbox": result,
            "message": f"Inbox created successfully. Email: {result.get('email')}"
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_list_inboxes",
    annotations={
        "title": "List Sendook Inboxes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_list_inboxes(params: ListInboxesInput) -> str:
    """List all inboxes in your Sendook organization.

    Returns all inboxes with their IDs, names, email addresses, and creation dates.
    Use this to discover available inboxes before sending messages or configuring webhooks.

    Args:
        params: ListInboxesInput containing:
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of inboxes in requested format
    """
    try:
        result = await _make_api_request("v1/inboxes")
        inboxes = result if isinstance(result, list) else []

        if not inboxes:
            return "No inboxes found. Use sendook_create_inbox to create one."

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({"count": len(inboxes), "inboxes": inboxes}, indent=2)
        else:
            lines = [f"# Sendook Inboxes ({len(inboxes)} total)", ""]
            for inbox in inboxes:
                lines.append(_format_inbox_markdown(inbox))
            response = "\n".join(lines)

        return _truncate_response(response, len(inboxes))

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_get_inbox",
    annotations={
        "title": "Get Sendook Inbox Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_get_inbox(params: InboxIdInput) -> str:
    """Get details for a specific inbox.

    Args:
        params: InboxIdInput containing:
            - inbox_id: The inbox identifier

    Returns:
        str: Inbox details including id, name, email, and createdAt
    """
    try:
        result = await _make_api_request(f"v1/inboxes/{params.inbox_id}")
        return json.dumps({"inbox": result}, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_delete_inbox",
    annotations={
        "title": "Delete Sendook Inbox",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_delete_inbox(params: InboxIdInput) -> str:
    """Delete an inbox and archive its messages.

    WARNING: This action revokes sending access and archives all historical messages.
    The inbox email address will no longer receive messages.

    Args:
        params: InboxIdInput containing:
            - inbox_id: The inbox identifier to delete

    Returns:
        str: Confirmation of deleted inbox
    """
    try:
        result = await _make_api_request(f"v1/inboxes/{params.inbox_id}", method="DELETE")
        return json.dumps({
            "success": True,
            "deleted_inbox": result,
            "message": "Inbox deleted. Historical messages have been archived."
        }, indent=2)
    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# Message Tools
# ============================================================================

@mcp.tool(
    name="sendook_send_message",
    annotations={
        "title": "Send Email via Sendook",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def sendook_send_message(params: SendMessageInput) -> str:
    """Send an email message from a Sendook inbox.

    Sends an email to specified recipients with optional CC, BCC, attachments,
    and custom labels. Supports both plain text and HTML content.

    Args:
        params: SendMessageInput containing:
            - inbox_id: Inbox to send from
            - to: List of recipient email addresses
            - subject: Email subject line
            - text: Plain text body (optional)
            - html: HTML body (optional)
            - cc: CC recipients (optional)
            - bcc: BCC recipients (optional)
            - labels: Custom labels (optional)
            - attachments: File attachments as base64 (optional)

    Returns:
        str: Confirmation with message ID and details

    Examples:
        - Simple email: to=["user@example.com"], subject="Hello", text="Hi there!"
        - With attachments: Include attachments list with base64 content
    """
    try:
        request_body: Dict[str, Any] = {
            "to": params.to,
            "subject": params.subject
        }

        # API requires both text and html - auto-generate missing one
        text_content = params.text or ""
        html_content = params.html or ""

        if text_content and not html_content:
            html_content = _text_to_html(text_content)
        elif html_content and not text_content:
            text_content = _html_to_text(html_content)
        elif not text_content and not html_content:
            return "Error: Must provide either 'text' or 'html' content for the message."

        request_body["text"] = text_content
        request_body["html"] = html_content

        if params.cc:
            request_body["cc"] = params.cc
        if params.bcc:
            request_body["bcc"] = params.bcc
        if params.labels:
            request_body["labels"] = params.labels
        if params.attachments:
            request_body["attachments"] = [
                {
                    "content": att.content,
                    "name": att.name,
                    "contentType": att.content_type
                }
                for att in params.attachments
            ]

        result = await _make_api_request(
            f"v1/inboxes/{params.inbox_id}/messages/send",
            method="POST",
            json_data=request_body
        )

        return json.dumps({
            "success": True,
            "message_id": result.get("id"),
            "subject": result.get("subject"),
            "recipients": params.to,
            "status": "Message accepted for delivery"
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_reply_to_message",
    annotations={
        "title": "Reply to Sendook Message",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def sendook_reply_to_message(params: ReplyToMessageInput) -> str:
    """Reply to an existing message in a conversation thread.

    Sends a reply that maintains the conversation thread context.
    The reply will be threaded with the original message.

    Args:
        params: ReplyToMessageInput containing:
            - inbox_id: Inbox containing the message
            - message_id: Original message to reply to
            - text: Plain text reply body (optional)
            - html: HTML reply body (optional)

    Returns:
        str: Confirmation with reply message ID
    """
    try:
        # API requires both text and html - auto-generate missing one
        text_content = params.text or ""
        html_content = params.html or ""

        if text_content and not html_content:
            html_content = _text_to_html(text_content)
        elif html_content and not text_content:
            text_content = _html_to_text(html_content)
        elif not text_content and not html_content:
            return "Error: Must provide either 'text' or 'html' content for the reply."

        request_body: Dict[str, Any] = {
            "text": text_content,
            "html": html_content
        }

        result = await _make_api_request(
            f"v1/inboxes/{params.inbox_id}/messages/{params.message_id}/reply",
            method="POST",
            json_data=request_body
        )

        return json.dumps({
            "success": True,
            "reply_message_id": result.get("id"),
            "in_reply_to": params.message_id,
            "status": "Reply accepted for delivery"
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_list_messages",
    annotations={
        "title": "List Sendook Messages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_list_messages(params: ListMessagesInput) -> str:
    """List messages in a Sendook inbox.

    Returns messages with subject, labels, and timestamps. Use the query
    parameter to filter messages by content or metadata.

    Args:
        params: ListMessagesInput containing:
            - inbox_id: Inbox to list messages from
            - query: Optional filter expression
            - limit: Maximum messages to return (default 20)
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of messages in requested format
    """
    try:
        request_params: Dict[str, Any] = {}
        if params.query:
            request_params["query"] = params.query

        result = await _make_api_request(
            f"v1/inboxes/{params.inbox_id}/messages",
            params=request_params if request_params else None
        )

        messages = result if isinstance(result, list) else []
        messages = messages[:params.limit]

        if not messages:
            return f"No messages found in inbox {params.inbox_id}."

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({
                "count": len(messages),
                "inbox_id": params.inbox_id,
                "messages": messages
            }, indent=2)
        else:
            lines = [f"# Messages in Inbox ({len(messages)} shown)", ""]
            for msg in messages:
                lines.append(_format_message_markdown(msg, include_body=False))
            response = "\n".join(lines)

        return _truncate_response(response, len(messages))

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_get_message",
    annotations={
        "title": "Get Sendook Message Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_get_message(params: GetMessageInput) -> str:
    """Get full details of a specific message.

    Returns complete message content including subject, body (text and HTML),
    labels, and timestamps.

    Args:
        params: GetMessageInput containing:
            - inbox_id: Inbox containing the message
            - message_id: Message to retrieve
            - response_format: 'markdown' or 'json'

    Returns:
        str: Full message details in requested format
    """
    try:
        result = await _make_api_request(
            f"v1/inboxes/{params.inbox_id}/messages/{params.message_id}"
        )

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({"message": result}, indent=2)
        else:
            response = _format_message_markdown(result, include_body=True)

        return _truncate_response(response, 1)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# Thread Tools
# ============================================================================

@mcp.tool(
    name="sendook_list_threads",
    annotations={
        "title": "List Sendook Conversation Threads",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_list_threads(params: ListThreadsInput) -> str:
    """List conversation threads in an inbox.

    Threads group related messages (replies and forwards) together.
    Each thread contains all messages in the conversation.

    Args:
        params: ListThreadsInput containing:
            - inbox_id: Inbox to list threads from
            - limit: Maximum threads to return (default 20)
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of threads in requested format
    """
    try:
        result = await _make_api_request(f"v1/inboxes/{params.inbox_id}/threads")

        threads = result if isinstance(result, list) else []
        threads = threads[:params.limit]

        if not threads:
            return f"No threads found in inbox {params.inbox_id}."

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({
                "count": len(threads),
                "inbox_id": params.inbox_id,
                "threads": threads
            }, indent=2)
        else:
            lines = [f"# Conversation Threads ({len(threads)} shown)", ""]
            for thread in threads:
                msg_count = len(thread.get("messages", []))
                lines.append(f"## {thread.get('subject', '(No Subject)')}")
                lines.append(f"- **Thread ID**: `{thread.get('id')}`")
                lines.append(f"- **Messages**: {msg_count}")
                lines.append("")
            response = "\n".join(lines)

        return _truncate_response(response, len(threads))

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_get_thread",
    annotations={
        "title": "Get Sendook Thread Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_get_thread(params: GetThreadInput) -> str:
    """Get a full conversation thread with all messages.

    Returns the complete thread including all messages in chronological order.
    Useful for understanding the full context of a conversation.

    Args:
        params: GetThreadInput containing:
            - inbox_id: Inbox containing the thread
            - thread_id: Thread to retrieve
            - response_format: 'markdown' or 'json'

    Returns:
        str: Thread with all messages in requested format
    """
    try:
        result = await _make_api_request(
            f"v1/inboxes/{params.inbox_id}/threads/{params.thread_id}"
        )

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({"thread": result}, indent=2)
        else:
            messages = result.get("messages", [])
            lines = [
                f"# Thread: {result.get('subject', '(No Subject)')}",
                f"**Thread ID**: `{result.get('id')}`",
                f"**Messages**: {len(messages)}",
                "",
                "---",
                ""
            ]
            for msg in messages:
                lines.append(_format_message_markdown(msg, include_body=True))
            response = "\n".join(lines)

        return _truncate_response(response, len(result.get("messages", [])))

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# Webhook Tools
# ============================================================================

@mcp.tool(
    name="sendook_create_webhook",
    annotations={
        "title": "Create Sendook Webhook",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True
    }
)
async def sendook_create_webhook(params: CreateWebhookInput) -> str:
    """Create a webhook to receive real-time event notifications.

    Webhooks notify your endpoint when events occur (message received, delivered, etc.).
    The endpoint must be HTTPS and respond within 15 seconds with a 2xx status.

    Available events:
    - inbox.created, inbox.deleted, inbox.updated
    - message.sent, message.received, message.delivered
    - message.bounced, message.complained, message.rejected

    Args:
        params: CreateWebhookInput containing:
            - url: HTTPS endpoint for webhook delivery
            - events: List of event types to subscribe to

    Returns:
        str: Created webhook details including id and subscribed events
    """
    try:
        request_body = {
            "url": params.url,
            "events": [e.value for e in params.events]
        }

        result = await _make_api_request("v1/webhooks", method="POST", json_data=request_body)

        return json.dumps({
            "success": True,
            "webhook": result,
            "message": f"Webhook created. Subscribed to: {', '.join(e.value for e in params.events)}"
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_list_webhooks",
    annotations={
        "title": "List Sendook Webhooks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_list_webhooks(params: ListWebhooksInput) -> str:
    """List all configured webhooks.

    Returns all webhook subscriptions with their URLs, events, and status.

    Args:
        params: ListWebhooksInput containing:
            - response_format: 'markdown' or 'json'

    Returns:
        str: List of webhooks in requested format
    """
    try:
        result = await _make_api_request("v1/webhooks")
        webhooks = result if isinstance(result, list) else []

        if not webhooks:
            return "No webhooks configured. Use sendook_create_webhook to create one."

        if params.response_format == ResponseFormat.JSON:
            response = json.dumps({"count": len(webhooks), "webhooks": webhooks}, indent=2)
        else:
            lines = [f"# Sendook Webhooks ({len(webhooks)} total)", ""]
            for wh in webhooks:
                events = wh.get("events", [])
                lines.append(f"## Webhook `{wh.get('id')}`")
                lines.append(f"- **URL**: {wh.get('url')}")
                lines.append(f"- **Events**: {', '.join(events)}")
                lines.append(f"- **Created**: {_format_timestamp(wh.get('createdAt'))}")
                lines.append("")
            response = "\n".join(lines)

        return _truncate_response(response, len(webhooks))

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_get_webhook",
    annotations={
        "title": "Get Sendook Webhook Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_get_webhook(params: WebhookIdInput) -> str:
    """Get details of a specific webhook.

    Args:
        params: WebhookIdInput containing:
            - webhook_id: Webhook identifier

    Returns:
        str: Webhook details including URL, events, and timestamps
    """
    try:
        result = await _make_api_request(f"v1/webhooks/{params.webhook_id}")
        return json.dumps({"webhook": result}, indent=2)
    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_test_webhook",
    annotations={
        "title": "Test Sendook Webhook",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_test_webhook(params: WebhookIdInput) -> str:
    """Send a test event to a webhook endpoint.

    Verifies that your endpoint is correctly configured and responding.
    A test payload will be sent to the webhook URL.

    Args:
        params: WebhookIdInput containing:
            - webhook_id: Webhook to test

    Returns:
        str: Test result indicating success or failure
    """
    try:
        result = await _make_api_request(
            f"v1/webhooks/{params.webhook_id}/test",
            method="POST"
        )

        success = result.get("success", False)
        return json.dumps({
            "test_result": "passed" if success else "failed",
            "webhook_id": params.webhook_id,
            "message": "Test event delivered successfully" if success else "Test event delivery failed"
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_delete_webhook",
    annotations={
        "title": "Delete Sendook Webhook",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_delete_webhook(params: WebhookIdInput) -> str:
    """Delete a webhook subscription.

    Removes the webhook and stops all event deliveries to its endpoint.

    Args:
        params: WebhookIdInput containing:
            - webhook_id: Webhook to delete

    Returns:
        str: Confirmation of deleted webhook
    """
    try:
        result = await _make_api_request(
            f"v1/webhooks/{params.webhook_id}",
            method="DELETE"
        )

        return json.dumps({
            "success": True,
            "deleted_webhook": result,
            "message": "Webhook deleted. Event deliveries have been stopped."
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="sendook_list_webhook_attempts",
    annotations={
        "title": "List Webhook Delivery Attempts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def sendook_list_webhook_attempts(params: WebhookIdInput) -> str:
    """List recent delivery attempts for a webhook.

    Shows the history of webhook deliveries including successes and failures.
    Useful for debugging webhook endpoint issues.

    Args:
        params: WebhookIdInput containing:
            - webhook_id: Webhook to check attempts for

    Returns:
        str: List of delivery attempts with status and details
    """
    try:
        result = await _make_api_request(f"v1/webhooks/{params.webhook_id}/attempts")
        attempts = result if isinstance(result, list) else []

        if not attempts:
            return f"No delivery attempts found for webhook {params.webhook_id}."

        return json.dumps({
            "webhook_id": params.webhook_id,
            "attempt_count": len(attempts),
            "attempts": attempts
        }, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# Server Entry Point
# ============================================================================

def main():
    """Run the Sendook MCP server."""
    # Validate API key on startup
    if not API_KEY:
        print(
            "Warning: SENDOOK_API_KEY environment variable is not set. "
            "Set it before using the tools.",
            file=sys.stderr
        )

    mcp.run()


if __name__ == "__main__":
    main()
