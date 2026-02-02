"""Intelligence resource for the Armor SDK (TECH-646)."""

from __future__ import annotations

from anomalyarmor.models import IntelligenceAnswer, IntelligenceGenerateResult
from anomalyarmor.resources.base import BaseResource


class IntelligenceResource(BaseResource):
    """Resource for interacting with Intelligence Q&A.

    Provides programmatic access to AnomalyArmor's intelligence Q&A system
    for querying database metadata and discovering relationships.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Ask about upstream dependencies
        >>> answer = client.intelligence.ask(
        ...     asset="postgresql.analytics",
        ...     question="list upstream tables for public.orders"
        ... )
        >>> print(answer.answer)
        >>>
        >>> # Get structured response for automation
        >>> answer = client.intelligence.ask(
        ...     asset="postgresql.analytics",
        ...     question="list upstream tables for public.orders as JSON array"
        ... )
        >>> import json
        >>> tables = json.loads(answer.answer)
    """

    def ask(
        self,
        asset: str,
        question: str,
        include_related_assets: bool = False,
    ) -> IntelligenceAnswer:
        """Ask a question about an asset using Intelligence Q&A.

        Uses the generated markdown knowledge base as context for accurate
        and comprehensive answers about database structure, lineage, and metadata.

        Args:
            asset: Asset identifier. Can be either:
                   - Public UUID (e.g., "123e4567-e89b-12d3-a456-426614174000")
                   - Qualified name (e.g., "postgresql.analytics")
            question: Natural language question to ask (3-2000 chars).
                      For automation, ask for JSON format in your question.
            include_related_assets: Include related assets in context for
                                    cross-database queries.

        Returns:
            IntelligenceAnswer with the generated answer, confidence level,
            sources used, and token usage.

        Raises:
            NotFoundError: If the asset is not found
            ValidationError: If the question is invalid
            ArmorError: For other API errors

        Example:
            >>> # Simple question
            >>> answer = client.intelligence.ask(
            ...     asset="postgresql.analytics",
            ...     question="What tables contain customer data?"
            ... )
            >>> print(f"Answer: {answer.answer}")
            >>> print(f"Confidence: {answer.confidence}")

            >>> # Question for automation (request JSON)
            >>> answer = client.intelligence.ask(
            ...     asset="postgresql.analytics",
            ...     question="list upstream tables for public.orders as JSON array"
            ... )
            >>> import json
            >>> upstream_tables = json.loads(answer.answer)
            >>> print(f"Upstream tables: {upstream_tables}")
        """
        response = self._post(
            "/intelligence/ask",
            json={
                "asset_id": asset,
                "question": question,
                "include_related_assets": include_related_assets,
            },
        )
        data = response.get("data", {})
        return IntelligenceAnswer.model_validate(data)

    def generate(
        self,
        asset: str,
        include_schemas: str | None = None,
        force_refresh: bool = False,
    ) -> IntelligenceGenerateResult:
        """Trigger intelligence generation for an asset.

        Generates AI analysis of the asset's schema including descriptions,
        summaries, and a knowledge base for Q&A.

        Args:
            asset: Asset identifier. Can be:
                   - Public UUID (e.g., "123e4567-e89b-12d3-a456-426614174000")
                   - Short UUID (e.g., "123e4567")
                   - Asset name (e.g., "BalloonBazaar")
            include_schemas: Comma-separated list of schemas to analyze.
                            If None, all schemas are analyzed.
            force_refresh: Force regeneration even if intelligence exists.

        Returns:
            IntelligenceGenerateResult with job_id for tracking progress.

        Raises:
            NotFoundError: If the asset is not found
            ArmorError: For other API errors

        Example:
            >>> result = client.intelligence.generate(
            ...     asset="postgresql.analytics"
            ... )
            >>> print(f"Job started: {result.job_id}")
        """
        response = self._post(
            "/intelligence/generate",
            json={
                "asset_id": asset,
                "include_schemas": include_schemas,
                "force_refresh": force_refresh,
            },
        )
        data = response.get("data", {})
        return IntelligenceGenerateResult.model_validate(data)
