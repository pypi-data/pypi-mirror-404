"""Metrics resource for the Armor SDK (TECH-712)."""

from __future__ import annotations

import builtins
from typing import Any

from anomalyarmor.models import (
    MetricDefinition,
    MetricsDryRunResponse,
    MetricSnapshot,
    MetricsSummary,
)
from anomalyarmor.resources.base import BaseResource


class MetricsResource(BaseResource):
    """Resource for interacting with data quality metrics.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Get metrics summary for an asset
        >>> summary = client.metrics.summary("asset-uuid")
        >>> print(f"Active metrics: {summary.active_metrics}")
        >>>
        >>> # List all metrics for an asset
        >>> metrics = client.metrics.list("asset-uuid")
        >>> for m in metrics:
        ...     print(f"{m.metric_type}: {m.table_path}")
        >>>
        >>> # Create a new metric
        >>> metric = client.metrics.create(
        ...     "asset-uuid",
        ...     metric_type="null_percent",
        ...     table_path="catalog.schema.table",
        ...     column_name="email",
        ... )
    """

    def summary(self, asset_id: str) -> MetricsSummary:
        """Get metrics summary for an asset.

        Args:
            asset_id: Asset UUID

        Returns:
            MetricsSummary with counts and last capture time
        """
        response = self._get(f"/metrics/{asset_id}/summary")
        return MetricsSummary.model_validate(response.get("data", {}))

    def list(
        self,
        asset_id: str,
        metric_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[MetricDefinition]:
        """List metrics for an asset.

        Args:
            asset_id: Asset UUID
            metric_type: Filter by type (row_count, null_percent, etc.)
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of MetricDefinition objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if metric_type is not None:
            params["metric_type"] = metric_type
        if is_active is not None:
            params["is_active"] = is_active

        response = self._get(f"/metrics/{asset_id}", params=params)
        data = response.get("data", {}).get("items", [])
        return [MetricDefinition.model_validate(item) for item in data]

    def get(
        self,
        asset_id: str,
        metric_id: str,
        include_snapshots: bool = True,
        snapshot_limit: int = 30,
    ) -> MetricDefinition:
        """Get metric details with optional snapshots.

        Args:
            asset_id: Asset UUID
            metric_id: Metric UUID
            include_snapshots: Whether to include recent snapshots
            snapshot_limit: Maximum number of snapshots to include

        Returns:
            MetricDefinition object (with snapshots if requested)

        Raises:
            NotFoundError: If metric is not found
        """
        params: dict[str, Any] = {
            "include_snapshots": include_snapshots,
            "snapshot_limit": snapshot_limit,
        }
        response = self._get(f"/metrics/{asset_id}/{metric_id}", params=params)
        return MetricDefinition.model_validate(response.get("data", {}))

    def create(
        self,
        asset_id: str,
        metric_type: str,
        table_path: str,
        column_name: str | None = None,
        capture_interval: str = "daily",
        sensitivity: float = 1.0,
        group_by_columns: builtins.list[str] | None = None,
        percentile_value: float | None = None,
    ) -> MetricDefinition:
        """Create a new metric.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            metric_type: Type (row_count, null_percent, distinct_count, etc.)
            table_path: Full table path (catalog.schema.table)
            column_name: Column name (required for column-level metrics)
            capture_interval: Capture interval (hourly, daily, weekly)
            sensitivity: Sensitivity multiplier for anomaly detection
            group_by_columns: Columns to group by for grouped metrics
            percentile_value: Percentile value (for percentile metrics)

        Returns:
            Created MetricDefinition

        Raises:
            ValidationError: If required fields are missing
            PermissionError: If API key doesn't have write scope
        """
        payload: dict[str, Any] = {
            "metric_type": metric_type,
            "table_path": table_path,
            "capture_interval": capture_interval,
            "sensitivity": sensitivity,
        }
        if column_name is not None:
            payload["column_name"] = column_name
        if group_by_columns is not None:
            payload["group_by_columns"] = group_by_columns
        if percentile_value is not None:
            payload["percentile_value"] = percentile_value

        response = self._post(f"/metrics/{asset_id}", json=payload)
        return MetricDefinition.model_validate(response.get("data", {}))

    def update(
        self,
        asset_id: str,
        metric_id: str,
        is_active: bool | None = None,
        capture_interval: str | None = None,
        sensitivity: float | None = None,
    ) -> MetricDefinition:
        """Update a metric.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            metric_id: Metric UUID
            is_active: Whether metric is active
            capture_interval: New capture interval
            sensitivity: New sensitivity multiplier

        Returns:
            Updated MetricDefinition

        Raises:
            NotFoundError: If metric is not found
            PermissionError: If API key doesn't have write scope
        """
        payload: dict[str, Any] = {}
        if is_active is not None:
            payload["is_active"] = is_active
        if capture_interval is not None:
            payload["capture_interval"] = capture_interval
        if sensitivity is not None:
            payload["sensitivity"] = sensitivity

        response = self._patch(f"/metrics/{asset_id}/{metric_id}", json=payload)
        return MetricDefinition.model_validate(response.get("data", {}))

    def delete(self, asset_id: str, metric_id: str) -> None:
        """Delete a metric.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            metric_id: Metric UUID

        Raises:
            NotFoundError: If metric is not found
            PermissionError: If API key doesn't have write scope
        """
        self._delete(f"/metrics/{asset_id}/{metric_id}")

    def capture(self, asset_id: str, metric_id: str) -> dict[str, Any]:
        """Trigger an immediate metric capture.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            metric_id: Metric UUID

        Returns:
            Dictionary with snapshot_count and snapshots

        Raises:
            NotFoundError: If metric is not found
            PermissionError: If API key doesn't have write scope
        """
        response = self._post(f"/metrics/{asset_id}/{metric_id}/capture")
        data: dict[str, Any] = response.get("data", {})
        return data

    def snapshots(
        self,
        asset_id: str,
        metric_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[MetricSnapshot]:
        """List snapshots for a metric.

        Args:
            asset_id: Asset UUID
            metric_id: Metric UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of MetricSnapshot objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = self._get(f"/metrics/{asset_id}/{metric_id}/snapshots", params=params)
        data = response.get("data", {}).get("items", [])
        return [MetricSnapshot.model_validate(item) for item in data]

    # =========================================================================
    # TECH-771: Dry-Run / Preview APIs
    # =========================================================================

    def dry_run(
        self,
        asset_id: str,
        table_path: str,
        metric_type: str,
        column_name: str | None = None,
        sensitivity: float = 1.0,
        lookback_days: int = 30,
    ) -> MetricsDryRunResponse:
        """Preview what anomalies would have been detected with proposed metric.

        Simulates metric monitoring over historical data to help understand
        the metric's behavior and tune sensitivity before enabling.

        Args:
            asset_id: Asset UUID
            table_path: Full table path (catalog.schema.table)
            metric_type: Type (row_count, null_percent, distinct_count, etc.)
            column_name: Column name (required for column-level metrics)
            sensitivity: Sensitivity multiplier for anomaly detection
            lookback_days: Days of history to analyze (default 30)

        Returns:
            MetricsDryRunResponse with anomaly simulation results

        Example:
            >>> result = client.metrics.dry_run(
            ...     asset_id="asset-uuid",
            ...     table_path="catalog.schema.orders",
            ...     metric_type="null_percent",
            ...     column_name="email",
            ...     sensitivity=1.5,
            ...     lookback_days=14,
            ... )
            >>> print(f"Anomaly rate: {result.anomaly_rate_percent}%")
            >>> print(f"Recommendation: {result.recommendation}")
        """
        payload: dict[str, Any] = {
            "asset_id": asset_id,
            "table_path": table_path,
            "metric_type": metric_type,
            "sensitivity": sensitivity,
            "lookback_days": lookback_days,
        }
        if column_name is not None:
            payload["column_name"] = column_name
        response = self._post("/metrics/dry-run", json=payload)
        return MetricsDryRunResponse.model_validate(response.get("data", {}))
