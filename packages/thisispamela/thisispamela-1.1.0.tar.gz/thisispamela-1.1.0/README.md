# thisispamela SDK for Python

Official SDK for the Pamela Enterprise Voice API.

## Installation

```bash
pip install thisispamela
```

## Usage

### Basic Example

```python
from pamela import PamelaClient

client = PamelaClient(
    api_key="pk_live_your_api_key_here",
    base_url="https://api.thisispamela.com",  # Optional
)

# Create a call
call = client.create_call(
    to="+1234567890",
    task="Order a large pizza for delivery",
    locale="en-US",
    max_duration_seconds=299,
    voice="female",
    agent_name="Pamela",
    caller_name="John from Acme",
)

print(f"Call created: {call['id']}")

# Get call status
status = client.get_call(call["id"])
print(f"Call status: {status['status']}")
```

### Webhook Verification

```python
from flask import Flask, request
from pamela import verify_webhook_signature

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

@app.route("/webhooks/pamela", methods=["POST"])
def handle_webhook():
    signature = request.headers.get("X-Pamela-Signature")
    payload = request.json

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return {"error": "Invalid signature"}, 401

    # Handle webhook event
    print(f"Webhook event: {payload['event']}")
    print(f"Call ID: {payload['call_id']}")

    return {"status": "ok"}, 200
```

### Tool Webhook Handler

```python
from flask import Flask, request
from pamela import verify_webhook_signature

app = Flask(__name__)
WEBHOOK_SECRET = "your_webhook_secret"

@app.route("/webhooks/pamela/tools", methods=["POST"])
def handle_tool_webhook():
    signature = request.headers.get("X-Pamela-Signature")
    payload = request.json

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return {"error": "Invalid signature"}, 401

    tool_name = payload["tool_name"]
    arguments = payload["arguments"]
    call_id = payload["call_id"]
    correlation_id = payload["correlation_id"]

    # Execute tool based on tool_name
    if tool_name == "check_order_status":
        order_id = arguments.get("order_id")
        result = check_order_status(order_id)
        return {"result": result}

    return {"error": "Unknown tool"}, 400
```

## Getting API Keys

### Obtaining Your API Key

API keys are created and managed through the Pamela Partner Portal or via the Partner API:

1. **Sign up for an Enterprise subscription** (see Subscription Requirements below)
2. **Create an API key** via one of these methods:
   - Partner Portal: Log in to your account and navigate to the Enterprise panel
   - Partner API: `POST /api/b2b/v1/partner/api-keys`
     ```bash
     curl -X POST https://api.thisispamela.com/api/b2b/v1/partner/api-keys \
       -H "Authorization: Bearer YOUR_B2C_USER_TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"project_id": "optional-project-id", "key_prefix": "pk_live_"}'
     ```
3. **Save your API key immediately** - the full key is only returned once during creation
4. **Use the key prefix** (`pk_live_`) to identify keys in your account

### Managing API Keys

- **List API keys**: `GET /api/b2b/v1/partner/api-keys`
- **Revoke API key**: `POST /api/b2b/v1/partner/api-keys/{key_id}/revoke`
- **Associate with projects**: Optionally link API keys to specific projects for better organization

### API Key Format

- **Live keys**: Start with `pk_live_` (all API usage)
- **Security**: Keys are hashed in the database. Store them securely and never commit them to version control.

## Subscription Requirements

### Enterprise Subscription Required

**All API access requires an active Enterprise subscription.** API calls will return `403 Forbidden` if:
- No Enterprise subscription is active
- Subscription status is `past_due` and grace period has expired
- Subscription status is `canceled`

### Grace Period

Enterprise subscriptions have a **1-week grace period** when payment fails:
- During grace period: API access is allowed, but usage is still charged
- After grace period expires: API access is blocked until payment is updated

### Subscription Status Endpoints

Check subscription status using the Enterprise Partner API:
- `GET /api/b2b/v1/partner/subscription` - Get subscription status
- `POST /api/b2b/v1/partner/subscription/checkout` - Create checkout session
- `POST /api/b2b/v1/partner/subscription/portal` - Access Customer Portal

## Error Handling

The SDK provides structured exceptions for all API errors:

