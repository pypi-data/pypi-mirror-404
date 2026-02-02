"""
Admin Namespace - Infrastructure and administrative operations.

Provides admin-level operations for seeding and resetting data.
"""
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class AdminNamespace:
    """
    Administrative operations namespace.

    Provides infrastructure-level operations like reseeding admin data
    and resetting schemas.

    Usage:
        # Reseed admin category with default data
        result = await dominus.admin.reseed_admin_category()

        # Reset and reseed admin category
        result = await dominus.admin.reset_admin_category()
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def reseed_admin_category(self) -> Dict[str, Any]:
        """
        Reseed the admin category with default data.

        Adds default scopes, roles, and navigation items to the admin
        tenant category without dropping existing data.

        Returns:
            Dict with success status, message, and seeded_entities
        """
        return await self._client._request(
            endpoint="/api/admin/reseed",
            method="POST"
        )

    async def reset_admin_category(self) -> Dict[str, Any]:
        """
        Reset and reseed the admin category.

        Drops all data from admin schemas and reseeds with default data.
        WARNING: This is a destructive operation.

        Returns:
            Dict with success status, message, and operations
        """
        return await self._client._request(
            endpoint="/api/admin/reset",
            method="POST"
        )
