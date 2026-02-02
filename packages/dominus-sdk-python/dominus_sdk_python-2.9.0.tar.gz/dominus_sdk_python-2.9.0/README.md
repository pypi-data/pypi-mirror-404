# CB Dominus SDK for Python

**Async Python SDK for the Dominus Orchestrator Platform**

A unified, async-first Python SDK providing seamless access to all Dominus backend services including secrets management, database operations, caching, file storage, authentication, schema management, and structured logging.

## Features

- **Namespace-based API** - Intuitive access via `dominus.db`, `dominus.redis`, `dominus.files`, etc.
- **Async/Await** - Built for modern async Python applications (asyncio)
- **Automatic JWT Management** - Token minting, caching, and refresh handled transparently
- **Resilience Built-in** - Circuit breaker, exponential backoff, and retry logic
- **Cold Start Handling** - Special retry logic for orchestrator cold starts
- **Typed Errors** - 9 specific error classes for different failure modes
- **Secure by Default** - Client-side password hashing, encrypted cache, audit trail support

## Quick Start

```python
from dominus import dominus
import os

# Set your token (or use DOMINUS_TOKEN environment variable)
os.environ["DOMINUS_TOKEN"] = "your-psk-token"

async def main():
    # Secrets
    db_url = await dominus.get("DATABASE_URL")

    # Database queries
    users = await dominus.db.query("users", filters={"status": "active"})

    # Redis caching
    await dominus.redis.set("session:123", {"user": "john"}, ttl=3600)

    # File storage
    result = await dominus.files.upload(data, "report.pdf", category="reports")

    # Structured logging
    await dominus.logs.info("User logged in", {"user_id": "123"})
```

## Installation

```bash
# Clone or add as submodule
git clone https://github.com/carebridgesystems/cb-dominus-sdk.git

# Install dependencies
pip install httpx bcrypt cryptography
```

Or install via pip (when published):

```bash
pip install dominus-sdk-python
```

## Requirements

- Python 3.9+
- `httpx` - Async HTTP client
- `bcrypt` - Password hashing
- `cryptography` - Cache encryption

## Namespaces

| Namespace | Service | Purpose |
|-----------|---------|---------|
| `dominus.secrets` | Warden | Secrets management |
| `dominus.db` | Scribe | Database CRUD operations |
| `dominus.secure` | Scribe | Secure table access with audit logging |
| `dominus.redis` | Whisperer | Redis caching & distributed locks |
| `dominus.files` | Archivist | Object storage (Backblaze B2) |
| `dominus.auth` | Guardian | Users, roles, scopes, tenants, pages, navigation |
| `dominus.ddl` | Smith | Schema DDL & migrations |
| `dominus.logs` | Herald | Structured logging (BetterStack) |
| `dominus.portal` | Portal | User auth, sessions, profiles, navigation |
| `dominus.courier` | Courier | Email delivery (Postmark) |
| `dominus.open` | Scribe | Direct database access |
| `dominus.health` | Health | Service health checks |

## Usage Examples

### Secrets Management

```python
# Root-level shortcuts
value = await dominus.get("API_KEY")
await dominus.upsert("API_KEY", "new-value", comment="Updated API key")

# Full namespace
secrets = await dominus.secrets.list(prefix="DB_")
await dominus.secrets.delete("OLD_KEY")
```

### Database Operations

```python
# List tables
tables = await dominus.db.tables()
tenant_tables = await dominus.db.tables(schema="tenant_acme")

# Query with filters and pagination
users = await dominus.db.query(
    "users",
    filters={"status": "active", "role": ["admin", "manager"]},
    sort_by="created_at",
    sort_order="desc",
    limit=50,
    offset=0
)

# Insert
user = await dominus.db.insert("users", {
    "email": "john@example.com",
    "name": "John Doe"
})

# Update
await dominus.db.update("users", {"status": "inactive"}, filters={"id": user_id})

# Delete
await dominus.db.delete("users", filters={"id": user_id})

# Bulk insert
await dominus.db.bulk_insert("events", [
    {"type": "login", "user_id": "123"},
    {"type": "login", "user_id": "456"}
])

# Secure table access (requires audit reason)
patients = await dominus.db.query(
    "patients",
    schema="tenant_acme",
    reason="Reviewing records for appointment #123",
    actor="dr.smith"
)
```

### Redis Caching

```python
# Key-value operations (TTL: min 60s, max 24h)
await dominus.redis.set("user:123", {"name": "John"}, ttl=3600)
value = await dominus.redis.get("user:123")
await dominus.redis.delete("user:123")

# Distributed locks
if await dominus.redis.setnx("lock:job", "worker-1", ttl=60):
    try:
        # Do exclusive work
        pass
    finally:
        await dominus.redis.delete("lock:job")

# Counters
await dominus.redis.incr("page:views", delta=1)

# Hash operations
await dominus.redis.hset("user:123", "email", "john@example.com", ttl=3600)
email = await dominus.redis.hget("user:123", "email")
```

### File Storage

