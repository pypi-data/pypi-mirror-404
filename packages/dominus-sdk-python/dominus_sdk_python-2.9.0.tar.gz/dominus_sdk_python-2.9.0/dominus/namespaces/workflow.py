"""
Workflow Namespace - Workflow management operations.

Provides CRUD operations for workflows, categories/pipelines, and templates.
Routes through gateway to dominus-workflow-manager service.

Usage:
    from dominus import dominus

    # Workflow CRUD
    workflow = await dominus.workflow.save(
        name="My Workflow",
        yaml_content="name: My Workflow\nnodes: []",
        description="A test workflow"
    )
    workflows = await dominus.workflow.list()
    workflow = await dominus.workflow.get(workflow_id, include_content=True)
    await dominus.workflow.delete(workflow_id)

    # Categories (execution pipelines)
    category = await dominus.workflow.create_category(
        name="Intake Pipeline",
        description="Patient intake workflow sequence"
    )
    await dominus.workflow.add_to_category(category_id, workflow_id)
    categories = await dominus.workflow.list_categories()

    # Templates
    templates = await dominus.workflow.list_templates()
    await dominus.workflow.copy_template(template_id)

    # Execution
    result = await dominus.workflow.execute(workflow_id, context={"key": "value"})
    result = await dominus.workflow.execute_async(workflow_id, callback_url="...")
    result = await dominus.workflow.execute_category(category_id)
"""
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class WorkflowNamespace:
    """
    Workflow management namespace.

    Provides operations for workflow CRUD, categories/pipelines, templates,
    and execution via the dominus-workflow-manager service.
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    async def _api(
        self,
        endpoint: str,
        method: str = "POST",
        body: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make gateway-routed API request to workflow-manager."""
        return await self._client._request(
            endpoint=endpoint,
            method=method,
            body=body,
            use_gateway=True
        )

    # ========================================
    # Workflow CRUD
    # ========================================

    async def save(
        self,
        name: str,
        yaml_content: str,
        workflow_id: Optional[str] = None,
        tenant_slug: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: bool = False,
    ) -> Dict[str, Any]:
        """
        Save a workflow (create or update).

        Args:
            name: Workflow display name
            yaml_content: YAML workflow definition
            workflow_id: Optional ID for updates (omit for create)
            tenant_slug: Optional tenant scope
            description: Optional description
            category_id: Optional category to assign
            tags: Optional list of tags
            is_template: Whether this is a template

        Returns:
            Dict with workflow metadata
        """
        body: Dict[str, Any] = {
            "name": name,
            "yaml_content": yaml_content,
        }
        if workflow_id:
            body["workflow_id"] = workflow_id
        if tenant_slug:
            body["tenant_slug"] = tenant_slug
        if description:
            body["description"] = description
        if category_id:
            body["category_id"] = category_id
        if tags:
            body["tags"] = tags
        if is_template:
            body["is_template"] = is_template

        return await self._api(
            endpoint="/api/workflow/workflows",
            body=body
        )

    async def get(
        self,
        workflow_id: str,
        include_content: bool = False
    ) -> Dict[str, Any]:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow UUID
            include_content: Whether to include YAML content

        Returns:
            Dict with workflow metadata and optionally content
        """
        endpoint = f"/api/workflow/workflows/{workflow_id}"
        if include_content:
            endpoint += "?include_content=true"
        return await self._api(endpoint=endpoint, method="GET")

    async def list(
        self,
        tenant_slug: Optional[str] = None,
        category_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List workflows.

        Args:
            tenant_slug: Filter by tenant
            category_id: Filter by category
            tags: Filter by tags (any match)
            is_template: Filter by template status
            search: Search in name/description
            limit: Max results
            offset: Pagination offset

        Returns:
            List of workflow metadata dicts
        """
        body: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tenant_slug:
            body["tenant_slug"] = tenant_slug
        if category_id:
            body["category_id"] = category_id
        if tags:
            body["tags"] = tags
        if is_template is not None:
            body["is_template"] = is_template
        if search:
            body["search"] = search

        result = await self._api(
            endpoint="/api/workflow/workflows/list",
            body=body
        )
        return result.get("workflows", result) if isinstance(result, dict) else result

    async def delete(self, workflow_id: str) -> Dict[str, Any]:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Dict with deletion status
        """
        return await self._api(
            endpoint=f"/api/workflow/workflows/{workflow_id}",
            method="DELETE"
        )

    # ========================================
    # Categories (Execution Pipelines)
    # ========================================

    async def create_category(
        self,
        name: str,
        tenant_slug: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a category (execution pipeline).

        Args:
            name: Category display name
            tenant_slug: Optional tenant scope
            description: Optional description

        Returns:
            Dict with category metadata
        """
        body: Dict[str, Any] = {"name": name}
        if tenant_slug:
            body["tenant_slug"] = tenant_slug
        if description:
            body["description"] = description

        return await self._api(
            endpoint="/api/workflow/categories",
            body=body
        )

    async def get_category(
        self,
        category_id: str,
        include_workflows: bool = False
    ) -> Dict[str, Any]:
        """
        Get a category by ID.

        Args:
            category_id: Category UUID
            include_workflows: Whether to include workflow list

        Returns:
            Dict with category metadata and optionally workflows
        """
        endpoint = f"/api/workflow/categories/{category_id}"
        if include_workflows:
            endpoint += "?include_workflows=true"
        return await self._api(endpoint=endpoint, method="GET")

    async def list_categories(
        self,
        tenant_slug: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List categories.

        Args:
            tenant_slug: Filter by tenant
            limit: Max results
            offset: Pagination offset

        Returns:
            List of category metadata dicts
        """
        body: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tenant_slug:
            body["tenant_slug"] = tenant_slug

        result = await self._api(
            endpoint="/api/workflow/categories/list",
            body=body
        )
        return result.get("categories", result) if isinstance(result, dict) else result

    async def delete_category(self, category_id: str) -> Dict[str, Any]:
        """
        Delete a category.

        Args:
            category_id: Category UUID

        Returns:
            Dict with deletion status
        """
        return await self._api(
            endpoint=f"/api/workflow/categories/{category_id}",
            method="DELETE"
        )

    async def add_to_category(
        self,
        category_id: str,
        workflow_id: str,
        position: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a workflow to a category.

        Args:
            category_id: Category UUID
            workflow_id: Workflow UUID
            position: Optional position in execution order

        Returns:
            Dict with operation status
        """
        body: Dict[str, Any] = {"workflow_id": workflow_id}
        if position is not None:
            body["position"] = position

        return await self._api(
            endpoint=f"/api/workflow/categories/{category_id}/workflows",
            body=body
        )

    async def remove_from_category(
        self,
        category_id: str,
        workflow_id: str,
    ) -> Dict[str, Any]:
        """
        Remove a workflow from a category.

        Args:
            category_id: Category UUID
            workflow_id: Workflow UUID

        Returns:
            Dict with operation status
        """
        return await self._api(
            endpoint=f"/api/workflow/categories/{category_id}/workflows/{workflow_id}",
            method="DELETE"
        )

    async def reorder_category(
        self,
        category_id: str,
        workflow_order: List[str],
    ) -> Dict[str, Any]:
        """
        Reorder workflows in a category.

        Args:
            category_id: Category UUID
            workflow_order: List of workflow IDs in desired order

        Returns:
            Dict with operation status
        """
        return await self._api(
            endpoint=f"/api/workflow/categories/{category_id}/reorder",
            body={"workflow_order": workflow_order}
        )

    # ========================================
    # Templates
    # ========================================

    async def list_templates(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List available templates.

        Args:
            limit: Max results
            offset: Pagination offset

        Returns:
            List of template metadata dicts
        """
        result = await self._api(
            endpoint="/api/workflow/templates",
            method="GET"
        )
        return result.get("templates", result) if isinstance(result, dict) else result

    async def get_template(
        self,
        template_id: str,
        include_content: bool = False
    ) -> Dict[str, Any]:
        """
        Get a template by ID.

        Args:
            template_id: Template UUID
            include_content: Whether to include YAML content

        Returns:
            Dict with template metadata and optionally content
        """
        endpoint = f"/api/workflow/templates/{template_id}"
        if include_content:
            endpoint += "?include_content=true"
        return await self._api(endpoint=endpoint, method="GET")

    async def copy_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        tenant_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Copy a template to create a new workflow.

        Args:
            template_id: Template UUID to copy
            name: Optional name for the new workflow
            tenant_slug: Optional tenant scope

        Returns:
            Dict with new workflow metadata
        """
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if tenant_slug:
            body["tenant_slug"] = tenant_slug

        return await self._api(
            endpoint=f"/api/workflow/templates/{template_id}/copy",
            body=body
        )

    # ========================================
    # Execution
    # ========================================

    async def execute(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow synchronously.

        Args:
            workflow_id: Workflow UUID
            context: Optional initial context/variables

        Returns:
            Dict with execution result
        """
        body: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "async_mode": False,
        }
        if context:
            body["context"] = context

        return await self._api(
            endpoint="/api/workflow/execute/workflow",
            body=body
        )

    async def execute_async(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a workflow asynchronously.

        Args:
            workflow_id: Workflow UUID
            context: Optional initial context/variables
            callback_url: URL to POST results to when complete

        Returns:
            Dict with execution_id for tracking
        """
        body: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "async_mode": True,
        }
        if context:
            body["context"] = context
        if callback_url:
            body["callback_url"] = callback_url

        return await self._api(
            endpoint="/api/workflow/execute/workflow",
            body=body
        )

    async def execute_category(
        self,
        category_id: str,
        context: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a category/pipeline (all workflows in sequence).

        Categories always execute asynchronously.

        Args:
            category_id: Category UUID
            context: Optional initial context/variables
            callback_url: URL to POST results to when complete

        Returns:
            Dict with execution_id for tracking
        """
        body: Dict[str, Any] = {"category_id": category_id}
        if context:
            body["context"] = context
        if callback_url:
            body["callback_url"] = callback_url

        return await self._api(
            endpoint="/api/workflow/execute/category",
            body=body
        )
