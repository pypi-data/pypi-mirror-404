"""Health resource for checking overall data health."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anomalyarmor.models import HealthSummary
from anomalyarmor.resources.base import BaseResource

if TYPE_CHECKING:
    pass


class HealthResource(BaseResource):
    """Resource for checking overall data health.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Check overall health
        >>> health = client.health.summary()
        >>> print(f"Status: {health.overall_status}")
        >>> if health.overall_status != "healthy":
        ...     for item in health.needs_attention:
        ...         print(f"  - {item.title}")
    """

    def summary(self) -> HealthSummary:
        """Get unified health summary across all monitoring dimensions.

        Returns a single response aggregating alerts, freshness, and schema
        drift status. Designed for AI skills to answer "is my data healthy?"

        Returns:
            HealthSummary with overall_status, component summaries, and
            items needing attention

        Example:
            >>> health = client.health.summary()
            >>> if health.overall_status == "critical":
            ...     print(f"Critical! {health.alerts.unresolved_alerts} unresolved alerts")
            >>> elif health.overall_status == "warning":
            ...     print(f"Warning: {health.freshness.stale_count} stale tables")
            >>> else:
            ...     print("All systems healthy!")
        """
        response = self._get("/health/summary")
        return HealthSummary.model_validate(response.get("data", {}))