```python
# Upload file
with open("report.pdf", "rb") as f:
    result = await dominus.files.upload(
        data=f.read(),
        filename="report.pdf",
        category="reports"
    )

# Get download URL
download = await dominus.files.download(file_id=result["id"])
url = download["download_url"]

# List files
files = await dominus.files.list(category="reports", prefix="2025/")

# Delete file
await dominus.files.delete(file_id=result["id"])
```

### Structured Logging

```python
# Simple logging (auto-captures file and function)
await dominus.logs.info("User logged in", {"user_id": "123"})
await dominus.logs.error("Payment failed", {"order_id": "456"})

# All log levels
await dominus.logs.debug("Debug message", {"data": "..."})
await dominus.logs.notice("Important notice", {})
await dominus.logs.warn("Warning message", {})
await dominus.logs.critical("Critical error", {})

# With category
await dominus.logs.info("Cache hit", {"key": "user:123"}, category="cache")

# With exception context
try:
    risky_operation()
except Exception as e:
    await dominus.logs.error("Operation failed", {}, exception=e)

# Batch logging
await dominus.logs.batch([
    {"level": "info", "message": "Step 1 complete", "data": {}},
    {"level": "info", "message": "Step 2 complete", "data": {}}
])

# Query logs
errors = await dominus.logs.query(level="error", limit=100)
```

### Authentication & Authorization (Guardian)

```python
# User management
users = await dominus.auth.list_users()
user = await dominus.auth.get_user(user_id="uuid")

new_user = await dominus.auth.add_user(
    username="john",
    password="secure-password",
    email="john@example.com"
)

await dominus.auth.update_user("uuid", status="active")
await dominus.auth.delete_user("uuid")

# Role management
roles = await dominus.auth.list_roles()
role = await dominus.auth.add_role(
    name="Editor",
    scope_slugs=["read", "write", "publish"]
)

# Scope management
scopes = await dominus.auth.list_scopes()

# Tenant management
tenants = await dominus.auth.list_tenants()
categories = await dominus.auth.list_tenant_categories()

# JWT operations
jwt = await dominus.auth.mint_jwt(user_id=user["id"], expires_in=900)
claims = await dominus.auth.validate_jwt(token)
```

### Schema Management (DDL)

```python
# Create table
await dominus.ddl.add_table("orders", [
    {"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY"]},
    {"name": "user_id", "type": "UUID", "constraints": ["NOT NULL"]},
    {"name": "total", "type": "DECIMAL(10,2)"},
    {"name": "created_at", "type": "TIMESTAMPTZ", "default": "NOW()"}
])

# Add column
await dominus.ddl.add_column("orders", "status", "VARCHAR(50)", default="'pending'")

# Provision tenant schema from category template
await dominus.ddl.provision_tenant("customer_acme", category_slug="healthcare")
```

### User Authentication (Portal)

```python
# User login (tenant_id is optional)
session = await dominus.portal.login(
    username="john@example.com",
    password="secret123",
    tenant_id="tenant-uuid"  # optional
)

# Client login with PSK (for service-to-service)
client_session = await dominus.portal.login_client(psk="psk-token")

# Get current user
me = await dominus.portal.me()

# Get navigation (access-filtered for current user)
nav = await dominus.portal.get_navigation()

# Check page access
has_access = await dominus.portal.check_page_access("/dashboard/admin/users")

# Switch tenant
await dominus.portal.switch_tenant("other-tenant-uuid")

# Profile & preferences
profile = await dominus.portal.get_profile()
await dominus.portal.update_profile(display_name="John Doe")

prefs = await dominus.portal.get_preferences()
await dominus.portal.update_preferences(theme="dark", timezone="America/New_York")

# Password management
await dominus.portal.change_password("old-password", "new-password")
await dominus.portal.request_password_reset("john@example.com")
await dominus.portal.confirm_password_reset("reset-token", "new-password")

# Session management
sessions = await dominus.portal.list_sessions()
await dominus.portal.revoke_session("session-id")
await dominus.portal.revoke_all_sessions()

# Registration & email verification
await dominus.portal.register("newuser", "new@example.com", "password", "tenant-id")
await dominus.portal.verify_email("verification-token")
await dominus.portal.resend_verification("new@example.com")

# Logout
await dominus.portal.logout()
```

### Email Delivery (Courier)

```python
# Send email via Postmark template
result = await dominus.courier.send(
    template_alias="welcome",
    to="user@example.com",
    from_email="noreply@myapp.com",
    model={"name": "John", "product_name": "My App"}
)

# Convenience methods
await dominus.courier.send_welcome(
    to="user@example.com",
    from_email="noreply@myapp.com",
    name="John",
    action_url="https://myapp.com/start",
    product_name="My App"
)

await dominus.courier.send_password_reset(
    to="user@example.com",
    from_email="noreply@myapp.com",
    name="John",
    reset_url="https://myapp.com/reset?token=abc",
    product_name="My App"
)

await dominus.courier.send_email_verification(
    to="user@example.com",
    from_email="noreply@myapp.com",
    name="John",
    verify_url="https://myapp.com/verify?token=xyz",
    product_name="My App"
)

await dominus.courier.send_invitation(
    to="invited@example.com",
    from_email="noreply@myapp.com",
    name="Invited User",
    invite_url="https://myapp.com/invite?token=abc",
    inviter_name="John",
    product_name="My App"
)
```

