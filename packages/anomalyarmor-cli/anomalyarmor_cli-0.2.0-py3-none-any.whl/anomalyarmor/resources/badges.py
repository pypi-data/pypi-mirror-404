"""Badges resource for the Armor SDK (TECH-646)."""

from __future__ import annotations

import builtins
from typing import Any

from anomalyarmor.models import Badge
from anomalyarmor.resources.base import BaseResource


class BadgesResource(BaseResource):
    """Resource for managing report badges.

    Provides programmatic access to AnomalyArmor's report badge system
    for displaying data quality status in documentation, dashboards, and reports.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Create a badge
        >>> badge = client.badges.create(
        ...     asset="postgresql.analytics",
        ...     label="Data Quality",
        ...     tag_filters=["financial_reporting"]
        ... )
        >>> print(f"Badge URL: {badge.badge_url}")
        >>>
        >>> # List all badges
        >>> badges = client.badges.list()
        >>> for badge in badges:
        ...     print(f"{badge.label}: {badge.badge_url}")
    """

    def create(
        self,
        asset: str,
        label: str = "AnomalyArmor",
        tag_filters: builtins.list[str] | None = None,
        schema_drift_enabled: bool = True,
        freshness_enabled: bool = True,
        include_upstream: bool = False,
    ) -> Badge:
        """Create a new report badge.

        Args:
            asset: Asset identifier (UUID or qualified name)
            label: Badge label text (displayed on the badge)
            tag_filters: Tag names to filter which objects are monitored
            schema_drift_enabled: Enable schema drift monitoring
            freshness_enabled: Enable freshness monitoring
            include_upstream: Include upstream dependencies

        Returns:
            Badge with the created badge info and URL

        Example:
            >>> badge = client.badges.create(
            ...     asset="postgresql.analytics",
            ...     label="Finance ETL",
            ...     tag_filters=["finance_q4"],
            ...     schema_drift_enabled=True,
            ...     freshness_enabled=True
            ... )
            >>> # Embed this URL in your documentation
            >>> print(badge.badge_url)
        """
        response = self._post(
            "/badges",
            json={
                "asset_id": asset,
                "label": label,
                "tag_filters": tag_filters or [],
                "schema_drift_enabled": schema_drift_enabled,
                "freshness_enabled": freshness_enabled,
                "include_upstream": include_upstream,
            },
        )
        data = response.get("data", {})
        return Badge.model_validate(data)

    def list(
        self,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[Badge]:
        """List all badges for the company.

        Args:
            active_only: Only return active badges
            limit: Maximum results (1-500)
            offset: Pagination offset

        Returns:
            List of Badge objects

        Example:
            >>> badges = client.badges.list()
            >>> for badge in badges:
            ...     print(f"{badge.label}: {badge.badge_url}")
        """
        params = {
            "active_only": active_only,
            "limit": limit,
            "offset": offset,
        }
        response = self._get("/badges", params=params)
        data = response.get("data", {})
        badges_data = data.get("badges", [])
        return [Badge.model_validate(b) for b in badges_data]

    def get(self, badge_id: str) -> Badge:
        """Get badge details by ID.

        Args:
            badge_id: Badge public UUID or internal ID

        Returns:
            Badge object

        Example:
            >>> badge = client.badges.get("123e4567-e89b-12d3-a456-426614174000")
            >>> print(f"Label: {badge.label}, Active: {badge.is_active}")
        """
        response = self._get(f"/badges/{badge_id}")
        data = response.get("data", {})
        return Badge.model_validate(data)

    def update(
        self,
        badge_id: str,
        label: str | None = None,
        tag_filters: builtins.list[str] | None = None,
        schema_drift_enabled: bool | None = None,
        freshness_enabled: bool | None = None,
        include_upstream: bool | None = None,
        is_active: bool | None = None,
    ) -> Badge:
        """Update a badge configuration.

        Args:
            badge_id: Badge public UUID or internal ID
            label: New badge label
            tag_filters: New tag filters
            schema_drift_enabled: Enable/disable schema drift monitoring
            freshness_enabled: Enable/disable freshness monitoring
            include_upstream: Enable/disable upstream inclusion
            is_active: Enable/disable badge

        Returns:
            Updated Badge object

        Example:
            >>> badge = client.badges.update(
            ...     badge_id="123e4567-e89b-12d3-a456-426614174000",
            ...     label="Finance ETL Updated",
            ...     is_active=False
            ... )
        """

        payload: dict[str, Any] = {}
        if label is not None:
            payload["label"] = label
        if tag_filters is not None:
            payload["tag_filters"] = tag_filters
        if schema_drift_enabled is not None:
            payload["schema_drift_enabled"] = schema_drift_enabled
        if freshness_enabled is not None:
            payload["freshness_enabled"] = freshness_enabled
        if include_upstream is not None:
            payload["include_upstream"] = include_upstream
        if is_active is not None:
            payload["is_active"] = is_active

        response = self._put(f"/badges/{badge_id}", json=payload)
        data = response.get("data", {})
        return Badge.model_validate(data)

    def delete(self, badge_id: str) -> bool:
        """Delete a badge.

        Args:
            badge_id: Badge public UUID or internal ID

        Returns:
            True if deleted successfully

        Example:
            >>> client.badges.delete("123e4567-e89b-12d3-a456-426614174000")
        """
        self._delete(f"/badges/{badge_id}")
        return True

    def get_status(self, badge_id: str) -> dict[str, Any]:
        """Get the current status of a badge.

        Args:
            badge_id: Badge public UUID or internal ID

        Returns:
            Dict with badge_id, status (passing/failing/unknown), and badge_url

        Example:
            >>> status = client.badges.get_status("123e4567-e89b-12d3-a456-426614174000")
            >>> print(f"Status: {status['status']}")
        """
        response = self._get(f"/badges/{badge_id}/status")
        data: dict[str, Any] = response.get("data", {})
        return data
