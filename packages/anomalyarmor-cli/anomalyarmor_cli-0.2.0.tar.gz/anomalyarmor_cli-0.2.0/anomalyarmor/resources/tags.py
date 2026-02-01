"""Tags resource for the Armor SDK (TECH-646)."""

from __future__ import annotations

import builtins

from anomalyarmor.models import BulkApplyResult, Tag
from anomalyarmor.resources.base import BaseResource


class TagsResource(BaseResource):
    """Resource for managing tags.

    Provides programmatic access to AnomalyArmor's tag management system
    for organizing and categorizing database objects.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Create a tag
        >>> client.tags.create(
        ...     asset="postgresql.analytics",
        ...     name="financial_reporting",
        ...     category="business"
        ... )
        >>>
        >>> # Apply tags to an asset
        >>> client.tags.apply(
        ...     asset="postgresql.analytics",
        ...     tag_names=["financial_reporting", "pii_data"]
        ... )
        >>>
        >>> # List tags for an asset
        >>> tags = client.tags.list(asset="postgresql.analytics")
        >>> for tag in tags:
        ...     print(f"{tag.name} ({tag.category})")
    """

    def create(
        self,
        asset: str,
        name: str,
        object_path: str,
        object_type: str = "table",
        category: str = "business",
        description: str | None = None,
    ) -> Tag:
        """Create a custom tag on a database object.

        Tags are applied to specific objects (tables, columns) within an asset.

        Args:
            asset: Asset identifier (UUID, short UUID, or qualified name like 'postgresql.mydb')
            name: Tag name (e.g., "pii_data", "financial_reporting")
            object_path: Path to the object (e.g., "schema.table" or "schema.table.column")
            object_type: Type of object: "table" or "column" (default: "table")
            category: Tag category: "business", "technical", or "governance" (default: "business")
            description: Optional tag description

        Returns:
            Tag object with the created tag info

        Example:
            >>> tag = client.tags.create(
            ...     asset="postgresql.analytics",
            ...     name="pii_data",
            ...     object_path="gold.customers",
            ...     object_type="table",
            ...     category="governance"
            ... )
        """
        response = self._post(
            "/tags",
            json={
                "asset_id": asset,
                "name": name,
                "category": category,
                "object_type": object_type,
                "object_path": object_path,
                "description": description,
            },
        )
        data = response.get("data", {})
        return Tag(
            id=data.get("id", ""),
            name=data.get("name", name),
            category=data.get("category", category),
            description=data.get("description", description),
            object_path=data.get("object_path"),
            object_type=data.get("object_type"),
            created_at=None,
        )

    def apply(
        self,
        asset: str,
        tag_names: builtins.list[str],
        object_paths: builtins.list[str],
        category: str = "business",
    ) -> BulkApplyResult:
        """Apply multiple tags to database objects within an asset.

        Creates tags on the specified tables or columns. Each tag_name is applied
        to each object_path, so the total operations = len(tag_names) * len(object_paths).

        Args:
            asset: Asset identifier (UUID, short UUID, or qualified name like 'postgresql.mydb')
            tag_names: List of tag names to apply (e.g., ["pii", "financial"])
            object_paths: List of object paths to tag
                (e.g., ["schema.table", "schema.table.column"])
            category: Tag category: "business", "technical", or "governance" (default: "business")

        Returns:
            BulkApplyResult with counts of applied/failed operations

        Example:
            >>> result = client.tags.apply(
            ...     asset="postgresql.analytics",
            ...     tag_names=["financial", "quarterly"],
            ...     object_paths=["gold.fact_orders", "gold.dim_customers"]
            ... )
            >>> print(f"Applied: {result.applied}, Failed: {result.failed}")
        """
        response = self._post(
            "/tags/apply",
            json={
                "asset_id": asset,
                "tag_names": tag_names,
                "object_paths": object_paths,
                "category": category,
            },
        )
        data = response.get("data", {})
        return BulkApplyResult.model_validate(data)

    def bulk_apply(
        self,
        tag_name: str,
        asset_ids: builtins.list[str],
        category: str = "business",
    ) -> BulkApplyResult:
        """Apply a single tag to multiple assets.

        Args:
            tag_name: Tag name to apply
            asset_ids: List of asset identifiers (UUIDs or qualified names)
            category: Tag category

        Returns:
            BulkApplyResult with counts of applied/failed

        Example:
            >>> result = client.tags.bulk_apply(
            ...     tag_name="finance-q4-2024",
            ...     asset_ids=["postgresql.analytics", "postgresql.warehouse"]
            ... )
            >>> print(f"Applied to {result.applied} assets")
        """
        response = self._post(
            "/tags/bulk-apply",
            json={
                "tag_name": tag_name,
                "asset_ids": asset_ids,
                "category": category,
            },
        )
        data = response.get("data", {})
        return BulkApplyResult.model_validate(data)

    def list(
        self,
        asset: str,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[Tag]:
        """List tags for an asset.

        Args:
            asset: Asset identifier (UUID or qualified name)
            category: Optional category filter
            limit: Maximum results (1-500)
            offset: Pagination offset

        Returns:
            List of Tag objects

        Example:
            >>> tags = client.tags.list(asset="postgresql.analytics")
            >>> compliance_tags = [t for t in tags if t.category == "compliance"]
        """
        params = {
            "asset_id": asset,
            "limit": limit,
            "offset": offset,
        }
        if category:
            params["category"] = category

        response = self._get("/tags", params=params)
        data = response.get("data", {})
        tags_data = data.get("tags", [])
        return [Tag.model_validate(t) for t in tags_data]