### Health Checks

```python
# Basic health check
status = await dominus.health.check()
```

## Error Handling

```python
from dominus import (
    dominus,
    DominusError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    ServiceError,
    SecureTableError,
    DominusConnectionError,  # Renamed to avoid shadowing built-in
    DominusTimeoutError,     # Renamed to avoid shadowing built-in
)

try:
    user = await dominus.auth.get_user(user_id="invalid")
except NotFoundError as e:
    print(f"User not found: {e.message}")
except SecureTableError as e:
    print("Secure table requires 'reason' and 'actor' parameters")
except AuthenticationError as e:
    print("Invalid or expired token")
except AuthorizationError as e:
    print("Insufficient permissions")
except ValidationError as e:
    print(f"Invalid request: {e.message}")
except TimeoutError as e:
    print("Request timed out")
except DominusError as e:
    print(f"Error {e.status_code}: {e.message}")
    if e.details:
        print(f"Details: {e.details}")
```

### Error Types

| Error | Status | Description |
|-------|--------|-------------|
| `DominusError` | - | Base class for all SDK errors |
| `AuthenticationError` | 401 | Invalid or missing token |
| `AuthorizationError` | 403 | Insufficient permissions |
| `NotFoundError` | 404 | Resource not found |
| `ValidationError` | 400 | Invalid request data |
| `ConflictError` | 409 | Duplicate or version conflict |
| `ServiceError` | 5xx | Backend service error |
| `SecureTableError` | 403 | Missing reason for secure table |
| `DominusConnectionError` | - | Network connection failed |
| `DominusTimeoutError` | 504 | Request timed out |

## Configuration

### Environment Variables

```bash
# Required: PSK token for authentication
export DOMINUS_TOKEN="your-psk-token"

# Optional: Project configuration
export CB_PROJECT_SLUG="my-project"
export CB_ENVIRONMENT="production"
```

### Token Resolution

The SDK resolves the authentication token in this order:
1. `DOMINUS_TOKEN` environment variable
2. Hardcoded fallback in `dominus/start.py` (development only)

## Architecture

```
┌─────────────────┐
│  Your App       │
│  (async Python) │
└────────┬────────┘
         │ await dominus.db.query(...)
         ▼
┌─────────────────┐
│  Dominus SDK    │  ← JWT caching, circuit breaker, retries
│  (this package) │
└────────┬────────┘
         │ HTTPS (base64-encoded JSON)
         ▼
┌─────────────────────────────────┐
│  Dominus Orchestrator           │
│  (Cloud Run FastAPI backend)    │
│                                 │
│  ┌─────────┬─────────┬────────┐ │
│  │ Warden  │Guardian │Archivist│ │
│  │ Scribe  │ Smith   │Whisperer│ │
│  │ Herald  │ Portal  │ Courier │ │
│  └─────────┴─────────┴────────┘ │
└─────────────────────────────────┘
```

## FastAPI Integration

```python
from fastapi import FastAPI, HTTPException
from dominus import dominus, NotFoundError

app = FastAPI()

@app.get("/users")
async def list_users():
    try:
        users = await dominus.db.query("users", filters={"status": "active"}, limit=50)
        return users
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    try:
        user = await dominus.auth.get_user(user_id)
        return user
    except NotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
```

## Pagination Pattern

```python
async def get_all_users(page_size: int = 100):
    offset = 0
    all_users = []
    while True:
        result = await dominus.db.query("users", limit=page_size, offset=offset)
        rows = result.get("rows", [])
        all_users.extend(rows)
        if len(rows) < page_size:
            break
        offset += page_size
    return all_users
```

## Documentation

- [Installation & Quick Start](dominus/QUICKSTART.md)
- [LLM Usage Guide](dominus/LLM-GUIDE.md)

## Version

**v2.4.0** - Full namespace parity with Node.js SDK

### Changelog

- **v2.4.0** - Full parity with Node.js SDK: all namespaces properly initialized, error classes exported, cache utilities exposed
- **v2.3.0** - Add comprehensive auth namespace with 100+ methods
- **v2.2.0** - Add DDL schema builder and migration methods
- **v2.1.6** - Fix navigation routes and add page scope methods
- **v2.1.5** - Add PSK-only client login
- **v2.1.4** - Make `tenant_id` optional in login methods
- **v2.1.2** - Remove `/verify` endpoint call, keep health warmup
- **v2.1.1** - Fix hardcoded orchestrator base URL
- **v2.1.0** - Fix SDK routes and remove hardcoded token support
- **v2.0.0** - Complete namespace-based API rewrite

## License

Proprietary - CareBridge Systems