```python
from pamela import (
    PamelaClient,
    PamelaError,
    AuthenticationError,
    SubscriptionError,
    RateLimitError,
    ValidationError,
    CallError,
)

client = PamelaClient(api_key="pk_live_your_key")

try:
    call = client.create_call(to="+1234567890", task="Test call")
except AuthenticationError as e:
    # 401: Invalid or missing API key
    print(f"Auth failed: {e.message}")
    print(f"Error code: {e.error_code}")
except SubscriptionError as e:
    # 403: Subscription inactive or expired
    if e.error_code == 7008:
        print("Grace period expired - update payment method")
    else:
        print(f"Subscription issue: {e.message}")
except RateLimitError as e:
    # 429: Rate limit exceeded
    retry_after = e.details.get("retry_after", 30)
    print(f"Rate limited, retry after {retry_after}s")
except ValidationError as e:
    # 400/422: Invalid request parameters
    print(f"Invalid request: {e.message}")
    print(f"Details: {e.details}")
except CallError as e:
    # Call-specific errors
    print(f"Call error: {e.message}")
except PamelaError as e:
    # All other API errors
    print(f"API error {e.error_code}: {e.message}")
```

### Exception Hierarchy

All exceptions inherit from `PamelaError`:

```
PamelaError (base)
├── AuthenticationError  # 401 errors
├── SubscriptionError    # 403 errors (subscription issues)
├── RateLimitError       # 429 errors
├── ValidationError      # 400/422 errors
└── CallError            # Call-specific errors
```

### Exception Attributes

All exceptions have:
- `message`: Human-readable error message
- `error_code`: Numeric error code (e.g., 7008 for subscription expired)
- `details`: Dict with additional context
- `status_code`: HTTP status code

## Error Codes Reference

### Authentication Errors (401)

| Code | Description |
|------|-------------|
| 1001 | API key required |
| 1002 | Invalid API key |
| 1003 | API key expired |

### Subscription Errors (403)

| Code | Description |
|------|-------------|
| 1005 | Enterprise subscription required |
| 7008 | Subscription expired (grace period ended) |

### Validation Errors (400)

| Code | Description |
|------|-------------|
| 2001 | Validation error |
| 2002 | Invalid phone number format |

### Enterprise Errors (7xxx)

| Code | Description |
|------|-------------|
| 7001 | Partner not found |
| 7002 | Project not found |
| 7003 | Call not found |
| 7004 | No phone number for country |
| 7005 | Unsupported country |

### Rate Limiting (429)

| Code | Description |
|------|-------------|
| 6001 | Rate limit exceeded |
| 6002 | Quota exceeded |

## Usage Limits & Billing

### Enterprise API Usage

- **Unlimited API calls** (no call count limits)
- **All API usage billed at $0.10/minute** (10 cents per minute)
- **Minimum billing: 1 minute per call** (even if call duration < 60 seconds)
- **Billing calculation**: `billed_minutes = max(ceil(duration_seconds / 60), 1)`
- **Only calls that connect** (have `started_at`) are billed

### Usage Tracking

- Usage is tracked in `b2b_usage` collection with `type: "api_usage"` (collection name stays `b2b_usage`)
- Usage is synced to Stripe hourly (at :00 minutes)
- Stripe meter name: `stripe_minutes`
- Failed syncs are retried with exponential backoff (1s, 2s, 4s, 8s, 16s), max 5 retries

### Billing Period

- Billing is based on calendar months (UTC midnight on 1st of each month)
- Calls are billed in the month where `started_at` occurred
- Usage sync status: `pending`, `synced`, or `failed`

## API Methods

### Calls

- `create_call(to, task, ...)` - Create a new call
- `get_call(call_id)` - Get call status and details
- `list_calls(status?, limit?, offset?, ...)` - List calls with optional filters
- `cancel_call(call_id)` - Cancel an in-progress call
- `hangup_call(call_id)` - Force hangup an in-progress call

### Tools

- `register_tool(name, description, input_schema, ...)` - Register a tool
- `list_tools()` - List all tools
- `delete_tool(tool_id)` - Delete a tool

### Usage

- `usage.get(period=None)` - Get usage statistics

**Example:**
```python
# Get current month usage
usage = client.usage.get()

# Get usage for specific period
jan_usage = client.usage.get("2024-01")

print(f"Usage: {usage['call_count']} calls, {usage.get('api_minutes', 0)} minutes")
print(f"Quota: {usage.get('quota', {}).get('partner_limit', 'Unlimited')}")
```

**Response:**
```python
{
    "partner_id": "partner_123",
    "project_id": "project_456",  # Optional
    "period": "2024-01",
    "call_count": 150,
    "quota": {
        "partner_limit": None,  # None = unlimited for Enterprise
        "project_limit": None
    }
}
```

**Note:** Enterprise subscriptions have no quota limits - all usage is billed per-minute.

## API Reference

See the [Pamela Enterprise API Documentation](https://docs.thisispamela.com/enterprise) for full API reference.

