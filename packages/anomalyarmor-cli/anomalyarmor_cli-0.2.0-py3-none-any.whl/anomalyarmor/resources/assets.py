"""Assets resource for the Armor SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from anomalyarmor.models import Asset, ConnectionTestResult, DiscoveryJob
from anomalyarmor.resources.base import BaseResource

if TYPE_CHECKING:
    pass


class AssetsResource(BaseResource):
    """Resource for interacting with assets.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # List all assets
        >>> assets = client.assets.list()
        >>>
        >>> # List with filters
        >>> pg_assets = client.assets.list(source="postgresql")
        >>>
        >>> # Get a specific asset
        >>> asset = client.assets.get("postgresql.mydb.public.users")
        >>>
        >>> # Create a new asset (TECH-758)
        >>> asset = client.assets.create(
        ...     name="Analytics Warehouse",
        ...     source_type="snowflake",
        ...     connection_config={...}
        ... )
    """

    def list(
        self,
        source: str | None = None,
        asset_type: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Asset]:
        """List assets with optional filters.

        Args:
            source: Filter by source type (e.g., "postgresql", "databricks")
            asset_type: Filter by asset type (e.g., "table", "view")
            search: Search in asset names
            limit: Maximum number of assets to return (default 50, max 100)
            offset: Number of assets to skip for pagination

        Returns:
            List of Asset objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if source:
            params["source"] = source
        if asset_type:
            params["asset_type"] = asset_type
        if search:
            params["search"] = search

        response = self._get("/assets", params=params)
        data = response.get("data", {}).get("data", [])
        return [Asset.model_validate(item) for item in data]

    def get(self, asset_id: str) -> Asset:
        """Get a specific asset by ID or qualified name.

        Args:
            asset_id: Asset UUID or qualified name (e.g., "postgresql.mydb.public.users")

        Returns:
            Asset object

        Raises:
            NotFoundError: If asset is not found
        """
        response = self._get(f"/assets/{asset_id}")
        return Asset.model_validate(response.get("data", {}))

    # =========================================================================
    # TECH-758: Asset Creation Methods
    # =========================================================================

    def create(
        self,
        name: str,
        source_type: str,
        connection_config: dict[str, Any],
        description: str | None = None,
    ) -> Asset:
        """Create a new asset (data source connection).

        Args:
            name: Display name for the asset
            source_type: Database type: "snowflake", "postgresql", "databricks",
                        "bigquery", "redshift", "mysql", "clickhouse"
            connection_config: Connection configuration (varies by source_type)
            description: Optional description

        Returns:
            Created Asset object

        Example:
            >>> asset = client.assets.create(
            ...     name="Analytics Warehouse",
            ...     source_type="snowflake",
            ...     connection_config={
            ...         "account": "abc123.us-east-1",
            ...         "warehouse": "COMPUTE_WH",
            ...         "database": "ANALYTICS",
            ...         "user": "anomalyarmor_user",
            ...         "password": "..."
            ...     }
            ... )
        """
        payload: dict[str, Any] = {
            "name": name,
            "source_type": source_type,
            "connection_config": connection_config,
        }
        if description:
            payload["description"] = description

        response = self._post("/assets", json=payload)
        return Asset.model_validate(response.get("data", {}))

    def test_connection(self, asset_id: str) -> ConnectionTestResult:
        """Test connection to an asset's data source.

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            ConnectionTestResult with success status and details

        Example:
            >>> result = client.assets.test_connection("asset-uuid")
            >>> if result.success:
            ...     print("Connection successful!")
            ... else:
            ...     print(f"Failed: {result.error_message}")
        """
        response = self._post(f"/assets/{asset_id}/test-connection")
        return ConnectionTestResult.model_validate(response.get("data", {}))

    def trigger_discovery(self, asset_id: str) -> DiscoveryJob:
        """Trigger schema discovery for an asset.

        Starts an async job that crawls the data source to discover
        tables, columns, and metadata. Use jobs.status() to track progress.

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            DiscoveryJob with job_id for tracking

        Example:
            >>> job = client.assets.trigger_discovery("asset-uuid")
            >>> print(f"Discovery started: {job.job_id}")
            >>>
            >>> # Poll for completion
            >>> import time
            >>> status = client.jobs.status(job.job_id)
            >>> while status.get("status") == "running":
            ...     time.sleep(5)
            ...     status = client.jobs.status(job.job_id)
        """
        response = self._post(f"/assets/{asset_id}/discover")
        return DiscoveryJob.model_validate(response.get("data", {}))
