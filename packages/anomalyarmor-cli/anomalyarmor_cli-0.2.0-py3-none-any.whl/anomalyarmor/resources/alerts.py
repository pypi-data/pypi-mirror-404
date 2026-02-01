"""Alerts resource for the Armor SDK."""

from __future__ import annotations

import builtins
from datetime import datetime
from typing import Any

from anomalyarmor.models import (
    Alert,
    AlertDestination,
    AlertPreviewResponse,
    AlertRule,
    AlertSummary,
)
from anomalyarmor.resources.base import BaseResource


class AlertsResource(BaseResource):
    """Resource for interacting with alerts.

    Example:
        >>> from anomalyarmor import Client
        >>> client = Client()
        >>>
        >>> # Get summary
        >>> summary = client.alerts.summary()
        >>> if summary.unresolved_alerts > 0:
        ...     print(f"You have {summary.unresolved_alerts} unresolved alerts")
        >>>
        >>> # List critical alerts
        >>> critical = client.alerts.list(severity="critical")
        >>>
        >>> # List alert rules
        >>> rules = client.alerts.rules()
        >>>
        >>> # Create destination and rule (TECH-646)
        >>> dest = client.alerts.create_destination(
        ...     name="Slack #alerts",
        ...     destination_type="slack",
        ...     config={"webhook_url": "https://..."}
        ... )
        >>> rule = client.alerts.create_rule(
        ...     name="Critical Alerts",
        ...     destination_ids=[dest.id],
        ...     severities=["critical"]
        ... )
    """

    def summary(self) -> AlertSummary:
        """Get a summary of alerts and rules.

        Returns:
            AlertSummary with counts
        """
        response = self._get("/alerts/summary")
        return AlertSummary.model_validate(response.get("data", {}))

    def list(
        self,
        status: str | None = None,
        severity: str | None = None,
        asset_id: str | None = None,
        from_date: datetime | str | None = None,
        to_date: datetime | str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[Alert]:
        """List alerts with optional filters.

        Args:
            status: Filter by status ("triggered", "acknowledged", "resolved")
            severity: Filter by severity ("info", "warning", "critical")
            asset_id: Filter by asset UUID or qualified name
            from_date: Start of date range (ISO string or datetime)
            to_date: End of date range (ISO string or datetime)
            limit: Maximum number of results (default 50, max 100)
            offset: Number of results to skip

        Returns:
            List of Alert objects

        Example:
            >>> from datetime import datetime, timedelta
            >>>
            >>> # Get alerts from yesterday
            >>> yesterday = datetime.now() - timedelta(days=1)
            >>> alerts = client.alerts.list(from_date=yesterday)
            >>>
            >>> # Get alerts for specific date range
            >>> alerts = client.alerts.list(
            ...     from_date="2026-01-01T00:00:00Z",
            ...     to_date="2026-01-31T23:59:59Z",
            ...     severity="critical"
            ... )
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        if asset_id:
            params["asset_id"] = asset_id
        if from_date:
            params["from_date"] = (
                from_date.isoformat() if isinstance(from_date, datetime) else from_date
            )
        if to_date:
            params["to_date"] = to_date.isoformat() if isinstance(to_date, datetime) else to_date

        response = self._get("/alerts", params=params)
        data = response.get("data", {}).get("data", [])
        return [Alert.model_validate(item) for item in data]

    def rules(
        self,
        enabled_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[AlertRule]:
        """List alert rules.

        Args:
            enabled_only: Only return enabled rules
            limit: Maximum number of results (default 50, max 100)
            offset: Number of results to skip

        Returns:
            List of AlertRule objects
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if enabled_only:
            params["enabled_only"] = True

        response = self._get("/alerts/rules", params=params)
        data = response.get("data", {}).get("data", [])
        return [AlertRule.model_validate(item) for item in data]

    # =========================================================================
    # TECH-646: Alert Rules CRUD
    # =========================================================================

    def create_rule(
        self,
        name: str,
        destination_ids: builtins.list[str],
        description: str | None = None,
        is_active: bool = True,
        event_types: builtins.list[str] | None = None,
        severities: builtins.list[str] | None = None,
        tag_filter_mode: str | None = None,
        tag_filter_tags: builtins.list[str] | None = None,
    ) -> AlertRule:
        """Create a new alert rule.

        Args:
            name: Rule name
            destination_ids: List of destination UUIDs to send alerts to
            description: Optional rule description
            is_active: Whether the rule is active (default True)
            event_types: Event types to alert on (e.g., ["freshness_alert", "schema_drift"])
            severities: Severity levels to alert on (e.g., ["critical", "warning"])
            tag_filter_mode: Tag filter mode ("any" or "all")
            tag_filter_tags: List of tags to filter by

        Returns:
            Created AlertRule object

        Example:
            >>> rule = client.alerts.create_rule(
            ...     name="Critical Freshness Alerts",
            ...     destination_ids=["dest-uuid-1"],
            ...     event_types=["freshness_alert"],
            ...     severities=["critical"]
            ... )
            >>> print(f"Created rule: {rule.id}")
        """
        payload = {
            "name": name,
            "destination_ids": destination_ids,
            "is_active": is_active,
        }
        if description:
            payload["description"] = description
        if event_types:
            payload["event_types"] = event_types
        if severities:
            payload["severities"] = severities
        if tag_filter_mode:
            payload["tag_filter_mode"] = tag_filter_mode
        if tag_filter_tags:
            payload["tag_filter_tags"] = tag_filter_tags

        response = self._post("/alerts/rules", json=payload)
        return AlertRule.model_validate(response.get("data", {}))

    def get_rule(self, rule_id: str) -> AlertRule:
        """Get a specific alert rule by ID.

        Args:
            rule_id: Rule public UUID

        Returns:
            AlertRule object

        Example:
            >>> rule = client.alerts.get_rule("rule-uuid")
            >>> print(f"Rule: {rule.name}, Active: {rule.is_active}")
        """
        response = self._get(f"/alerts/rules/{rule_id}")
        return AlertRule.model_validate(response.get("data", {}))

    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule.

        Args:
            rule_id: Rule public UUID

        Returns:
            True if deleted successfully

        Example:
            >>> client.alerts.delete_rule("rule-uuid")
        """
        self._delete(f"/alerts/rules/{rule_id}")
        return True

    # =========================================================================
    # TECH-646: Alert Destinations CRUD
    # =========================================================================

    def list_destinations(
        self,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> builtins.list[AlertDestination]:
        """List alert destinations.

        Args:
            active_only: Only return active destinations
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AlertDestination objects

        Example:
            >>> destinations = client.alerts.list_destinations()
            >>> for dest in destinations:
            ...     print(f"{dest.name} ({dest.destination_type})")
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if active_only:
            params["active_only"] = True

        response = self._get("/alerts/destinations", params=params)
        data = response.get("data", {}).get("destinations", [])
        return [AlertDestination.model_validate(item) for item in data]

    def create_destination(
        self,
        name: str,
        destination_type: str,
        config: dict[str, Any],
    ) -> AlertDestination:
        """Create a new alert destination.

        Args:
            name: Destination name
            destination_type: Type: email, slack, webhook, teams, pagerduty
            config: Configuration dict (varies by type)
                - email: {"email": "user@example.com"} or {"recipients": ["email1", "email2"]}
                - slack: {"webhook_url": "https://hooks.slack.com/..."}
                - webhook: {"url": "https://...", "headers": {...}}
                - teams: {"webhook_url": "https://..."}
                - pagerduty: {"api_token": "...", "routing_key": "..."}

        Returns:
            Created AlertDestination

        Example:
            >>> dest = client.alerts.create_destination(
            ...     name="Slack #alerts",
            ...     destination_type="slack",
            ...     config={"webhook_url": "https://hooks.slack.com/..."}
            ... )
            >>> print(f"Created: {dest.id}")
        """
        payload = {
            "name": name,
            "destination_type": destination_type,
            "config": config,
        }
        response = self._post("/alerts/destinations", json=payload)
        return AlertDestination.model_validate(response.get("data", {}))

    def get_destination(self, destination_id: str) -> AlertDestination:
        """Get a specific alert destination by ID.

        Args:
            destination_id: Destination public UUID

        Returns:
            AlertDestination object

        Example:
            >>> dest = client.alerts.get_destination("dest-uuid")
            >>> print(f"{dest.name}: {dest.destination_type}")
        """
        response = self._get(f"/alerts/destinations/{destination_id}")
        return AlertDestination.model_validate(response.get("data", {}))

    def delete_destination(self, destination_id: str) -> bool:
        """Delete an alert destination.

        Args:
            destination_id: Destination public UUID

        Returns:
            True if deleted successfully

        Example:
            >>> client.alerts.delete_destination("dest-uuid")
        """
        self._delete(f"/alerts/destinations/{destination_id}")
        return True

    # =========================================================================
    # TECH-767: Alert Resolution APIs
    # =========================================================================

    def acknowledge(self, alert_id: str, notes: str | None = None) -> dict[str, Any]:
        """Acknowledge an alert - mark as seen/being worked on.

        Args:
            alert_id: Alert public UUID
            notes: Optional notes about the acknowledgment

        Returns:
            Dict with alert id and new status

        Example:
            >>> result = client.alerts.acknowledge("alert-uuid", notes="Looking into this")
            >>> print(f"Alert {result['id']} is now {result['status']}")
        """
        payload: dict[str, Any] = {}
        if notes:
            payload["notes"] = notes
        response = self._post(f"/alerts/{alert_id}/acknowledge", json=payload)
        data: dict[str, Any] = response.get("data", {})
        return data

    def resolve(self, alert_id: str, notes: str | None = None) -> dict[str, Any]:
        """Resolve an alert - mark as fixed.

        Args:
            alert_id: Alert public UUID
            notes: Optional resolution notes

        Returns:
            Dict with alert id and new status

        Example:
            >>> result = client.alerts.resolve("alert-uuid", notes="Fixed the pipeline")
            >>> print(f"Alert {result['id']} is now {result['status']}")
        """
        payload: dict[str, Any] = {}
        if notes:
            payload["notes"] = notes
        response = self._post(f"/alerts/{alert_id}/resolve", json=payload)
        data: dict[str, Any] = response.get("data", {})
        return data

    def dismiss(self, alert_id: str, notes: str | None = None) -> dict[str, Any]:
        """Dismiss an alert - mark as false positive or expected behavior.

        Args:
            alert_id: Alert public UUID
            notes: Optional notes explaining the dismissal

        Returns:
            Dict with alert id and new status

        Example:
            >>> result = client.alerts.dismiss("alert-uuid", notes="Expected maintenance")
            >>> print(f"Alert {result['id']} is now {result['status']}")
        """
        payload: dict[str, Any] = {}
        if notes:
            payload["notes"] = notes
        response = self._post(f"/alerts/{alert_id}/dismiss", json=payload)
        data: dict[str, Any] = response.get("data", {})
        return data

    def snooze(
        self, alert_id: str, duration_hours: int, notes: str | None = None
    ) -> dict[str, Any]:
        """Snooze an alert for a specified duration.

        Args:
            alert_id: Alert public UUID
            duration_hours: Hours to snooze (1-720, max 30 days)
            notes: Optional notes

        Returns:
            Dict with alert id, status, and snoozed_until timestamp

        Example:
            >>> # Snooze for 24 hours
            >>> result = client.alerts.snooze("alert-uuid", duration_hours=24)
            >>> print(f"Snoozed until {result['snoozed_until']}")
        """
        payload: dict[str, Any] = {"duration_hours": duration_hours}
        if notes:
            payload["notes"] = notes
        response = self._post(f"/alerts/{alert_id}/snooze", json=payload)
        data: dict[str, Any] = response.get("data", {})
        return data

    def history(self, alert_id: str) -> builtins.list[dict[str, Any]]:
        """Get resolution history for an alert.

        Args:
            alert_id: Alert public UUID

        Returns:
            List of history entries (action, timestamp, user_id, notes)

        Example:
            >>> history = client.alerts.history("alert-uuid")
            >>> for entry in history:
            ...     print(f"{entry['action']} at {entry['timestamp']}")
        """
        response = self._get(f"/alerts/{alert_id}/history")
        history: list[dict[str, Any]] = response.get("data", {}).get("history", [])
        return history

    def trends(self, period: str = "7d") -> dict[str, Any]:
        """Get alert volume trends over time.

        Args:
            period: Time period - "24h", "7d", "30d", or "90d" (default "7d")

        Returns:
            Dict with period and trends data

        Example:
            >>> trends = client.alerts.trends(period="30d")
            >>> print(f"Trends for {trends['period']}: {len(trends['trends'])} data points")
        """
        response = self._get("/alerts/trends", params={"period": period})
        data: dict[str, Any] = response.get("data", {})
        return data

    # =========================================================================
    # TECH-771: Alert Preview APIs
    # =========================================================================

    def preview(
        self,
        rule_id: str | None = None,
        event_types: builtins.list[str] | None = None,
        severities: builtins.list[str] | None = None,
        lookback_days: int = 7,
    ) -> AlertPreviewResponse:
        """Preview what alerts would have been sent with a rule configuration.

        Simulates alert rule matching over historical alerts to help understand
        alert volume before enabling a rule.

        Args:
            rule_id: Existing rule UUID to preview (optional)
            event_types: Event types to match (if not using rule_id)
            severities: Severities to match (if not using rule_id)
            lookback_days: Days of history to analyze (default 7)

        Returns:
            AlertPreviewResponse with alert volume simulation

        Example:
            >>> # Preview an existing rule
            >>> result = client.alerts.preview(rule_id="rule-uuid")
            >>> print(f"Matching alerts: {result.alerts_would_match}")
            >>>
            >>> # Preview a hypothetical rule
            >>> result = client.alerts.preview(
            ...     event_types=["freshness_alert"],
            ...     severities=["critical"],
            ...     lookback_days=30,
            ... )
            >>> print(f"By severity: {result.alerts_by_severity}")
        """
        payload: dict[str, Any] = {
            "lookback_days": lookback_days,
        }
        if rule_id is not None:
            payload["rule_id"] = rule_id
        if event_types is not None:
            payload["event_types"] = event_types
        if severities is not None:
            payload["severities"] = severities
        response = self._post("/alerts/preview", json=payload)
        return AlertPreviewResponse.model_validate(response.get("data", {}))
