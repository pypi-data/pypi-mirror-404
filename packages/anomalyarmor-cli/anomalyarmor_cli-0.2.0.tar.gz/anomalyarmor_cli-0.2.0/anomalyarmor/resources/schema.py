"""Schema resource for the Armor SDK."""

from __future__ import annotations

import builtins
from typing import Any

from anomalyarmor.models import (
    SchemaBaseline,
    SchemaChange,
    SchemaDryRunResponse,
    SchemaMonitoringStatus,
    SchemaSummary,
)
from anomalyarmor.resources.base import BaseResource


class SchemaResource(BaseResource):
    """Resource for interacting with schema drift monitoring.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Get summary
        >>> summary = client.schema.summary()
        >>> if summary.critical_count > 0:
        ...     print(f"Warning: {summary.critical_count} critical changes!")
        >>>
        >>> # List unacknowledged changes
        >>> changes = client.schema.changes(unacknowledged_only=True)
        >>>
        >>> # Get changes for specific asset
        >>> asset_schema = client.schema.get("postgresql.mydb.public.users")
    """

    def summary(self) -> SchemaSummary:
        """Get a summary of schema changes across all assets.

        Returns:
            SchemaSummary with counts by severity
        """
        response = self._get("/schema/summary")
        return SchemaSummary.model_validate(response.get("data", {}))

    def changes(
        self,
        asset_id: str | None = None,
        severity: str | None = None,
        unacknowledged_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[SchemaChange]:
        """List schema changes with optional filters.

        Args:
            asset_id: Filter by asset UUID or qualified name
            severity: Filter by severity ("critical", "warning", "info")
            unacknowledged_only: Only return unacknowledged changes
            limit: Maximum number of results (default 50, max 100)
            offset: Number of results to skip

        Returns:
            List of SchemaChange objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if asset_id:
            params["asset_id"] = asset_id
        if severity:
            params["severity"] = severity
        if unacknowledged_only:
            params["unacknowledged_only"] = True

        response = self._get("/schema/changes", params=params)
        data = response.get("data", {}).get("data", [])
        return [SchemaChange.model_validate(item) for item in data]

    def get(self, asset_id: str) -> dict[str, Any]:
        """Get current schema and recent changes for an asset.

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            Dict with asset_id, qualified_name, recent_changes, total_unacknowledged

        Raises:
            NotFoundError: If asset is not found
        """
        response = self._get(f"/schema/{asset_id}")
        data = response.get("data", {})
        return data if isinstance(data, dict) else {}

    # =========================================================================
    # TECH-758: Schema Baseline and Monitoring
    # =========================================================================

    def create_baseline(
        self,
        asset_id: str,
        description: str | None = None,
    ) -> SchemaBaseline:
        """Create a schema baseline for an asset.

        Captures the current schema as the baseline for drift detection.

        Args:
            asset_id: Asset UUID or qualified name
            description: Optional description for the baseline

        Returns:
            SchemaBaseline with captured schema info

        Example:
            >>> baseline = client.schema.create_baseline(
            ...     asset_id="asset-uuid",
            ...     description="Initial production baseline"
            ... )
            >>> print(f"Captured {baseline.column_count} columns")
        """
        payload: dict[str, Any] = {}
        if description:
            payload["description"] = description

        response = self._post(f"/schema/{asset_id}/baseline", json=payload)
        return SchemaBaseline.model_validate(response.get("data", {}))

    def enable_monitoring(
        self,
        asset_id: str,
        schedule_type: str = "daily",
        auto_create_baseline: bool = True,
    ) -> SchemaMonitoringStatus:
        """Enable schema drift monitoring for an asset.

        If no baseline exists and auto_create_baseline=True, one will be
        created automatically.

        Args:
            asset_id: Asset UUID or qualified name
            schedule_type: Check schedule - "hourly", "every_4_hours", "daily", "weekly"
            auto_create_baseline: Create baseline if none exists (default True)

        Returns:
            SchemaMonitoringStatus with current settings

        Example:
            >>> config = client.schema.enable_monitoring(
            ...     asset_id="asset-uuid",
            ...     schedule_type="daily",
            ... )
            >>> print(f"Next check: {config.next_check_at}")
        """
        payload = {
            "schedule_type": schedule_type,
            "auto_create_baseline": auto_create_baseline,
        }
        response = self._post(f"/schema/{asset_id}/monitoring", json=payload)
        return SchemaMonitoringStatus.model_validate(response.get("data", {}))

    def disable_monitoring(self, asset_id: str) -> dict[str, Any]:
        """Disable schema drift monitoring for an asset (keeps baseline).

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            Dict with monitoring_enabled=False and asset_id

        Example:
            >>> client.schema.disable_monitoring("asset-uuid")
        """
        response = self._delete(f"/schema/{asset_id}/monitoring")
        data = response.get("data", {})
        return data if isinstance(data, dict) else {}

    # =========================================================================
    # TECH-771: Dry-Run / Preview APIs
    # =========================================================================

    def dry_run(
        self,
        asset_id: str,
        table_path: str | None = None,
        lookback_days: int = 30,
    ) -> SchemaDryRunResponse:
        """Preview schema changes that would have been detected over time.

        Simulates schema drift detection over historical data to understand
        change patterns before enabling monitoring.

        Args:
            asset_id: Asset UUID or qualified name
            table_path: Filter to specific table (optional)
            lookback_days: Days of history to analyze (default 30)

        Returns:
            SchemaDryRunResponse with change simulation results

        Example:
            >>> result = client.schema.dry_run(
            ...     asset_id="asset-uuid",
            ...     lookback_days=30,
            ... )
            >>> print(f"Total changes: {result.total_changes}")
            >>> print(f"Changes by type: {result.changes_summary}")
            >>> for change in result.sample_changes[:5]:
            ...     print(f"  {change.change_type}: {change.table_name}")
        """
        payload: dict[str, Any] = {
            "asset_id": asset_id,
            "lookback_days": lookback_days,
        }
        if table_path is not None:
            payload["table_path"] = table_path
        response = self._post("/schema/dry-run", json=payload)
        return SchemaDryRunResponse.model_validate(response.get("data", {}))
