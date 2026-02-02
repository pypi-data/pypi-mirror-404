"""Validity resource for the Armor SDK (TECH-712)."""

from __future__ import annotations

import builtins
from typing import Any

from anomalyarmor.models import ValidityCheckResult, ValidityRule, ValiditySummary
from anomalyarmor.resources.base import BaseResource


class ValidityResource(BaseResource):
    """Resource for interacting with validity rules.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Get validity summary for an asset
        >>> summary = client.validity.summary("asset-uuid")
        >>> print(f"Failing rules: {summary.failing_rules}")
        >>>
        >>> # List all validity rules
        >>> rules = client.validity.list("asset-uuid")
        >>> for r in rules:
        ...     print(f"{r.rule_type} on {r.column_name}: {r.latest_status}")
        >>>
        >>> # Create a NOT NULL check
        >>> rule = client.validity.create(
        ...     "asset-uuid",
        ...     rule_type="NOT_NULL",
        ...     table_path="catalog.schema.table",
        ...     column_name="email",
        ...     severity="critical",
        ... )
    """

    def summary(self, asset_id: str) -> ValiditySummary:
        """Get validity summary for an asset.

        Args:
            asset_id: Asset UUID

        Returns:
            ValiditySummary with counts and status info
        """
        response = self._get(f"/validity/{asset_id}/summary")
        return ValiditySummary.model_validate(response.get("data", {}))

    def list(
        self,
        asset_id: str,
        rule_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[ValidityRule]:
        """List validity rules for an asset.

        Args:
            asset_id: Asset UUID
            rule_type: Filter by type (NOT_NULL, UNIQUE, REGEX, etc.)
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ValidityRule objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if rule_type is not None:
            params["rule_type"] = rule_type
        if is_active is not None:
            params["is_active"] = is_active

        response = self._get(f"/validity/{asset_id}", params=params)
        data = response.get("data", {}).get("items", [])
        return [ValidityRule.model_validate(item) for item in data]

    def get(self, asset_id: str, rule_id: str) -> ValidityRule:
        """Get validity rule details with recent results.

        Args:
            asset_id: Asset UUID
            rule_id: Rule UUID

        Returns:
            ValidityRule object

        Raises:
            NotFoundError: If rule is not found
        """
        response = self._get(f"/validity/{asset_id}/{rule_id}")
        return ValidityRule.model_validate(response.get("data", {}))

    def create(
        self,
        asset_id: str,
        rule_type: str,
        table_path: str,
        column_name: str | None = None,
        rule_config: dict[str, Any] | None = None,
        name: str | None = None,
        description: str | None = None,
        error_message: str | None = None,
        severity: str = "warning",
        alert_threshold_percent: float | None = None,
        treat_null_as_valid: bool = False,
        check_interval: str = "daily",
    ) -> ValidityRule:
        """Create a new validity rule.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            rule_type: Rule type (NOT_NULL, UNIQUE, REGEX, RANGE, etc.)
            table_path: Full table path (catalog.schema.table)
            column_name: Column name (required for column-level rules)
            rule_config: Rule-specific configuration (e.g., regex pattern)
            name: Human-readable rule name
            description: Rule description
            error_message: Custom error message for failures
            severity: Severity level (info, warning, critical)
            alert_threshold_percent: Alert when invalid % exceeds this
            treat_null_as_valid: Whether nulls pass the check
            check_interval: Check interval (hourly, daily, weekly)

        Returns:
            Created ValidityRule

        Raises:
            ValidationError: If required fields are missing
            PermissionError: If API key doesn't have write scope
        """
        payload: dict[str, Any] = {
            "rule_type": rule_type,
            "table_path": table_path,
            "severity": severity,
            "treat_null_as_valid": treat_null_as_valid,
            "check_interval": check_interval,
        }
        if column_name is not None:
            payload["column_name"] = column_name
        if rule_config is not None:
            payload["rule_config"] = rule_config
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if error_message is not None:
            payload["error_message"] = error_message
        if alert_threshold_percent is not None:
            payload["alert_threshold_percent"] = alert_threshold_percent

        response = self._post(f"/validity/{asset_id}", json=payload)
        return ValidityRule.model_validate(response.get("data", {}))

    def update(
        self,
        asset_id: str,
        rule_id: str,
        is_active: bool | None = None,
        severity: str | None = None,
        name: str | None = None,
        description: str | None = None,
        alert_threshold_percent: float | None = None,
        treat_null_as_valid: bool | None = None,
        check_interval: str | None = None,
    ) -> ValidityRule:
        """Update a validity rule.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            rule_id: Rule UUID
            is_active: Whether rule is active
            severity: Severity level
            name: Rule name
            description: Rule description
            alert_threshold_percent: Alert threshold percentage
            treat_null_as_valid: Whether nulls pass the check
            check_interval: Check interval

        Returns:
            Updated ValidityRule

        Raises:
            NotFoundError: If rule is not found
            PermissionError: If API key doesn't have write scope
        """
        payload: dict[str, Any] = {}
        if is_active is not None:
            payload["is_active"] = is_active
        if severity is not None:
            payload["severity"] = severity
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if alert_threshold_percent is not None:
            payload["alert_threshold_percent"] = alert_threshold_percent
        if treat_null_as_valid is not None:
            payload["treat_null_as_valid"] = treat_null_as_valid
        if check_interval is not None:
            payload["check_interval"] = check_interval

        response = self._patch(f"/validity/{asset_id}/{rule_id}", json=payload)
        return ValidityRule.model_validate(response.get("data", {}))

    def delete(self, asset_id: str, rule_id: str) -> None:
        """Delete a validity rule.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            rule_id: Rule UUID

        Raises:
            NotFoundError: If rule is not found
            PermissionError: If API key doesn't have write scope
        """
        self._delete(f"/validity/{asset_id}/{rule_id}")

    def check(
        self,
        asset_id: str,
        rule_id: str,
        sample_limit: int = 10,
    ) -> ValidityCheckResult:
        """Trigger an immediate validity check.

        Requires read-write or admin API key scope.

        Args:
            asset_id: Asset UUID
            rule_id: Rule UUID
            sample_limit: Maximum invalid samples to collect

        Returns:
            ValidityCheckResult with status and details

        Raises:
            NotFoundError: If rule is not found
            PermissionError: If API key doesn't have write scope
        """
        payload = {"sample_limit": sample_limit}
        response = self._post(f"/validity/{asset_id}/{rule_id}/check", json=payload)
        return ValidityCheckResult.model_validate(response.get("data", {}))

    def results(
        self,
        asset_id: str,
        rule_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> builtins.list[ValidityCheckResult]:
        """List check results for a validity rule.

        Args:
            asset_id: Asset UUID
            rule_id: Rule UUID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of ValidityCheckResult objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        response = self._get(f"/validity/{asset_id}/{rule_id}/results", params=params)
        data = response.get("data", {}).get("items", [])
        return [ValidityCheckResult.model_validate(item) for item in data]
