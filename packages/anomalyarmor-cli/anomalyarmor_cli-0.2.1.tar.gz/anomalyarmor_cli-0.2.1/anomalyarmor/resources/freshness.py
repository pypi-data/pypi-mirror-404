"""Freshness resource for the Armor SDK."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any

from anomalyarmor.models import (
    FreshnessDryRunResponse,
    FreshnessSchedule,
    FreshnessStatus,
    FreshnessSummary,
)
from anomalyarmor.resources.base import BaseResource

if TYPE_CHECKING:
    pass


class FreshnessResource(BaseResource):
    """Resource for interacting with freshness monitoring.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Get overall summary
        >>> summary = client.freshness.summary()
        >>> print(f"Freshness rate: {summary.freshness_rate}%")
        >>>
        >>> # Check specific asset
        >>> status = client.freshness.get("postgresql.mydb.public.users")
        >>> if status.is_stale:
        ...     print(f"Stale for {status.hours_since_update} hours")
        >>>
        >>> # List all stale assets
        >>> stale = client.freshness.list(status="stale")
    """

    def summary(self) -> FreshnessSummary:
        """Get a summary of freshness across all assets.

        Returns:
            FreshnessSummary with counts and rates
        """
        response = self._get("/freshness/summary")
        return FreshnessSummary.model_validate(response.get("data", {}))

    def get(self, asset_id: str) -> FreshnessStatus:
        """Get freshness status for a specific asset.

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            FreshnessStatus object

        Raises:
            NotFoundError: If asset is not found
        """
        response = self._get(f"/freshness/{asset_id}")
        return FreshnessStatus.model_validate(response.get("data", {}))

    def list(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[FreshnessStatus]:
        """List freshness status for all assets.

        Args:
            status: Filter by status ("fresh", "stale", "unknown", "disabled")
            limit: Maximum number of results (default 50, max 100)
            offset: Number of results to skip

        Returns:
            List of FreshnessStatus objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = self._get("/freshness", params=params)
        data = response.get("data", {}).get("data", [])
        return [FreshnessStatus.model_validate(item) for item in data]

    def require_fresh(
        self,
        asset_id: str,
        max_age_hours: float | None = None,
    ) -> FreshnessStatus:
        """Require an asset to be fresh, raising an error if stale.

        This is the recommended way to gate downstream processes on data freshness.
        Use in CI/CD pipelines or before running analytics.

        Args:
            asset_id: Asset UUID or qualified name
            max_age_hours: Maximum acceptable age in hours. If not provided,
                          uses the asset's configured threshold.

        Returns:
            FreshnessStatus object if fresh

        Raises:
            DataStaleError: If asset is stale (hours > max_age_hours)
            NotFoundError: If asset is not found

        Example:
            >>> from anomalyarmor import Client
            >>> from anomalyarmor.exceptions import DataStaleError
            >>>
            >>> client = Client()
            >>> try:
            ...     client.freshness.require_fresh("postgresql.mydb.public.users")
            ...     # Run downstream process
            ... except DataStaleError as e:
            ...     print(f"Data is stale: {e.hours_since_update}h old")
            ...     sys.exit(1)
        """
        from anomalyarmor.exceptions import StalenessError

        status = self.get(asset_id)

        # Determine the threshold to use
        threshold = max_age_hours
        if threshold is None:
            threshold = status.staleness_threshold_hours or 24.0  # Default to 24h

        # Check if stale
        if status.is_stale or (
            status.hours_since_update is not None and status.hours_since_update > threshold
        ):
            raise StalenessError(
                asset=asset_id,
                hours_since_update=status.hours_since_update or 0.0,
                threshold_hours=threshold,
            )

        return status

    def refresh(self, asset_id: str) -> dict[str, Any]:
        """Trigger a freshness check for an asset.

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            Dictionary with job_id, status, and message

        Raises:
            NotFoundError: If asset is not found
            PermissionError: If API key doesn't have write scope
        """
        response = self._post(f"/freshness/{asset_id}/refresh")
        data = response.get("data", {})
        return data if isinstance(data, dict) else {}

    # =========================================================================
    # TECH-758: Freshness Schedule CRUD
    # =========================================================================

    def list_schedules(
        self,
        asset_id: str | None = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[FreshnessSchedule]:
        """List freshness monitoring schedules.

        Args:
            asset_id: Filter by asset UUID or qualified name
            active_only: Only return active schedules
            limit: Maximum results (default 50, max 100)
            offset: Pagination offset

        Returns:
            List of FreshnessSchedule objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if asset_id:
            params["asset_id"] = asset_id
        if active_only:
            params["active_only"] = True

        response = self._get("/freshness/schedules", params=params)
        data = response.get("data", {}).get("data", [])
        return [FreshnessSchedule.model_validate(item) for item in data]

    def create_schedule(
        self,
        asset_id: str,
        table_path: str,
        check_interval: str,
        expected_interval_hours: float | None = None,
        freshness_column: str | None = None,
        monitoring_mode: str = "auto_learn",
        is_active: bool = True,
    ) -> FreshnessSchedule:
        """Create a freshness monitoring schedule.

        Args:
            asset_id: Asset UUID or qualified name
            table_path: Table path (e.g., "public.orders")
            check_interval: Check frequency: "5m", "1h", "6h", "1d", "1w"
            expected_interval_hours: Hours until stale (required for explicit mode)
            freshness_column: Column to check (auto-detected if not provided)
            monitoring_mode: "auto_learn" or "explicit"
            is_active: Whether schedule is active (default True)

        Returns:
            Created FreshnessSchedule object

        Example:
            >>> # Auto-learn mode (recommended)
            >>> schedule = client.freshness.create_schedule(
            ...     asset_id="asset-uuid",
            ...     table_path="public.orders",
            ...     check_interval="1h",
            ... )
            >>>
            >>> # Explicit mode with threshold
            >>> schedule = client.freshness.create_schedule(
            ...     asset_id="asset-uuid",
            ...     table_path="public.orders",
            ...     check_interval="1h",
            ...     expected_interval_hours=24,
            ...     monitoring_mode="explicit",
            ... )
        """
        payload: dict[str, Any] = {
            "asset_id": asset_id,
            "table_path": table_path,
            "check_interval": check_interval,
            "monitoring_mode": monitoring_mode,
            "is_active": is_active,
        }
        if expected_interval_hours is not None:
            payload["expected_interval_hours"] = expected_interval_hours
        if freshness_column is not None:
            payload["freshness_column"] = freshness_column

        response = self._post("/freshness/schedules", json=payload)
        return FreshnessSchedule.model_validate(response.get("data", {}))

    def update_schedule(
        self,
        schedule_id: str,
        check_interval: str | None = None,
        expected_interval_hours: float | None = None,
        freshness_column: str | None = None,
        monitoring_mode: str | None = None,
        is_active: bool | None = None,
    ) -> FreshnessSchedule:
        """Update an existing freshness schedule.

        Args:
            schedule_id: Schedule UUID
            check_interval: New check interval (optional)
            expected_interval_hours: New threshold hours (optional)
            freshness_column: New freshness column (optional)
            monitoring_mode: New mode (optional)
            is_active: New active status (optional)

        Returns:
            Updated FreshnessSchedule object
        """
        payload: dict[str, Any] = {}
        if check_interval is not None:
            payload["check_interval"] = check_interval
        if expected_interval_hours is not None:
            payload["expected_interval_hours"] = expected_interval_hours
        if freshness_column is not None:
            payload["freshness_column"] = freshness_column
        if monitoring_mode is not None:
            payload["monitoring_mode"] = monitoring_mode
        if is_active is not None:
            payload["is_active"] = is_active

        response = self._patch(f"/freshness/schedules/{schedule_id}", json=payload)
        return FreshnessSchedule.model_validate(response.get("data", {}))

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a freshness schedule.

        Args:
            schedule_id: Schedule UUID

        Returns:
            True if deleted successfully
        """
        self._delete(f"/freshness/schedules/{schedule_id}")
        return True

    # =========================================================================
    # TECH-771: Dry-Run / Preview APIs
    # =========================================================================

    def dry_run(
        self,
        asset_id: str,
        table_path: str,
        expected_interval_hours: float,
        lookback_days: int = 7,
    ) -> FreshnessDryRunResponse:
        """Preview what alerts would have fired with proposed freshness settings.

        Simulates freshness monitoring over historical data to help tune thresholds
        before enabling monitoring.

        Args:
            asset_id: Asset UUID or qualified name
            table_path: Table path (e.g., "public.orders")
            expected_interval_hours: Proposed threshold in hours
            lookback_days: Days of history to analyze (default 7)

        Returns:
            FreshnessDryRunResponse with alert simulation results

        Example:
            >>> result = client.freshness.dry_run(
            ...     asset_id="asset-uuid",
            ...     table_path="public.orders",
            ...     expected_interval_hours=24.0,
            ...     lookback_days=14,
            ... )
            >>> print(f"Alert rate: {result.alert_rate_percent}%")
            >>> print(f"Would alert now: {result.would_alert_now}")
            >>> print(f"Recommendation: {result.recommendation}")
        """
        payload = {
            "asset_id": asset_id,
            "table_path": table_path,
            "expected_interval_hours": expected_interval_hours,
            "lookback_days": lookback_days,
        }
        response = self._post("/freshness/dry-run", json=payload)
        return FreshnessDryRunResponse.model_validate(response.get("data", {}))
