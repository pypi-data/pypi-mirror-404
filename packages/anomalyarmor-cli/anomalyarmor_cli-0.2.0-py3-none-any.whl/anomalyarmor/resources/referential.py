"""Referential integrity resource for the Armor SDK (TECH-712)."""

from __future__ import annotations

import builtins
from typing import Any

from anomalyarmor.models import (
    ReferentialCheck,
    ReferentialCheckResult,
    ReferentialSummary,
)
from anomalyarmor.resources.base import BaseResource


class ReferentialResource(BaseResource):
    """Resource for interacting with referential integrity checks.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # List referential checks for an asset
        >>> checks = client.referential.list("asset-uuid")
        >>> for c in checks:
        ...     print(f"{c.child_table_path} -> {c.parent_table_path}")
        >>>
        >>> # Create a new referential check
        >>> check = client.referential.create(
        ...     "asset-uuid",
        ...     child_table_path="catalog.schema.orders",
        ...     child_column_name="customer_id",
        ...     parent_table_path="catalog.schema.customers",
        ...     parent_column_name="id",
        ... )
        >>>
        >>> # Execute a check immediately
        >>> result = client.referential.execute("asset-uuid", "check-uuid")
        >>> print(f"Orphans: {result.orphan_count}")
    """

    def summary(self, asset_id: str) -> ReferentialSummary:
        """Get referential integrity summary for an asset.

        Args:
            asset_id: Asset UUID or qualified name

        Returns:
            ReferentialSummary with counts and status

        Example:
            >>> summary = client.referential.summary("asset-uuid")
            >>> print(f"Failing checks: {summary.failing_checks}")
        """
        response = self._get(f"/referential/{asset_id}/summary")
        return ReferentialSummary.model_validate(response.get("data", {}))

    def list(
        self,
        asset_id: str,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[ReferentialCheck]:
        """List referential checks for an asset.

        Args:
            asset_id: Asset UUID
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ReferentialCheck objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if is_active is not None:
            params["is_active"] = is_active

        response = self._get(f"/referential/{asset_id}", params=params)
        data = response.get("data", {}).get("items", [])
        return [ReferentialCheck.model_validate(item) for item in data]

    def get(self, asset_id: str, check_id: str) -> ReferentialCheck:
        """Get referential check details with latest result.

        Args:
            asset_id: Asset UUID
            check_id: Check UUID

        Returns:
            ReferentialCheck object

        Raises:
            NotFoundError: If check is not found
        """
        response = self._get(f"/referential/{asset_id}/{check_id}")
        return ReferentialCheck.model_validate(response.get("data", {}))

    def create(
        self,
        asset_id: str,
        child_table_path: str,
        child_column_name: str,
        parent_table_path: str,
        parent_column_name: str,
        name: str | None = None,
        description: str | None = None,
        capture_interval: str = "daily",
        max_orphan_count: int | None = None,
        max_orphan_percent: float | None = None,
        min_child_count: int | None = None,
        max_child_count: int | None = None,
    ) -> ReferentialCheck:
        """Create a new referential integrity check.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            child_table_path: Full path to child table (with FK column)
            child_column_name: Column name in child table (FK)
            parent_table_path: Full path to parent table (with PK column)
            parent_column_name: Column name in parent table (PK)
            name: Human-readable check name
            description: Check description
            capture_interval: Capture interval (hourly, daily, weekly)
            max_orphan_count: Alert if orphan count exceeds this
            max_orphan_percent: Alert if orphan percentage exceeds this
            min_child_count: Minimum expected child count per parent
            max_child_count: Maximum expected child count per parent

        Returns:
            Created ReferentialCheck

        Raises:
            ValidationError: If required fields are missing
            PermissionError: If API key doesn't have write scope
        """
        payload: dict[str, Any] = {
            "child_table_path": child_table_path,
            "child_column_name": child_column_name,
            "parent_table_path": parent_table_path,
            "parent_column_name": parent_column_name,
            "capture_interval": capture_interval,
        }
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if max_orphan_count is not None:
            payload["max_orphan_count"] = max_orphan_count
        if max_orphan_percent is not None:
            payload["max_orphan_percent"] = max_orphan_percent
        if min_child_count is not None:
            payload["min_child_count"] = min_child_count
        if max_child_count is not None:
            payload["max_child_count"] = max_child_count

        response = self._post(f"/referential/{asset_id}", json=payload)
        return ReferentialCheck.model_validate(response.get("data", {}))

    def update(
        self,
        asset_id: str,
        check_id: str,
        is_active: bool | None = None,
        name: str | None = None,
        description: str | None = None,
        capture_interval: str | None = None,
        max_orphan_count: int | None = None,
        max_orphan_percent: float | None = None,
        min_child_count: int | None = None,
        max_child_count: int | None = None,
    ) -> ReferentialCheck:
        """Update a referential check.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            check_id: Check UUID
            is_active: Whether check is active
            name: Check name
            description: Check description
            capture_interval: Capture interval
            max_orphan_count: Max orphan count threshold
            max_orphan_percent: Max orphan percent threshold
            min_child_count: Min child count cardinality
            max_child_count: Max child count cardinality

        Returns:
            Updated ReferentialCheck

        Raises:
            NotFoundError: If check is not found
            PermissionError: If API key doesn't have write scope
        """
        payload: dict[str, Any] = {}
        if is_active is not None:
            payload["is_active"] = is_active
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if capture_interval is not None:
            payload["capture_interval"] = capture_interval
        if max_orphan_count is not None:
            payload["max_orphan_count"] = max_orphan_count
        if max_orphan_percent is not None:
            payload["max_orphan_percent"] = max_orphan_percent
        if min_child_count is not None:
            payload["min_child_count"] = min_child_count
        if max_child_count is not None:
            payload["max_child_count"] = max_child_count

        response = self._patch(f"/referential/{asset_id}/{check_id}", json=payload)
        return ReferentialCheck.model_validate(response.get("data", {}))

    def delete(self, asset_id: str, check_id: str) -> None:
        """Delete a referential check.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            check_id: Check UUID

        Raises:
            NotFoundError: If check is not found
            PermissionError: If API key doesn't have write scope
        """
        self._delete(f"/referential/{asset_id}/{check_id}")

    def execute(self, asset_id: str, check_id: str) -> ReferentialCheckResult:
        """Execute a referential check immediately.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            check_id: Check UUID

        Returns:
            ReferentialCheckResult with status and details

        Raises:
            NotFoundError: If check is not found
            ValidationError: If check is inactive
            PermissionError: If API key doesn't have write scope
        """
        response = self._post(f"/referential/{asset_id}/{check_id}/execute")
        return ReferentialCheckResult.model_validate(response.get("data", {}))

    def results(
        self,
        asset_id: str,
        check_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[ReferentialCheckResult]:
        """List historical results for a referential check.

        Args:
            asset_id: Asset UUID
            check_id: Check UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ReferentialCheckResult objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = self._get(f"/referential/{asset_id}/{check_id}/results", params=params)
        data = response.get("data", {}).get("items", [])
        return [ReferentialCheckResult.model_validate(item) for item in data]
