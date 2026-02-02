"""
Secure Namespace - Audit-logged data access for sensitive tables.

Provides CRUD operations with mandatory reason/actor parameters for compliance.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class SecureAccessContext:
    """Access context for secure table operations."""

    def __init__(self, reason: str, actor: str):
        self.reason = reason
        self.actor = actor


class SecureNamespace:
    """
    Secure data access namespace.

    All operations require a SecureAccessContext with reason and actor
    for HIPAA/compliance audit logging.

    Usage:
        context = SecureAccessContext(
            reason="Viewing patient chart for appointment #123",
            actor="user:abc123"
        )

        # List secure tables
        tables = await dominus.secure.tables(schema="tenant_acme")

        # Query with audit context
        patients = await dominus.secure.query(
            "patients",
            context,
            filters={"active": True}
        )

        # Insert with audit context
        await dominus.secure.insert(
            "patients",
            {"mrn": "12345", "name": "John Doe"},
            context
        )
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def tables(self, schema: str = "public") -> List[Dict[str, Any]]:
        """
        List tables in a schema (secure view).

        Args:
            schema: Schema name (default: "public")

        Returns:
            List of table metadata
        """
        result = await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/tables",
            method="GET"
        )
        return result.get("tables", result) if isinstance(result, dict) else result

    async def columns(self, table: str, schema: str = "public") -> List[Dict[str, Any]]:
        """
        List columns in a table (secure view).

        Args:
            table: Table name
            schema: Schema name (default: "public")

        Returns:
            List of column metadata with is_primary_key
        """
        result = await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/columns",
            method="GET"
        )
        return result.get("columns", result) if isinstance(result, dict) else result

    async def query(
        self,
        table: str,
        context: SecureAccessContext,
        schema: str = "public",
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "ASC",
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query table data with mandatory audit context.

        Args:
            table: Table name
            context: SecureAccessContext with reason and actor
            schema: Schema name (default: "public")
            filters: Column:value filter dictionary
            sort_by: Column to sort by
            sort_order: "ASC" or "DESC"
            limit: Maximum rows to return (default: 100)
            offset: Rows to skip (default: 0)

        Returns:
            Dict with "rows" and "total" keys
        """
        body = {
            "filters": filters,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset,
            "reason": context.reason,
            "actor": context.actor
        }

        result = await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/query",
            body=body
        )

        # Normalize response
        return {
            "rows": result.get("items", result.get("rows", [])),
            "total": result.get("total", 0)
        }

    async def insert(
        self,
        table: str,
        data: Dict[str, Any],
        context: SecureAccessContext,
        schema: str = "public"
    ) -> Dict[str, Any]:
        """
        Insert a row with mandatory audit context.

        Args:
            table: Table name
            data: Column:value dictionary
            context: SecureAccessContext with reason and actor
            schema: Schema name (default: "public")

        Returns:
            Inserted row data
        """
        body = {
            "data": data,
            "reason": context.reason,
            "actor": context.actor
        }

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/insert",
            body=body
        )

    async def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
        context: SecureAccessContext,
        schema: str = "public"
    ) -> Dict[str, Any]:
        """
        Update rows with mandatory audit context.

        Args:
            table: Table name
            data: Column:value dictionary of updates
            filters: Column:value dictionary for WHERE clause
            context: SecureAccessContext with reason and actor
            schema: Schema name (default: "public")

        Returns:
            Dict with "affected_rows" count
        """
        body = {
            "data": data,
            "filters": filters,
            "reason": context.reason,
            "actor": context.actor
        }

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/update",
            body=body
        )

    async def delete(
        self,
        table: str,
        filters: Dict[str, Any],
        context: SecureAccessContext,
        schema: str = "public"
    ) -> Dict[str, Any]:
        """
        Delete rows with mandatory audit context.

        Args:
            table: Table name
            filters: Column:value dictionary for WHERE clause
            context: SecureAccessContext with reason and actor
            schema: Schema name (default: "public")

        Returns:
            Dict with "affected_rows" count
        """
        body = {
            "filters": filters,
            "reason": context.reason,
            "actor": context.actor
        }

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/delete",
            body=body
        )

    async def bulk_insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        context: SecureAccessContext,
        schema: str = "public"
    ) -> Dict[str, Any]:
        """
        Insert multiple rows with mandatory audit context.

        Args:
            table: Table name
            rows: List of column:value dictionaries
            context: SecureAccessContext with reason and actor
            schema: Schema name (default: "public")

        Returns:
            Dict with "inserted_count" and optionally "rows"
        """
        body = {
            "rows": rows,
            "reason": context.reason,
            "actor": context.actor
        }

        return await self._client._request(
            endpoint=f"/api/scribe/data/{schema}/{table}/bulk-insert",
            body=body
        )
