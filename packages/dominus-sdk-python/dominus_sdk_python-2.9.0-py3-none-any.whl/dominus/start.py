"""
CB Dominus SDK

Setup:
    export DOMINUS_TOKEN="your_token"

Service URLs are hardcoded in the SDK (dominus/config/endpoints.py).
No need to set URL environment variables.

Note: In Infisical, the secret is stored as PROVISION_DOMINUS_TOKEN.
When fetching via dominus.secrets.get("PROVISION_DOMINUS_TOKEN"),
set the result as DOMINUS_TOKEN environment variable (drop PROVISION_ prefix).

Usage (Ultra-Flat API):
    from dominus import dominus

    # Secrets (root level)
    value = await dominus.get("DB_URL")
    await dominus.upsert("KEY", "value")

    # Auth (root level)
    await dominus.add_user(username="john", password="secret", role_id="...")
    await dominus.add_scope(slug="read", display_name="Read", tenant_category_id=1)
    await dominus.add_role(name="admin", scope_slugs=["read", "write"])
    result = await dominus.verify_user_password(username="john", password="secret")

    # SQL data - app schema (root level)
    tables = await dominus.list_tables()
    rows = await dominus.query_table("users")
    await dominus.insert_row("users", {"name": "John"})

    # SQL data - secure schema (secure namespace)
    rows = await dominus.secure.query_table("patients")
    await dominus.secure.insert_row("patients", {"mrn": "12345"})

    # Schema DDL - app schema (root level)
    await dominus.add_table("users", [{"name": "id", "type": "UUID"}])
    await dominus.add_column("users", "email", "VARCHAR(255)")

    # Schema DDL - secure schema (secure namespace)
    await dominus.secure.add_table("patients", [...])

    # Open DSN
    dsn = await dominus.open.dsn()

    # Health
    status = await dominus.health.check()

Usage (String-based API - Backward Compatible):
    result = await dominus("secrets.get", key="DB_URL")
"""
import os
import httpx
import base64
import json
from typing import Optional, Any, Dict, List

# Module-level state
_VALIDATED = False
_TOKEN: Optional[str] = None
_BASE_URL: Optional[str] = None
_GATEWAY_URL: Optional[str] = None
_VALIDATION_ERROR: Optional[str] = None


# === MODULE-LEVEL INITIALIZATION ===
from .helpers.auth import _resolve_token
from .config.endpoints import BASE_URL, GATEWAY_URL

_TOKEN = _resolve_token()
_BASE_URL = BASE_URL
_GATEWAY_URL = GATEWAY_URL

# Initialize cache encryption
from .helpers.cache import dominus_cache
if _TOKEN:
    dominus_cache.set_encryption_key(_TOKEN)

# Validate token presence
if not _TOKEN:
    _VALIDATION_ERROR = (
        "DOMINUS_TOKEN not found.\n\n"
        "Set the environment variable:\n"
        "  export DOMINUS_TOKEN=your_token\n\n"
        "Or in production, set it via your deployment platform.\n"
    )


