"""Recommendations resource for AI-driven monitoring suggestions (TECH-772)."""

from __future__ import annotations

from typing import Any

from anomalyarmor.models import (
    CoverageRecommendationsResponse,
    FreshnessRecommendationsResponse,
    MetricsRecommendationsResponse,
    ThresholdsRecommendationsResponse,
)
from anomalyarmor.resources.base import BaseResource


class RecommendationsResource(BaseResource):
    """Resource for AI-driven monitoring recommendations.

    Provides intelligent suggestions for monitoring setup based on
    historical patterns, schema analysis, and alert data.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Get freshness recommendations
        >>> recs = client.recommendations.freshness("my-asset")
        >>> for rec in recs.recommendations:
        ...     print(f"{rec.table_path}: {rec.suggested_threshold_hours}h")
        >>>
        >>> # Get coverage analysis
        >>> coverage = client.recommendations.coverage("my-asset")
        >>> print(f"Coverage: {coverage.coverage_percentage:.1f}%")
    """

    def freshness(
        self,
        asset_id: str,
        *,
        min_confidence: float = 0.5,
        limit: int = 20,
        include_monitored: bool = False,
    ) -> FreshnessRecommendationsResponse:
        """Get freshness monitoring recommendations for an asset.

        Analyzes historical update patterns to suggest tables and thresholds
        for freshness monitoring.

        Args:
            asset_id: Asset UUID or qualified name (e.g., "snowflake.production")
            min_confidence: Minimum confidence threshold (0.0-1.0, default 0.5)
            limit: Maximum recommendations to return (default 20)
            include_monitored: Include already-monitored tables (default False)

        Returns:
            FreshnessRecommendationsResponse with recommendations list,
            tables_analyzed count, and tables_with_recommendations count

        Example:
            >>> recs = client.recommendations.freshness(
            ...     "my-asset",
            ...     min_confidence=0.7,
            ...     limit=10
            ... )
            >>> for rec in recs.recommendations:
            ...     print(f"{rec.table_path}:")
            ...     print(f"  Threshold: {rec.suggested_threshold_hours}h")
            ...     print(f"  Interval: {rec.suggested_check_interval}")
            ...     print(f"  Confidence: {rec.confidence:.0%}")
        """
        params = {
            "asset_id": asset_id,
            "min_confidence": min_confidence,
            "limit": limit,
            "include_monitored": include_monitored,
        }
        response = self._get("/recommendations/freshness", params=params)
        return FreshnessRecommendationsResponse.model_validate(response.get("data", {}))

    def metrics(
        self,
        asset_id: str,
        *,
        table_path: str | None = None,
        min_confidence: float = 0.5,
        limit: int = 50,
    ) -> MetricsRecommendationsResponse:
        """Get metric recommendations based on schema analysis.

        Analyzes column types and naming patterns to suggest quality checks.

        Args:
            asset_id: Asset UUID or qualified name
            table_path: Filter to specific table (optional)
            min_confidence: Minimum confidence threshold (0.0-1.0, default 0.5)
            limit: Maximum recommendations to return (default 50)

        Returns:
            MetricsRecommendationsResponse with recommendations list,
            columns_analyzed count, and columns_with_recommendations count

        Example:
            >>> recs = client.recommendations.metrics(
            ...     "my-asset",
            ...     table_path="public.orders"
            ... )
            >>> for rec in recs.recommendations:
            ...     print(f"{rec.column_name}: {rec.suggested_metric_type}")
        """
        params: dict[str, Any] = {
            "asset_id": asset_id,
            "min_confidence": min_confidence,
            "limit": limit,
        }
        if table_path:
            params["table_path"] = table_path
        response = self._get("/recommendations/metrics", params=params)
        return MetricsRecommendationsResponse.model_validate(response.get("data", {}))

    def coverage(
        self,
        asset_id: str,
        *,
        limit: int = 20,
    ) -> CoverageRecommendationsResponse:
        """Analyze monitoring coverage and identify gaps.

        Identifies high-value unmonitored tables prioritized by importance.

        Args:
            asset_id: Asset UUID or qualified name
            limit: Maximum recommendations to return (default 20)

        Returns:
            CoverageRecommendationsResponse with total_tables, monitored_tables,
            coverage_percentage, and prioritized recommendations

        Example:
            >>> coverage = client.recommendations.coverage("my-asset")
            >>> print(f"Coverage: {coverage.coverage_percentage:.1f}%")
            >>> print(f"Monitored: {coverage.monitored_tables}/{coverage.total_tables}")
            >>> for rec in coverage.recommendations[:5]:
            ...     print(f"  {rec.table_path}: {rec.importance_score:.0%}")
        """
        params = {
            "asset_id": asset_id,
            "limit": limit,
        }
        response = self._get("/recommendations/coverage", params=params)
        return CoverageRecommendationsResponse.model_validate(response.get("data", {}))

    def thresholds(
        self,
        asset_id: str,
        *,
        days: int = 30,
        limit: int = 10,
    ) -> ThresholdsRecommendationsResponse:
        """Get threshold adjustment suggestions to reduce alert fatigue.

        Analyzes historical alerts to suggest threshold tuning.

        Args:
            asset_id: Asset UUID or qualified name
            days: Historical window for analysis (default 30)
            limit: Maximum recommendations to return (default 10)

        Returns:
            ThresholdsRecommendationsResponse with recommendations list,
            monitored_items_analyzed count, and items_with_recommendations count

        Example:
            >>> suggestions = client.recommendations.thresholds("my-asset", days=30)
            >>> for rec in suggestions.recommendations:
            ...     print(f"{rec.table_path}:")
            ...     print(f"  Current: {rec.current_threshold}")
            ...     print(f"  Suggested: {rec.suggested_threshold} ({rec.direction})")
            ...     print(f"  Projected reduction: {rec.projected_reduction}")
        """
        params = {
            "asset_id": asset_id,
            "days": days,
            "limit": limit,
        }
        response = self._get("/recommendations/thresholds", params=params)
        return ThresholdsRecommendationsResponse.model_validate(response.get("data", {}))
