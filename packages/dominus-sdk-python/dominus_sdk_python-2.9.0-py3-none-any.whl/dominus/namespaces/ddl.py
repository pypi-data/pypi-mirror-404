"""
DDL Namespace - Smith schema and migration operations.

Provides DDL operations and Alembic migration management.
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class DdlNamespace:
    """
    Schema DDL and migration namespace.

    All DDL operations go through /api/smith/* endpoints.

    Usage:
        # Table operations
        await dominus.ddl.create_table("tenant_acme", "users", [
            {"name": "id", "type": "UUID", "primary_key": True},
            {"name": "email", "type": "VARCHAR(255)", "nullable": False}
        ])

        # Column operations
        await dominus.ddl.add_column("tenant_acme", "users", "phone", "VARCHAR(20)")

        # Migrations
        migrations = await dominus.ddl.list_migrations("tenant_acme")

        # Provisioning
        await dominus.ddl.provision_tenant("acme")
        await dominus.ddl.provision_from_category("acme", "healthcare")
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    # ========================================
    # SCHEMA DDL OPERATIONS
    # ========================================

    async def create_table(
        self,
        schema: str,
        table: str,
        columns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new table.

        Args:
            schema: Schema name (e.g., "tenant_acme")
            table: Table name
            columns: List of column definitions:
                [{"name": "id", "type": "UUID", "primary_key": True}]

        Returns:
            Creation confirmation with migration_version
        """
        return await self._client._request(
            endpoint="/api/smith/schema/create-table",
            body={
                "schema": schema,
                "table": table,
                "columns": columns
            }
        )

    async def drop_table(self, schema: str, table: str) -> Dict[str, Any]:
        """Drop a table."""
        return await self._client._request(
            endpoint="/api/smith/schema/drop-table",
            method="DELETE",
            body={"schema": schema, "table": table}
        )

    async def truncate_table(self, schema: str, table: str) -> Dict[str, Any]:
        """Truncate a table (delete all rows)."""
        return await self._client._request(
            endpoint="/api/smith/schema/truncate-table",
            body={"schema": schema, "table": table}
        )

    # ========================================
    # COLUMN OPERATIONS
    # ========================================

    async def add_column(
        self,
        schema: str,
        table: str,
        column: str,
        column_type: str,
        nullable: bool = True,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a column to a table.

        Args:
            schema: Schema name
            table: Table name
            column: Column name
            column_type: PostgreSQL type (e.g., "VARCHAR(100)")
            nullable: Allow NULL values (default: True)
            default: Optional default value

        Returns:
            Alteration confirmation with migration_version
        """
        body = {
            "schema": schema,
            "table": table,
            "column": column,
            "type": column_type,
            "nullable": nullable
        }
        if default is not None:
            body["default"] = default

        return await self._client._request(
            endpoint="/api/smith/schema/add-column",
            body=body
        )

    async def drop_column(
        self,
        schema: str,
        table: str,
        column: str
    ) -> Dict[str, Any]:
        """Drop a column from a table."""
        return await self._client._request(
            endpoint="/api/smith/schema/drop-column",
            method="DELETE",
            body={
                "schema": schema,
                "table": table,
                "column": column
            }
        )

    async def alter_column(
        self,
        schema: str,
        table: str,
        column: str,
        new_type: Optional[str] = None,
        nullable: Optional[bool] = None,
        default: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Alter a column's properties.

        Args:
            schema: Schema name
            table: Table name
            column: Column name
            new_type: New column type
            nullable: Set nullable status
            default: New default value (use "DROP" to remove)

        Returns:
            Alteration confirmation
        """
        body = {
            "schema": schema,
            "table": table,
            "column": column
        }
        if new_type:
            body["type"] = new_type
        if nullable is not None:
            body["nullable"] = nullable
        if default is not None:
            body["default"] = default

        return await self._client._request(
            endpoint="/api/smith/schema/alter-column",
            method="PUT",
            body=body
        )

    async def rename_column(
        self,
        schema: str,
        table: str,
        old_name: str,
        new_name: str
    ) -> Dict[str, Any]:
        """Rename a column."""
        return await self._client._request(
            endpoint="/api/smith/schema/rename-column",
            body={
                "schema": schema,
                "table": table,
                "old_name": old_name,
                "new_name": new_name
            }
        )

    # ========================================
    # INDEX OPERATIONS
    # ========================================

    async def create_index(
        self,
        schema: str,
        table: str,
        index_name: str,
        columns: List[str],
        unique: bool = False
    ) -> Dict[str, Any]:
        """Create an index on columns."""
        return await self._client._request(
            endpoint="/api/smith/schema/create-index",
            body={
                "schema": schema,
                "table": table,
                "index_name": index_name,
                "columns": columns,
                "unique": unique
            }
        )

    async def drop_index(
        self,
        schema: str,
        index_name: str
    ) -> Dict[str, Any]:
        """Drop an index."""
        return await self._client._request(
            endpoint="/api/smith/schema/drop-index",
            method="DELETE",
            body={"schema": schema, "index_name": index_name}
        )

    # ========================================
    # CONSTRAINT OPERATIONS
    # ========================================

    async def add_constraint(
        self,
        schema: str,
        table: str,
        constraint_name: str,
        constraint_type: str,
        definition: str
    ) -> Dict[str, Any]:
        """Add a constraint to a table."""
        return await self._client._request(
            endpoint="/api/smith/schema/add-constraint",
            body={
                "schema": schema,
                "table": table,
                "constraint_name": constraint_name,
                "constraint_type": constraint_type,
                "definition": definition
            }
        )

    async def drop_constraint(
        self,
        schema: str,
        table: str,
        constraint_name: str
    ) -> Dict[str, Any]:
        """Drop a constraint from a table."""
        return await self._client._request(
            endpoint="/api/smith/schema/drop-constraint",
            method="DELETE",
            body={
                "schema": schema,
                "table": table,
                "constraint_name": constraint_name
            }
        )

    # ========================================
    # RAW DDL (Admin Only)
    # ========================================

    async def execute_raw(self, schema: str, sql: str) -> Dict[str, Any]:
        """
        Execute raw DDL SQL (admin only).

        Use with caution - this bypasses safety checks.
        SQL must be base64 encoded.
        """
        import base64
        sql_b64 = base64.b64encode(sql.encode('utf-8')).decode('utf-8')

        return await self._client._request(
            endpoint="/api/smith/schema/execute-raw-ddl",
            body={"schema": schema, "sql": sql_b64}
        )

    # ========================================
    # MIGRATIONS
    # ========================================

    async def list_migrations(self, schema: str) -> List[Dict[str, Any]]:
        """List migrations for a schema."""
        result = await self._client._request(
            endpoint=f"/api/smith/migrations/list/{schema}",
            method="GET"
        )
        return result if isinstance(result, list) else []

    async def apply_migration(self, schema: str, migration_id: str) -> Dict[str, Any]:
        """
        Apply a specific migration to a schema.

        Args:
            schema: Schema name (e.g., "tenant_acme")
            migration_id: Migration version ID to apply

        Returns:
            Dict with application result
        """
        return await self._client._request(
            endpoint=f"/api/smith/migrations/apply/{schema}",
            body={"migration_id": migration_id}
        )

    async def get_current_version(self, schema: str) -> Dict[str, Any]:
        """Get current migration version for a schema."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/current/{schema}",
            method="GET"
        )

    async def get_migration_file(self, schema: str, version: str) -> Dict[str, Any]:
        """Get a specific migration file content."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/file/{schema}/{version}",
            method="GET"
        )

    async def migration_history(self, schema: str) -> Dict[str, Any]:
        """Get migration history for a schema."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/history/{schema}",
            method="GET"
        )

    async def rollback_migration(self, schema: str, version: str) -> Dict[str, Any]:
        """Rollback to a previous migration version."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/rollback/{schema}",
            body={"version": version}
        )

    async def compare_versions(self, schemas: List[str]) -> Dict[str, Any]:
        """Compare migration versions across multiple schemas."""
        schemas_param = ",".join(schemas)
        return await self._client._request(
            endpoint=f"/api/smith/migrations/compare?schemas={schemas_param}",
            method="GET"
        )

    # ========================================
    # CATEGORY MIGRATIONS
    # ========================================

    async def list_category_migrations(self, category_slug: str) -> Dict[str, Any]:
        """List migrations for a tenant category."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/category/{category_slug}/list",
            method="GET"
        )

    async def get_category_migration_file(
        self,
        category_slug: str,
        version: str
    ) -> Dict[str, Any]:
        """Get a specific category migration file."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/category/{category_slug}/file/{version}",
            method="GET"
        )

    async def category_sync_status(self, category_slug: str) -> Dict[str, Any]:
        """Get sync status for all tenants in a category."""
        return await self._client._request(
            endpoint=f"/api/smith/migrations/category/{category_slug}/sync-status",
            method="GET"
        )

    async def list_public_migrations(self) -> Dict[str, Any]:
        """List migrations for the public schema."""
        return await self._client._request(
            endpoint="/api/smith/migrations/public/list",
            method="GET"
        )

    # ========================================
    # CATEGORY DDL (Atomic across tenants)
    # ========================================

    async def category_create_table(
        self,
        category_slug: str,
        table: str,
        columns: List[Dict[str, Any]],
        target: str = "category"
    ) -> Dict[str, Any]:
        """
        Create table in all tenant schemas of a category (atomic).

        Args:
            category_slug: Category identifier
            table: Table name
            columns: Column definitions
            target: "category" or "public"
        """
        return await self._client._request(
            endpoint="/api/smith/category/create-table",
            body={
                "target": target,
                "category_slug": category_slug,
                "table": table,
                "columns": columns
            }
        )

    async def category_add_column(
        self,
        category_slug: str,
        table: str,
        column: str,
        column_type: str,
        nullable: bool = True,
        target: str = "category"
    ) -> Dict[str, Any]:
        """Add column to all tenant schemas of a category (atomic)."""
        return await self._client._request(
            endpoint="/api/smith/category/add-column",
            body={
                "target": target,
                "category_slug": category_slug,
                "table": table,
                "column": column,
                "type": column_type,
                "nullable": nullable
            }
        )

    async def category_drop_table(
        self,
        category_slug: str,
        table: str,
        target: str = "category"
    ) -> Dict[str, Any]:
        """Drop table from all tenant schemas of a category (admin only)."""
        return await self._client._request(
            endpoint="/api/smith/category/drop-table",
            method="DELETE",
            body={
                "target": target,
                "category_slug": category_slug,
                "table": table
            }
        )

    async def category_drop_column(
        self,
        category_slug: str,
        table: str,
        column: str,
        target: str = "category"
    ) -> Dict[str, Any]:
        """Drop column from all tenant schemas of a category (admin only)."""
        return await self._client._request(
            endpoint="/api/smith/category/drop-column",
            method="DELETE",
            body={
                "target": target,
                "category_slug": category_slug,
                "table": table,
                "column": column
            }
        )

    async def category_create_index(
        self,
        category_slug: str,
        table: str,
        index_name: str,
        columns: List[str],
        unique: bool = False,
        target: str = "category"
    ) -> Dict[str, Any]:
        """Create index in all tenant schemas of a category (atomic)."""
        return await self._client._request(
            endpoint="/api/smith/category/create-index",
            body={
                "target": target,
                "category_slug": category_slug,
                "table": table,
                "index_name": index_name,
                "columns": columns,
                "unique": unique
            }
        )

    # ========================================
    # TENANT PROVISIONING
    # ========================================

    async def provision_tenant(self, tenant_slug: str) -> Dict[str, Any]:
        """
        Provision a new tenant schema.

        Creates: tenant_{slug} schema with proper permissions.

        Args:
            tenant_slug: Tenant identifier (becomes schema name: tenant_{slug})

        Returns:
            Provisioning result with schema name and initial version
        """
        return await self._client._request(
            endpoint="/api/smith/provision/tenant-schema",
            body={"tenant_slug": tenant_slug}
        )

    async def deprovision_tenant(
        self,
        tenant_slug: str,
        cascade: bool = False
    ) -> Dict[str, Any]:
        """
        Drop a tenant schema (destructive).

        Args:
            tenant_slug: Tenant identifier
            cascade: If True, drops all dependent objects
        """
        return await self._client._request(
            endpoint="/api/smith/provision/tenant-schema",
            method="DELETE",
            body={"tenant_slug": tenant_slug, "cascade": cascade}
        )

    async def provision_from_category(
        self,
        tenant_slug: str,
        category_slug: str
    ) -> Dict[str, Any]:
        """
        Provision tenant with category-specific migrations.

        Args:
            tenant_slug: Tenant identifier
            category_slug: Category for migrations to inherit

        Returns:
            Provisioning result with applied migrations
        """
        return await self._client._request(
            endpoint="/api/smith/provision/tenant-from-category",
            body={
                "tenant_slug": tenant_slug,
                "category_slug": category_slug
            }
        )

    async def provision_status(self, tenant_slug: str) -> Dict[str, Any]:
        """Get provision status for a tenant."""
        return await self._client._request(
            endpoint=f"/api/smith/provision/status/{tenant_slug}",
            method="GET"
        )

    async def list_provisions(self) -> List[Dict[str, Any]]:
        """List all provisioned tenant schemas."""
        result = await self._client._request(
            endpoint="/api/smith/provision/list",
            method="GET"
        )
        return result if isinstance(result, list) else []

    async def list_categories(self) -> List[Dict[str, Any]]:
        """List all tenant categories."""
        result = await self._client._request(
            endpoint="/api/smith/provision/categories",
            method="GET"
        )
        return result if isinstance(result, list) else []

    async def category_status(self, category_slug: str) -> Dict[str, Any]:
        """Get migration sync status for all tenants in a category."""
        return await self._client._request(
            endpoint=f"/api/smith/provision/category-status/{category_slug}",
            method="GET"
        )

    async def tenants_by_category(self, category_slug: str) -> Dict[str, Any]:
        """List all tenants in a category."""
        return await self._client._request(
            endpoint=f"/api/smith/provision/tenants-by-category/{category_slug}",
            method="GET"
        )

    # ========================================
    # SCHEMA BUILDER (UI SUPPORT)
    # ========================================

    async def get_category_structure(self, category_slug: str) -> Dict[str, Any]:
        """
        Get schema structure for a category (for Schema Builder UI).

        Returns tables, columns, indexes, constraints for all tables.

        Returns:
            Dict with category, tenant_count, tables, current_version, migration_count
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/structure",
            method="GET"
        )

    async def get_category_migration_history(self, category_slug: str) -> Dict[str, Any]:
        """
        Get migration history for a category.

        Returns:
            Dict with migrations, stored_versions, current_version, total
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/migrations",
            method="GET"
        )

    async def preview_migration(
        self,
        category_slug: str,
        operation: str,
        params: Dict[str, Any],
        migration_name: str
    ) -> Dict[str, Any]:
        """
        Preview a migration before applying.

        Args:
            category_slug: Category identifier
            operation: Operation type (create_table, add_column, etc.)
            params: Operation parameters
            migration_name: Human-readable migration name

        Returns:
            Dict with affected_tenants, migration_preview, sql_preview
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/preview-migration",
            body={
                "operation": operation,
                "params": params,
                "migration_name": migration_name
            }
        )

    async def apply_builder_migration(
        self,
        category_slug: str,
        operation: str,
        params: Dict[str, Any],
        migration_name: str
    ) -> Dict[str, Any]:
        """
        Apply a migration from Schema Builder.

        Args:
            category_slug: Category identifier
            operation: Operation type (create_table, add_column, etc.)
            params: Operation parameters
            migration_name: Human-readable migration name

        Returns:
            Dict with success, migration_id, b2_key, applied_schemas, tenant_count, versions_recorded
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/apply-migration",
            body={
                "operation": operation,
                "params": params,
                "migration_name": migration_name
            },
            timeout=120000  # 2 minutes for migration operations
        )

    async def get_builder_migration_file(
        self,
        category_slug: str,
        version_id: str
    ) -> Dict[str, Any]:
        """
        Get a specific migration file content from B2 storage.

        Args:
            category_slug: Category identifier
            version_id: Migration version ID

        Returns:
            Dict with version_id, content, migration_name, b2_key
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/migrations/{version_id}",
            method="GET"
        )

    async def get_tenant_sync_status(self, category_slug: str) -> Dict[str, Any]:
        """
        Get sync status for all tenants in a category.

        Shows which tenants are on which migration version.

        Returns:
            Dict with category_slug, latest_version, total_tenants, synced_count,
            pending_count, tenants
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/sync-status",
            method="GET"
        )

    async def sync_tenants_to_latest(self, category_slug: str) -> Dict[str, Any]:
        """
        Sync all tenants in a category to the latest migration version.

        Applies any pending migrations to tenants that are behind.

        Returns:
            Dict with success, message, synced_count, failed_count, results
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/sync-tenants",
            method="POST",
            timeout=120000  # 2 minutes for sync operations
        )

    # ========================================
    # RESET / DELETE OPERATIONS
    # ========================================

    async def reset_category_schema(self, category_slug: str) -> Dict[str, Any]:
        """
        Factory reset a category's schema.

        WARNING: This is a destructive operation that:
        - Drops ALL tenant schemas in this category (CASCADE)
        - Clears ALL migration history from meta.alembic_version
        - Recreates empty schemas for each tenant
        - Deletes ALL migration files from B2 storage

        After reset, the category is back to a blank slate.

        Returns:
            Dict with success, message, reset_count, failed_count, migrations_deleted, results
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/reset",
            method="DELETE",
            timeout=120000  # 2 minutes for reset operations
        )

    async def reset_tenant_schema(
        self,
        category_slug: str,
        tenant_slug: str
    ) -> Dict[str, Any]:
        """
        Reset a single tenant's schema to blank.

        WARNING: This is a destructive operation that:
        - Clears the tenant's migration history from meta.alembic_version
        - Drops the tenant's schema with CASCADE
        - Recreates an empty schema

        The tenant can then re-sync to apply current category migrations.

        Returns:
            Dict with success, message, tenant_slug, schema, versions_cleared
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/tenants/{tenant_slug}/reset",
            method="DELETE",
            timeout=60000  # 1 minute for single tenant reset
        )

    async def delete_migration(
        self,
        category_slug: str,
        version_id: str
    ) -> Dict[str, Any]:
        """
        Delete a single migration file from B2 storage.

        WARNING: This does NOT clean up meta.alembic_version records.
        Tenants that have already applied this migration keep their history.
        Use with caution - typically only for cleaning up test migrations.

        Returns:
            Dict with success, message, version_id, category_slug
        """
        return await self._client._request(
            endpoint=f"/api/smith/builder/category/{category_slug}/migrations/{version_id}",
            method="DELETE"
        )