class SecureNamespace:
    """
    Secure schema operations namespace.

    Provides SQL data operations and schema DDL for the secure schema.
    Used for PHI/sensitive data with audit logging.
    """

    def __init__(self, _execute_command):
        self._execute = _execute_command

    # ========================================
    # SECURE SQL DATA OPERATIONS
    # ========================================

    async def list_tables(self) -> List[Dict[str, Any]]:
        """List tables in the secure schema."""
        return await self._execute("sql.secure.list_tables", schema="secure")

    async def query_table(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Query table data from the secure schema."""
        return await self._execute(
            "sql.secure.query_table",
            table_name=table_name,
            schema="secure",
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

    async def insert_row(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a row into a table in the secure schema."""
        return await self._execute(
            "sql.secure.insert_row",
            table_name=table_name,
            data=data,
            schema="secure"
        )

    async def update_rows(
        self,
        table_name: str,
        data: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update rows in a table in the secure schema."""
        return await self._execute(
            "sql.secure.update_rows",
            table_name=table_name,
            data=data,
            filters=filters,
            schema="secure"
        )

    async def delete_rows(
        self,
        table_name: str,
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delete rows from app schema (secure schema doesn't allow DELETE).

        Note: This uses app schema even from secure namespace because
        PHI data in secure schema uses soft deletes only.
        """
        return await self._execute(
            "sql.secure.delete_rows",
            table_name=table_name,
            filters=filters,
            schema="app"
        )

    async def list_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """List columns in a table in the secure schema."""
        return await self._execute(
            "sql.secure.list_columns",
            table_name=table_name,
            schema="secure"
        )

    async def get_table_size(self, table_name: str) -> Dict[str, Any]:
        """Get table size information from the secure schema."""
        return await self._execute(
            "sql.secure.get_table_size",
            table_name=table_name,
            schema="secure"
        )

    # ========================================
    # SECURE SCHEMA DDL OPERATIONS
    # ========================================

    async def add_table(
        self,
        table_name: str,
        columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create a new table in the secure schema."""
        return await self._execute(
            "schema.secure_add_table",
            table_name=table_name,
            columns=columns
        )

    async def delete_table(self, table_name: str) -> Dict[str, Any]:
        """Drop a table from the secure schema."""
        return await self._execute(
            "schema.secure_delete_table",
            table_name=table_name
        )

    async def ddl_list_tables(self) -> List[Dict[str, Any]]:
        """List all tables in the secure schema (DDL view)."""
        return await self._execute("schema.secure_list_tables")

    async def ddl_list_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """List columns in a table (DDL view)."""
        return await self._execute(
            "schema.secure_list_columns",
            table_name=table_name
        )

    async def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        constraints: Optional[List[str]] = None,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a column to a table in the secure schema."""
        return await self._execute(
            "schema.secure_add_column",
            table_name=table_name,
            column_name=column_name,
            column_type=column_type,
            constraints=constraints,
            default=default
        )

    async def delete_column(
        self,
        table_name: str,
        column_name: str
    ) -> Dict[str, Any]:
        """Drop a column from a table in the secure schema."""
        return await self._execute(
            "schema.secure_delete_column",
            table_name=table_name,
            column_name=column_name
        )




class Dominus:
    """
    Main SDK entry point with ultra-flat API.

    Most operations are directly on the root object:
    - dominus.get(), dominus.upsert() - secrets
    - dominus.add_user(), dominus.add_scope() - auth
    - dominus.query_table(), dominus.insert_row() - SQL (app schema)
    - dominus.add_table(), dominus.add_column() - DDL (app schema)

    Namespaces for specific use cases:
    - dominus.secure.* - secure schema operations
    - dominus.open.dsn() - open user DSN
    - dominus.health.check() - health checks
    """

    def __init__(self):
        """Initialize Dominus with flat API and minimal namespaces."""
        # Create internal execute function that handles validation
        async def _execute_command(command: str, **kwargs) -> Any:
            """Internal command executor with validation"""
            global _VALIDATED

            if _VALIDATION_ERROR:
                raise RuntimeError(_VALIDATION_ERROR)

            # Validate on first call
            if not _VALIDATED:
                from .helpers.core import verify_token_format, health_check_all

                # Basic token format check
                verify_token_format(_TOKEN)

                # Health check to warm up the server
                result = await health_check_all(_BASE_URL)
                if result["status"] != "healthy" and result["status"] != "ok":
                    raise RuntimeError(f"Services unhealthy: {result['message']}")

                _VALIDATED = True

            # Execute command
            from .helpers.core import execute_command
            return await execute_command(command, _TOKEN, _BASE_URL, **kwargs)

        self._execute = _execute_command

        # Initialize legacy flat API namespaces (backward compatibility)
        self.secure = SecureNamespace(_execute_command)

        # Initialize portal namespace (needs client reference for _request)
        from .namespaces.portal import PortalNamespace
        self.portal = PortalNamespace(self)

        # Initialize FastAPI namespace (decorators for route auth)
        from .namespaces.fastapi import FastAPINamespace
        self.fastapi = FastAPINamespace(self)

        # Initialize all namespaces (matching Node.js SDK pattern)
        from .namespaces.db import DbNamespace
        from .namespaces.auth import AuthNamespace
        from .namespaces.ddl import DdlNamespace
        from .namespaces.files import FilesNamespace
        from .namespaces.admin import AdminNamespace
        from .namespaces.secure import SecureNamespace as SecureNS
        from .namespaces.secrets import SecretsNamespace
        from .namespaces.redis import RedisNamespace
        from .namespaces.logs import LogsNamespace
        from .namespaces.courier import CourierNamespace
        from .namespaces.health import HealthNamespace
        from .namespaces.open import OpenNamespace

        # Core namespaces
        self.db = DbNamespace(self)
        self.auth = AuthNamespace(self)
        self.ddl = DdlNamespace(self)
        self.files = FilesNamespace(self)
        self.admin = AdminNamespace(self)

        # Additional namespaces (Node.js SDK parity)
        self.secrets = SecretsNamespace(self)
        self.redis = RedisNamespace(self)
        self.logs = LogsNamespace(self)
        self.courier = CourierNamespace(self)
        self.health = HealthNamespace(self)
        self.open = OpenNamespace(self)

        # Secure namespace with proper audit context support
        self.db_secure = SecureNS(self)

        # Oracle namespace (Speech-to-Text streaming)
        from .namespaces.oracle import OracleNamespace
        self.oracle = OracleNamespace(self)

        # Alias for Node.js SDK parity (stt = oracle)
        self.stt = self.oracle

        # AI namespace (agent-runtime unified API)
        from .namespaces.ai import AiNamespace
        self.ai = AiNamespace(self)

        # Workflow namespace (workflow-manager service)
        from .namespaces.workflow import WorkflowNamespace
        self.workflow = WorkflowNamespace(self)

        # Cache for JWT public key
        self._public_key_cache = None

    # ========================================
    # INTERNAL REQUEST METHOD (for user JWT)
    # ========================================

    async def _request(
        self,
        endpoint: str,
        method: str = "POST",
        body: Optional[Dict[str, Any]] = None,
        user_token: Optional[str] = None,
        use_gateway: bool = False
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the orchestrator or gateway.

        If user_token is provided, uses that JWT directly (for user-authenticated requests).
        Otherwise, uses the service token flow (PSK -> JWT).

        Args:
            endpoint: API endpoint path (e.g., "/api/portal/auth/me")
            method: HTTP method (GET, POST, PUT, DELETE)
            body: Request body (will be base64-encoded)
            user_token: Optional user JWT for user-authenticated requests
            use_gateway: If True, route through gateway (/api/* -> /svc/*)

        Returns:
            Response data dict
        """
        global _VALIDATED

        # Base64 helpers
        def _b64_encode(d: dict) -> str:
            return base64.b64encode(json.dumps(d).encode()).decode()

        def _b64_decode(s: str) -> dict:
            return json.loads(base64.b64decode(s.encode('utf-8')).decode('utf-8'))

        # Transform endpoint for gateway routing
        if use_gateway and endpoint.startswith("/api/"):
            endpoint = "/svc/" + endpoint[5:]  # /api/llm/complete -> /svc/llm/complete

        # Determine which JWT to use
        if user_token:
            # Use the provided user JWT directly (no validation needed - orchestrator validates it)
            jwt = user_token
        else:
            # Use service token flow - validate first if needed
            if _VALIDATION_ERROR:
                raise RuntimeError(_VALIDATION_ERROR)

            if not _VALIDATED:
                from .helpers.core import verify_token_format, health_check_all

                # Basic token format check
                verify_token_format(_TOKEN)

                # Health check to warm up the server
                result = await health_check_all(_BASE_URL)
                if result["status"] != "healthy" and result["status"] != "ok":
                    raise RuntimeError(f"Services unhealthy: {result['message']}")

                _VALIDATED = True

            # Get service JWT
            from .helpers.core import _ensure_valid_jwt
            jwt = await _ensure_valid_jwt(_TOKEN, _BASE_URL)

        # Prepare request
        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "text/plain"
        }

        # Prepare body
        body_b64 = _b64_encode(body or {})

        # Select base URL
        base_url = _GATEWAY_URL if use_gateway else _BASE_URL

        # Make request
        async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=30.0) as client:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "DELETE":
                response = await client.delete(endpoint)
            elif method == "PUT":
                response = await client.put(endpoint, content=body_b64)
            else:
                response = await client.post(endpoint, content=body_b64)

        response.raise_for_status()

        # Decode base64 response
        result = _b64_decode(response.text)

        # Check for success
        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            raise RuntimeError(f"Request error: {error_msg}")

        return result.get("data", {})

    async def _stream_request(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        on_chunk: Optional[Any] = None,
        timeout: float = 300.0,
        use_gateway: bool = False
    ):
        """
        Make an SSE streaming request to the orchestrator or gateway.

        Args:
            endpoint: API endpoint path (e.g., "/api/agent/stream")
            body: Request body (will be base64-encoded)
            on_chunk: Optional callback for each chunk
            timeout: Request timeout in seconds (default: 300s for long operations)
            use_gateway: If True, route through gateway (/api/* -> /svc/*)

        Yields:
            Parsed JSON chunks from SSE stream
        """
        global _VALIDATED

        # Base64 helpers
        def _b64_encode(d: dict) -> str:
            return base64.b64encode(json.dumps(d).encode()).decode()

        # Transform endpoint for gateway routing
        if use_gateway and endpoint.startswith("/api/"):
            endpoint = "/svc/" + endpoint[5:]

        # Validate and get JWT
        if _VALIDATION_ERROR:
            raise RuntimeError(_VALIDATION_ERROR)

        if not _VALIDATED:
            from .helpers.core import verify_token_format, health_check_all
            verify_token_format(_TOKEN)
            result = await health_check_all(_BASE_URL)
            if result["status"] != "healthy" and result["status"] != "ok":
                raise RuntimeError(f"Services unhealthy: {result['message']}")
            _VALIDATED = True

        from .helpers.core import _ensure_valid_jwt
        jwt = await _ensure_valid_jwt(_TOKEN, _BASE_URL)

        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "text/plain",
            "Accept": "text/event-stream"
        }

        body_b64 = _b64_encode(body or {})

        from .helpers.sse import stream_sse

        base_url = _GATEWAY_URL if use_gateway else _BASE_URL
        async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
            async with client.stream("POST", endpoint, content=body_b64, headers=headers) as response:
                response.raise_for_status()
                async for chunk in stream_sse(response, on_chunk):
                    yield chunk

    async def _binary_upload(
        self,
        endpoint: str,
        file_bytes: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        additional_fields: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
        use_gateway: bool = False
    ) -> Dict[str, Any]:
        """
        Upload binary file via multipart/form-data (no base64 encoding).

        Used for audio uploads (STT) and other binary file uploads.

        Args:
            endpoint: API endpoint path (e.g., "/api/agent/stt")
            file_bytes: Raw binary file content
            filename: Filename for the upload
            content_type: MIME type (default: application/octet-stream)
            additional_fields: Optional additional form fields
            timeout: Request timeout in seconds
            use_gateway: If True, route through gateway (/api/* -> /svc/*)

        Returns:
            Response data dict
        """
        global _VALIDATED

        def _b64_decode(s: str) -> dict:
            return json.loads(base64.b64decode(s.encode('utf-8')).decode('utf-8'))

        # Transform endpoint for gateway routing
        if use_gateway and endpoint.startswith("/api/"):
            endpoint = "/svc/" + endpoint[5:]

        if _VALIDATION_ERROR:
            raise RuntimeError(_VALIDATION_ERROR)

        if not _VALIDATED:
            from .helpers.core import verify_token_format, health_check_all
            verify_token_format(_TOKEN)
            result = await health_check_all(_BASE_URL)
            if result["status"] != "healthy" and result["status"] != "ok":
                raise RuntimeError(f"Services unhealthy: {result['message']}")
            _VALIDATED = True

        from .helpers.core import _ensure_valid_jwt
        jwt = await _ensure_valid_jwt(_TOKEN, _BASE_URL)

        headers = {
            "Authorization": f"Bearer {jwt}"
        }

        # Build multipart form data
        files = {"file": (filename, file_bytes, content_type)}
        data = additional_fields or {}

        base_url = _GATEWAY_URL if use_gateway else _BASE_URL
        async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout) as client:
            response = await client.post(endpoint, files=files, data=data)

        response.raise_for_status()

        # Response may be base64-encoded JSON or raw JSON
        try:
            result = _b64_decode(response.text)
        except Exception:
            result = response.json()

        if isinstance(result, dict) and not result.get("success", True):
            error_msg = result.get("error", "Unknown error")
            raise RuntimeError(f"Upload error: {error_msg}")

        return result.get("data", result) if isinstance(result, dict) else result

    async def _binary_download(
        self,
        endpoint: str,
        body: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
        use_gateway: bool = False
    ) -> bytes:
        """
        Download binary content (no base64 encoding in response).

        Used for TTS audio responses and other binary downloads.

        Args:
            endpoint: API endpoint path (e.g., "/api/agent/tts")
            body: Request body (will be base64-encoded for auth)
            timeout: Request timeout in seconds
            use_gateway: If True, route through gateway (/api/* -> /svc/*)

        Returns:
            Raw binary bytes
        """
        global _VALIDATED

        def _b64_encode(d: dict) -> str:
            return base64.b64encode(json.dumps(d).encode()).decode()

        # Transform endpoint for gateway routing
        if use_gateway and endpoint.startswith("/api/"):
            endpoint = "/svc/" + endpoint[5:]

        if _VALIDATION_ERROR:
            raise RuntimeError(_VALIDATION_ERROR)

        if not _VALIDATED:
            from .helpers.core import verify_token_format, health_check_all
            verify_token_format(_TOKEN)
            result = await health_check_all(_BASE_URL)
            if result["status"] != "healthy" and result["status"] != "ok":
                raise RuntimeError(f"Services unhealthy: {result['message']}")
            _VALIDATED = True

        from .helpers.core import _ensure_valid_jwt
        jwt = await _ensure_valid_jwt(_TOKEN, _BASE_URL)

        headers = {
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "text/plain",
            "Accept": "audio/*"
        }

        body_b64 = _b64_encode(body or {})

        base_url = _GATEWAY_URL if use_gateway else _BASE_URL
        async with httpx.AsyncClient(base_url=base_url, headers=headers, timeout=timeout) as client:
            response = await client.post(endpoint, content=body_b64)

        response.raise_for_status()

        # Return raw binary content
        return response.content

    # ========================================
    # SECRETS (root level)
    # ========================================

    async def get(self, key: str) -> Any:
        """
        Get a secret value.

        Args:
            key: Secret key name

        Returns:
            Secret value
        """
        return await self._execute("secrets.get", key=key)

    async def upsert(self, key: str, value: str) -> Dict[str, Any]:
        """
        Create or update a secret.

        Args:
            key: Secret key name
            value: Secret value

        Returns:
            Operation result
        """
        return await self._execute("secrets.upsert", key=key, value=value)

    # ========================================
    # SQL DATA - APP SCHEMA (root level)
    # ========================================

    async def list_tables(self, schema: str = "app") -> List[Dict[str, Any]]:
        """List tables in the app schema (or specified schema)."""
        return await self._execute("sql.app.list_tables", schema=schema)

    async def query_table(
        self,
        table_name: str,
        schema: str = "app",
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Query table data from the app schema (default)."""
        return await self._execute(
            "sql.app.query_table",
            table_name=table_name,
            schema=schema,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )

    async def insert_row(
        self,
        table_name: str,
        data: Dict[str, Any],
        schema: str = "app"
    ) -> Dict[str, Any]:
        """Insert a row into a table in the app schema (default)."""
        return await self._execute(
            "sql.app.insert_row",
            table_name=table_name,
            data=data,
            schema=schema
        )

    async def update_rows(
        self,
        table_name: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        schema: str = "app"
    ) -> Dict[str, Any]:
        """Update rows in a table in the app schema (default)."""
        return await self._execute(
            "sql.app.update_rows",
            table_name=table_name,
            data=data,
            filters=filters,
            schema=schema
        )

    async def delete_rows(
        self,
        table_name: str,
        filters: Dict[str, Any],
        schema: str = "app"
    ) -> Dict[str, Any]:
        """Delete rows from a table in the app schema (default)."""
        return await self._execute(
            "sql.app.delete_rows",
            table_name=table_name,
            filters=filters,
            schema=schema
        )

    async def list_columns(
        self,
        table_name: str,
        schema: str = "app"
    ) -> List[Dict[str, Any]]:
        """List columns in a table."""
        return await self._execute(
            "sql.app.list_columns",
            table_name=table_name,
            schema=schema
        )

    async def get_table_size(
        self,
        table_name: str,
        schema: str = "app"
    ) -> Dict[str, Any]:
        """Get table size information."""
        return await self._execute(
            "sql.app.get_table_size",
            table_name=table_name,
            schema=schema
        )

    # ========================================
    # SCHEMA DDL - APP SCHEMA (root level)
    # ========================================

    async def add_table(
        self,
        table_name: str,
        columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new table in the app schema.

        Args:
            table_name: Name of table to create
            columns: List of column definitions
                [{"name": "id", "type": "UUID", "constraints": ["PRIMARY KEY"]}]
        """
        return await self._execute(
            "schema.add_table",
            table_name=table_name,
            columns=columns
        )

    async def delete_table(self, table_name: str) -> Dict[str, Any]:
        """Drop a table from the app schema."""
        return await self._execute(
            "schema.delete_table",
            table_name=table_name
        )

    async def ddl_list_tables(self) -> List[Dict[str, Any]]:
        """List all tables in the app schema (DDL view)."""
        return await self._execute("schema.list_tables")

    async def ddl_list_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """List columns in a table (DDL view)."""
        return await self._execute(
            "schema.list_columns",
            table_name=table_name
        )

    async def add_column(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        constraints: Optional[List[str]] = None,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a column to a table in the app schema."""
        return await self._execute(
            "schema.add_column",
            table_name=table_name,
            column_name=column_name,
            column_type=column_type,
            constraints=constraints,
            default=default
        )

    async def delete_column(
        self,
        table_name: str,
        column_name: str
    ) -> Dict[str, Any]:
        """Drop a column from a table in the app schema."""
        return await self._execute(
            "schema.delete_column",
            table_name=table_name,
            column_name=column_name
        )

    # ========================================
    # AUTH - SCOPES (root level)
    # ========================================

    async def add_scope(
        self,
        slug: str,
        display_name: str,
        tenant_category_id: int,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new scope."""
        return await self._execute(
            "auth.add_scope",
            slug=slug,
            display_name=display_name,
            tenant_category_id=tenant_category_id,
            description=description
        )

    async def delete_scope(self, scope_id: str) -> Dict[str, Any]:
        """Delete a scope by ID."""
        return await self._execute("auth.delete_scope", scope_id=scope_id)

    async def list_scopes(
        self,
        tenant_category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """List all scopes, optionally filtered by category."""
        return await self._execute(
            "auth.list_scopes",
            tenant_category_id=tenant_category_id
        )

    async def get_scope(
        self,
        scope_id: Optional[str] = None,
        slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a scope by ID or slug."""
        return await self._execute(
            "auth.get_scope",
            scope_id=scope_id,
            slug=slug
        )

    # ========================================
    # AUTH - ROLES (root level)
    # ========================================

    async def add_role(
        self,
        name: str,
        scope_slugs: Optional[List[str]] = None,
        description: Optional[str] = None,
        role_type: str = "user"
    ) -> Dict[str, Any]:
        """Add a new role."""
        return await self._execute(
            "auth.add_role",
            name=name,
            scope_slugs=scope_slugs or [],
            description=description,
            role_type=role_type
        )

    async def delete_role(self, role_id: str) -> Dict[str, Any]:
        """Delete a role by ID."""
        return await self._execute("auth.delete_role", role_id=role_id)

    async def list_roles(self) -> List[Dict[str, Any]]:
        """List all roles for the tenant."""
        return await self._execute("auth.list_roles")

    async def get_role(
        self,
        role_id: Optional[str] = None,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a role by ID or name."""
        return await self._execute(
            "auth.get_role",
            role_id=role_id,
            name=name
        )

    async def update_role_scopes(
        self,
        role_id: str,
        scope_slugs: List[str]
    ) -> Dict[str, Any]:
        """Update the scopes assigned to a role."""
        return await self._execute(
            "auth.update_role_scopes",
            role_id=role_id,
            scope_slugs=scope_slugs
        )

    # ========================================
    # AUTH - USERS (root level)
    # ========================================

    async def add_user(
        self,
        username: str,
        password: str,
        role_id: str,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new user.

        Password is hashed client-side before sending to Architect.
        """
        from .helpers.crypto import hash_password
        password_hash = hash_password(password)
        return await self._execute(
            "auth.add_user",
            username=username,
            password_hash=password_hash,
            role_id=role_id,
            email=email
        )

    async def delete_user(self, user_id: str) -> Dict[str, Any]:
        """Delete a user by ID."""
        return await self._execute("auth.delete_user", user_id=user_id)

    async def list_users(self) -> List[Dict[str, Any]]:
        """List all users for the tenant."""
        return await self._execute("auth.list_users")

    async def get_user(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get a user by ID or username."""
        return await self._execute(
            "auth.get_user",
            user_id=user_id,
            username=username
        )

    async def update_user_status(
        self,
        user_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Update a user's status (active, inactive, suspended)."""
        return await self._execute(
            "auth.update_user_status",
            user_id=user_id,
            status=status
        )

    async def update_user_role(
        self,
        user_id: str,
        role_id: str
    ) -> Dict[str, Any]:
        """Update a user's assigned role."""
        return await self._execute(
            "auth.update_user_role",
            user_id=user_id,
            role_id=role_id
        )

    async def verify_user_password(
        self,
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Verify a user's password.

        Raw password is sent to Architect which does bcrypt comparison.
        """
        return await self._execute(
            "auth.verify_user_password",
            username=username,
            password=password
        )

    # ========================================
    # AUTH - CLIENTS / PSK (root level)
    # ========================================

    async def add_client(
        self,
        label: str,
        role_id: str
    ) -> Dict[str, Any]:
        """
        Add a new service client with PSK.

        Returns {"client": {...}, "psk": "raw-psk-one-time-visible"}
        """
        from .helpers.crypto import hash_psk, generate_psk_local
        raw_psk = generate_psk_local()
        psk_hash = hash_psk(raw_psk)
        client_result = await self._execute(
            "auth.add_client",
            label=label,
            role_id=role_id,
            psk_hash=psk_hash
        )
        return {
            "client": client_result,
            "psk": raw_psk  # One-time visible
        }

    async def delete_client(self, client_id: str) -> Dict[str, Any]:
        """Delete a client by ID."""
        return await self._execute("auth.delete_client", client_id=client_id)

    async def list_clients(self) -> List[Dict[str, Any]]:
        """List all clients for the tenant."""
        return await self._execute("auth.list_clients")

    async def get_client(self, client_id: str) -> Dict[str, Any]:
        """Get a client by ID."""
        return await self._execute("auth.get_client", client_id=client_id)

    async def regenerate_client_psk(self, client_id: str) -> Dict[str, Any]:
        """
        Regenerate a client's PSK.

        Returns {"client": {...}, "psk": "new-raw-psk-one-time-visible"}
        """
        from .helpers.crypto import hash_psk, generate_psk_local
        raw_psk = generate_psk_local()
        psk_hash = hash_psk(raw_psk)
        client_result = await self._execute(
            "auth.regenerate_client_psk",
            client_id=client_id,
            psk_hash=psk_hash
        )
        return {
            "client": client_result,
            "psk": raw_psk
        }

    async def verify_client_psk(
        self,
        client_id: str,
        psk: str
    ) -> Dict[str, Any]:
        """
        Verify a client's PSK.

        Raw PSK is sent to Architect which does bcrypt comparison.
        """
        return await self._execute(
            "auth.verify_client_psk",
            client_id=client_id,
            psk=psk
        )

    # ========================================
    # AUTH - REFRESH TOKENS (root level)
    # ========================================

    async def add_refresh_token(
        self,
        user_id: Optional[str] = None,
        client_psk_id: Optional[str] = None,
        expires_in_seconds: int = 86400 * 30  # 30 days
    ) -> Dict[str, Any]:
        """
        Create a new refresh token.

        Either user_id or client_psk_id must be provided.
        Returns {"token_id": "...", "token": "raw-token-one-time-visible"}
        """
        from .helpers.crypto import hash_token, generate_token
        raw_token = generate_token()
        token_hash = hash_token(raw_token)

        result = await self._execute(
            "auth.add_refresh_token",
            user_id=user_id,
            client_psk_id=client_psk_id,
            token_hash=token_hash,
            expires_in_seconds=expires_in_seconds
        )
        return {
            "token_id": result.get("id"),
            "token": raw_token,
            "expires_at": result.get("expires_at")
        }

    async def delete_refresh_token(self, token_id: str) -> Dict[str, Any]:
        """Delete/revoke a refresh token."""
        return await self._execute(
            "auth.delete_refresh_token",
            token_id=token_id
        )

    async def list_refresh_tokens(
        self,
        user_id: Optional[str] = None,
        client_psk_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List refresh tokens, optionally filtered by user or client."""
        return await self._execute(
            "auth.list_refresh_tokens",
            user_id=user_id,
            client_psk_id=client_psk_id
        )

    # ========================================
    # AUTH - JWT OPERATIONS (root level)
    # ========================================

    async def mint_jwt(
        self,
        user_id: str,
        scope: Optional[List[str]] = None,
        expires_in: int = 900,
        system: str = "user"
    ) -> Dict[str, Any]:
        """
        Mint a JWT for a subsidiary user.

        Returns {"access_token": "...", "token_type": "Bearer", "expires_in": ...}
        """
        return await self._execute(
            "auth.mint",
            user_id=user_id,
            scope=scope,
            system=system
        )

    async def get_public_key(self) -> Dict[str, Any]:
        """Get Sovereign's JWKS for JWT validation (cached)."""
        if self._public_key_cache:
            return self._public_key_cache

        result = await self._execute("auth.jwks")
        self._public_key_cache = result
        return self._public_key_cache

    async def validate_jwt(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT and return its claims.

        Decodes the JWT payload and checks expiration.
        Matches JS SDK behavior (decode + expiration check).

        Raises ValueError if token is invalid or expired.
        """
        import base64
        import json
        import time

        # Ensure JWKS is cached for potential future use
        await self.get_public_key()

        # Decode JWT without cryptographic verification (matches JS SDK)
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Invalid JWT format")

        try:
            # Decode payload (base64url)
            payload_b64 = parts[1]
            # Add padding if needed
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            # Replace URL-safe characters
            payload_b64 = payload_b64.replace('-', '+').replace('_', '/')
            payload_bytes = base64.b64decode(payload_b64)
            claims = json.loads(payload_bytes.decode('utf-8'))

            # Check expiration
            exp = claims.get("exp")
            if exp and exp < int(time.time()):
                raise ValueError("Token has expired")

            return claims
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Invalid token: {e}")

    # ========================================
    # STRING-BASED API (backward compatible)
    # ========================================

    async def __call__(self, command: str, **kwargs) -> Any:
        """
        String-based command execution (backward compatible).

        Examples:
            await dominus("health.check")
            await dominus("secrets.get", key="DATABASE_URL")
            await dominus("sql.app.list_tables", schema="app")
        """
        global _VALIDATED

        if _VALIDATION_ERROR:
            raise RuntimeError(_VALIDATION_ERROR)

        # Validate on first call
        if not _VALIDATED:
            from .helpers.core import verify_token_format, health_check_all

            # Basic token format check
            verify_token_format(_TOKEN)

            # Health check to warm up the server
            result = await health_check_all(_BASE_URL)
            if result["status"] != "healthy" and result["status"] != "ok":
                raise RuntimeError(f"Services unhealthy: {result['message']}")

            _VALIDATED = True

        # Execute command
        from .helpers.core import execute_command
        return await execute_command(command, _TOKEN, _BASE_URL, **kwargs)


# Create singleton instance
dominus = Dominus()
