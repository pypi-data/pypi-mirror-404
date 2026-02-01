# Sendook MCP Server

MCP (Model Context Protocol) server for [Sendook](https://www.sendook.com) - an AI email communication platform that enables AI agents to send and receive emails programmatically.

## Features

- **Inbox Management**: Create, list, and delete managed email inboxes
- **Email Sending**: Send emails with HTML/text content, attachments, and CC/BCC
- **Message Handling**: List, retrieve, and reply to messages
- **Conversation Threads**: View and manage email conversation threads
- **Webhooks**: Configure real-time notifications for email events

## Installation

```bash
# Using uv (recommended)
cd sendook_mcp
uv sync

# Or using pip
pip install -e .
```

## Configuration

Set your Sendook API key as an environment variable:

```bash
export SENDOOK_API_KEY="your-api-key-here"
```

Optional: Set a custom API URL (defaults to production):

```bash
export SENDOOK_API_URL="https://api.sendook.com"
```

## Usage with Claude Desktop

Add to your Claude Desktop configuration (`~/.config/Claude/claude_desktop_config.json` on macOS/Linux or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "sendook": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/sendook_mcp", "python", "sendook_mcp.py"],
      "env": {
        "SENDOOK_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Or if installed globally:

```json
{
  "mcpServers": {
    "sendook": {
      "command": "sendook-mcp",
      "env": {
        "SENDOOK_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Available Tools

### Inbox Management

| Tool | Description |
|------|-------------|
| `sendook_create_inbox` | Create a new inbox for an AI agent |
| `sendook_list_inboxes` | List all inboxes in your organization |
| `sendook_get_inbox` | Get details for a specific inbox |
| `sendook_delete_inbox` | Delete an inbox (archives messages) |

### Message Operations

| Tool | Description |
|------|-------------|
| `sendook_send_message` | Send an email with optional attachments |
| `sendook_reply_to_message` | Reply to an existing message |
| `sendook_list_messages` | List messages in an inbox |
| `sendook_get_message` | Get full details of a message |

### Thread Operations

| Tool | Description |
|------|-------------|
| `sendook_list_threads` | List conversation threads in an inbox |
| `sendook_get_thread` | Get a thread with all its messages |

### Webhook Management

| Tool | Description |
|------|-------------|
| `sendook_create_webhook` | Create a webhook subscription |
| `sendook_list_webhooks` | List all configured webhooks |
| `sendook_get_webhook` | Get details of a webhook |
| `sendook_test_webhook` | Send a test event to a webhook |
| `sendook_delete_webhook` | Delete a webhook subscription |
| `sendook_list_webhook_attempts` | View webhook delivery history |

## Examples

### Send an Email

```
Use sendook_send_message with:
- inbox_id: "ibox_01J3ZKZ0BRQ9SSJK1GRSCX4N4Z"
- to: ["customer@example.com"]
- subject: "Your Order Confirmation"
- text: "Thank you for your order!"
```

### Create a Support Inbox

```
Use sendook_create_inbox with:
- name: "Customer Support Bot"
- email: "support@yourdomain.com"
```

### Set Up Webhook for Incoming Emails

```
Use sendook_create_webhook with:
- url: "https://your-app.com/webhooks/sendook"
- events: ["message.received", "message.delivered"]
```

## Response Formats

Most read operations support two response formats:

- **markdown** (default): Human-readable formatted output
- **json**: Machine-readable structured data

Set `response_format: "json"` for programmatic processing.

## Error Handling

The server provides actionable error messages:

- **401**: Authentication failed - check your API key
- **403**: Permission denied - verify API key permissions
- **404**: Resource not found - check the ID
- **429**: Rate limit exceeded - wait and retry

## Development

```bash
# Install dev dependencies
uv sync --extra dev

# Run linting
uv run ruff check .

# Run tests
uv run pytest
```

## License

MIT
