"""
CB Dominus SDK - Ultra-flat async SDK for CareBridge Services

Ultra-Flat API:
    from dominus import dominus

    # Secrets (root level shortcuts)
    value = await dominus.get("DB_URL")
    await dominus.upsert("KEY", "value")

    # Secrets namespace
    value = await dominus.secrets.get("DB_URL")
    await dominus.secrets.upsert("KEY", "value")

    # Database (namespace-based)
    tables = await dominus.db.tables()
    rows = await dominus.db.query("users", filters={"status": "active"})
    await dominus.db.insert("users", {"name": "John"})

    # Auth (namespace-based)
    users = await dominus.auth.list_users()
    await dominus.auth.create_user(username="john", email="j@ex.com", password="secret")

    # DDL (namespace-based)
    await dominus.ddl.create_table("public", "users", [{"name": "id", "type": "UUID"}])

    # Files (namespace-based)
    result = await dominus.files.upload(data=file_bytes, filename="report.pdf", category="reports")

    # Redis caching
    await dominus.redis.set("key", "value", ttl=3600)
    value = await dominus.redis.get("key")

    # Logging
    await dominus.logs.info("Operation complete", {"user_id": user_id})

    # Email
    await dominus.courier.send("welcome", to="user@example.com", from_email="hello@app.com", model={})

    # Secure table access with audit logging
    rows = await dominus.db_secure.query("patients", context=SecureAccessContext(
        reason="Reviewing chart",
        actor=user_id
    ))

    # Admin operations
    await dominus.admin.reseed_admin_category()

    # Portal authentication
    session = await dominus.portal.login("user@example.com", "password", "tenant-id")

    # Open DSN and raw SQL
    dsn = await dominus.open.dsn()
    result = await dominus.open.execute("SELECT * FROM users WHERE id = $1", {"1": user_id})

    # Health
    status = await dominus.health.check()
    await dominus.health.ping()
    await dominus.health.warmup()

Backward Compatible APIs:
    # String-based API
    result = await dominus("secrets.get", key="DB_URL")

    # Flat API (root level shortcuts for common operations)
    await dominus.list_tables()
    await dominus.query_table("users")
    await dominus.insert_row("users", {"name": "John"})

Crypto Helpers:
    from dominus import hash_password, hash_psk, generate_token
    hashed = hash_password("secret")
"""
from .start import dominus, Dominus
from .helpers.core import DominusResponse

# Export crypto helpers
from .helpers.crypto import (
    hash_password,
    verify_password,
    hash_psk,
    verify_psk,
    generate_psk_local,
    hash_token,
    generate_token,
)

# Export namespace classes for type hints
from .namespaces.db import DbNamespace
from .namespaces.auth import AuthNamespace
from .namespaces.ddl import DdlNamespace
from .namespaces.files import FilesNamespace
from .namespaces.portal import PortalNamespace
from .namespaces.admin import AdminNamespace
from .namespaces.secure import SecureNamespace, SecureAccessContext
from .namespaces.secrets import SecretsNamespace
from .namespaces.redis import RedisNamespace
from .namespaces.logs import LogsNamespace
from .namespaces.courier import CourierNamespace
from .namespaces.health import HealthNamespace
from .namespaces.open import OpenNamespace

# Export Oracle namespace for speech-to-text
from .namespaces.oracle import (
    OracleNamespace,
    OracleSession,
    OracleSessionOptions,
    VADState,
)

# Export AI namespace for agent-runtime operations
from .namespaces.ai import (
    AiNamespace,
    RagSubNamespace,
    ArtifactsSubNamespace,
    ResultsSubNamespace,
    WorkflowSubNamespace,
)

# Export cache and resilience utilities
from .helpers.cache import (
    dominus_cache,
    CircuitBreaker,
    DominusCache,
    orchestrator_circuit_breaker,
    exponential_backoff_with_jitter,
)

# Export JWT verification utilities
from .helpers.core import (
    verify_jwt_locally,
    is_jwt_valid,
)

# Export error classes
from .errors import (
    DominusError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    ConflictError,
    ServiceError,
    SecureTableError,
    ConnectionError as DominusConnectionError,
    TimeoutError as DominusTimeoutError,
)

__version__ = "2.8.0"
__all__ = [
    # Main SDK instance
    "dominus",
    "Dominus",
    "DominusResponse",
    # Crypto helpers
    "hash_password",
    "verify_password",
    "hash_psk",
    "verify_psk",
    "generate_psk_local",
    "hash_token",
    "generate_token",
    # Namespace classes (for type hints)
    "DbNamespace",
    "AuthNamespace",
    "DdlNamespace",
    "FilesNamespace",
    "PortalNamespace",
    "AdminNamespace",
    "SecureNamespace",
    "SecureAccessContext",
    "SecretsNamespace",
    "RedisNamespace",
    "LogsNamespace",
    "CourierNamespace",
    "HealthNamespace",
    "OpenNamespace",
    # Oracle namespace for speech-to-text
    "OracleNamespace",
    "OracleSession",
    "OracleSessionOptions",
    "VADState",
    # AI namespace for agent-runtime operations
    "AiNamespace",
    "RagSubNamespace",
    "ArtifactsSubNamespace",
    "ResultsSubNamespace",
    "WorkflowSubNamespace",
    # Cache and resilience utilities
    "dominus_cache",
    "CircuitBreaker",
    "DominusCache",
    "orchestrator_circuit_breaker",
    "exponential_backoff_with_jitter",
    # JWT verification utilities
    "verify_jwt_locally",
    "is_jwt_valid",
    # Error classes
    "DominusError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "ConflictError",
    "ServiceError",
    "SecureTableError",
    "DominusConnectionError",
    "DominusTimeoutError",
]
