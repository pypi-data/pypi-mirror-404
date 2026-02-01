"""Tests for SDK resource classes."""

from unittest.mock import MagicMock

import pytest

from anomalyarmor.exceptions import StalenessError


class TestAssetsResource:
    """Tests for AssetsResource."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_list_assets(self, mock_client):
        """List assets makes correct API call."""
        from anomalyarmor.resources.assets import AssetsResource

        mock_client._request.return_value = {
            "data": {
                "data": [
                    {
                        "id": "1",
                        "qualified_name": "snowflake.prod.orders",
                        "name": "orders",
                        "asset_type": "table",
                    }
                ]
            },
        }

        resource = AssetsResource(mock_client)
        assets = resource.list()

        mock_client._request.assert_called_once_with(
            "GET", "/sdk/assets", params={"limit": 50, "offset": 0}
        )
        assert len(assets) == 1
        assert assets[0].qualified_name == "snowflake.prod.orders"

    def test_list_assets_with_filters(self, mock_client):
        """List assets passes filter parameters."""
        from anomalyarmor.resources.assets import AssetsResource

        mock_client._request.return_value = {"data": {"data": []}}

        resource = AssetsResource(mock_client)
        resource.list(source="snowflake", asset_type="table", limit=10)

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        call_params = call_args[1]["params"]
        assert call_params["source"] == "snowflake"
        assert call_params["asset_type"] == "table"
        assert call_params["limit"] == 10

    def test_get_asset(self, mock_client):
        """Get single asset by qualified name."""
        from anomalyarmor.resources.assets import AssetsResource

        mock_client._request.return_value = {
            "data": {
                "id": "1",
                "qualified_name": "snowflake.prod.orders",
                "name": "orders",
                "asset_type": "table",
            }
        }

        resource = AssetsResource(mock_client)
        asset = resource.get("snowflake.prod.orders")

        mock_client._request.assert_called_once_with(
            "GET", "/sdk/assets/snowflake.prod.orders", params=None
        )
        assert asset.qualified_name == "snowflake.prod.orders"


class TestFreshnessResource:
    """Tests for FreshnessResource."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_get_freshness(self, mock_client):
        """Get freshness status for asset."""
        from anomalyarmor.resources.freshness import FreshnessResource

        mock_client._request.return_value = {
            "data": {
                "asset_id": "1",
                "qualified_name": "snowflake.prod.orders",
                "status": "fresh",
                "is_stale": False,
                "checked_at": "2024-12-04T10:00:00Z",
            }
        }

        resource = FreshnessResource(mock_client)
        status = resource.get("snowflake.prod.orders")

        assert status.is_stale is False
        assert status.qualified_name == "snowflake.prod.orders"

    def test_require_fresh_passes_when_fresh(self, mock_client):
        """require_fresh doesn't raise when data is fresh."""
        from anomalyarmor.resources.freshness import FreshnessResource

        mock_client._request.return_value = {
            "data": {
                "asset_id": "1",
                "qualified_name": "snowflake.prod.orders",
                "status": "fresh",
                "is_stale": False,
                "hours_since_update": 2.0,
                "staleness_threshold_hours": 24,
                "checked_at": "2024-12-04T10:00:00Z",
            }
        }

        resource = FreshnessResource(mock_client)
        # Should not raise
        status = resource.require_fresh("snowflake.prod.orders")
        assert status.is_stale is False

    def test_require_fresh_raises_when_stale(self, mock_client):
        """require_fresh raises StalenessError when data is stale."""
        from anomalyarmor.resources.freshness import FreshnessResource

        mock_client._request.return_value = {
            "data": {
                "asset_id": "1",
                "qualified_name": "snowflake.prod.orders",
                "status": "stale",
                "is_stale": True,
                "hours_since_update": 30.0,
                "staleness_threshold_hours": 24,
                "checked_at": "2024-12-04T10:00:00Z",
            }
        }

        resource = FreshnessResource(mock_client)

        with pytest.raises(StalenessError) as exc_info:
            resource.require_fresh("snowflake.prod.orders")

        assert exc_info.value.asset == "snowflake.prod.orders"
        assert exc_info.value.threshold_hours == 24

    def test_refresh_triggers_check(self, mock_client):
        """Refresh triggers freshness check."""
        from anomalyarmor.resources.freshness import FreshnessResource

        mock_client._request.return_value = {"data": {"job_id": "job_123", "status": "pending"}}

        resource = FreshnessResource(mock_client)
        result = resource.refresh("snowflake.prod.orders")

        mock_client._request.assert_called_once_with(
            "POST",
            "/sdk/freshness/snowflake.prod.orders/refresh",
            json=None,
        )
        assert result["job_id"] == "job_123"

    def test_summary(self, mock_client):
        """Get freshness summary."""
        from anomalyarmor.resources.freshness import FreshnessResource

        mock_client._request.return_value = {
            "data": {
                "total_assets": 100,
                "fresh_count": 95,
                "stale_count": 3,
                "unknown_count": 1,
                "disabled_count": 1,
                "freshness_rate": 95.0,
            }
        }

        resource = FreshnessResource(mock_client)
        summary = resource.summary()

        assert summary.total_assets == 100
        assert summary.fresh_count == 95
        assert summary.stale_count == 3


class TestAlertsResource:
    """Tests for AlertsResource."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_list_alerts(self, mock_client):
        """List alerts makes correct API call."""
        from anomalyarmor.resources.alerts import AlertsResource

        mock_client._request.return_value = {
            "data": {
                "data": [
                    {
                        "id": "alert_1",
                        "message": "Test alert",
                        "severity": "warning",
                        "status": "triggered",
                        "triggered_at": "2024-12-04T10:00:00Z",
                    }
                ]
            },
        }

        resource = AlertsResource(mock_client)
        alerts = resource.list()

        assert len(alerts) == 1
        assert alerts[0].severity == "warning"

    def test_list_alerts_with_status_filter(self, mock_client):
        """List alerts filters by status."""
        from anomalyarmor.resources.alerts import AlertsResource

        mock_client._request.return_value = {"data": {"data": []}}

        resource = AlertsResource(mock_client)
        resource.list(status="triggered")

        call_args = mock_client._request.call_args
        call_params = call_args[1]["params"]
        assert call_params["status"] == "triggered"

    def test_summary(self, mock_client):
        """Get alerts summary."""
        from anomalyarmor.resources.alerts import AlertsResource

        mock_client._request.return_value = {
            "data": {
                "total_rules": 50,
                "active_rules": 45,
                "recent_alerts": 10,
                "unresolved_alerts": 3,
            }
        }

        resource = AlertsResource(mock_client)
        summary = resource.summary()

        assert summary.total_rules == 50
        assert summary.active_rules == 45


class TestLineageResource:
    """Tests for LineageResource."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_get_lineage(self, mock_client):
        """Get lineage for asset."""
        from anomalyarmor.resources.lineage import LineageResource

        mock_client._request.return_value = {
            "data": {
                "root": {
                    "id": "1",
                    "qualified_name": "snowflake.prod.orders",
                    "name": "orders",
                },
                "upstream": [{"id": "2", "qualified_name": "raw.orders", "name": "orders"}],
                "downstream": [{"id": "3", "qualified_name": "mart.orders", "name": "orders"}],
                "edges": [],
            }
        }

        resource = LineageResource(mock_client)
        lineage = resource.get("snowflake.prod.orders")

        assert len(lineage.upstream) == 1
        assert len(lineage.downstream) == 1

    def test_get_lineage_with_depth(self, mock_client):
        """Get lineage with custom depth."""
        from anomalyarmor.resources.lineage import LineageResource

        mock_client._request.return_value = {
            "data": {
                "root": {
                    "id": "1",
                    "qualified_name": "snowflake.prod.orders",
                    "name": "orders",
                },
                "upstream": [],
                "downstream": [],
                "edges": [],
            }
        }

        resource = LineageResource(mock_client)
        resource.get("snowflake.prod.orders", depth=3)

        call_args = mock_client._request.call_args
        call_params = call_args[1]["params"]
        assert call_params["depth"] == 3


class TestSchemaResource:
    """Tests for SchemaResource."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_summary(self, mock_client):
        """Get schema summary."""
        from anomalyarmor.resources.schema import SchemaResource

        mock_client._request.return_value = {
            "data": {
                "total_changes": 100,
                "unacknowledged": 5,
                "critical_count": 2,
                "warning_count": 10,
                "info_count": 88,
            }
        }

        resource = SchemaResource(mock_client)
        summary = resource.summary()

        assert summary.total_changes == 100
        assert summary.unacknowledged == 5

    def test_list_changes(self, mock_client):
        """List schema changes."""
        from anomalyarmor.resources.schema import SchemaResource

        mock_client._request.return_value = {
            "data": {
                "data": [
                    {
                        "id": "change_1",
                        "asset_id": "asset_1",
                        "qualified_name": "snowflake.prod.orders",
                        "change_type": "column_added",
                        "severity": "info",
                        "column_name": "new_col",
                        "detected_at": "2024-12-04T10:00:00Z",
                    }
                ]
            },
        }

        resource = SchemaResource(mock_client)
        changes = resource.changes()

        assert len(changes) == 1
        assert changes[0].change_type == "column_added"


class TestMetricsResource:
    """Tests for MetricsResource (TECH-712)."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_summary(self, mock_client):
        """Get metrics summary for asset."""
        from anomalyarmor.resources.metrics import MetricsResource

        mock_client._request.return_value = {
            "data": {
                "total_metrics": 15,
                "active_metrics": 10,
                "total_checks": 5,
                "passing": 3,
                "failing": 1,
                "warning": 1,
                "error": 0,
                "health_percentage": 75.0,
            }
        }

        resource = MetricsResource(mock_client)
        summary = resource.summary("asset-uuid")

        mock_client._request.assert_called_once_with(
            "GET", "/sdk/metrics/asset-uuid/summary", params=None
        )
        assert summary.active_metrics == 10
        assert summary.total_metrics == 15
        assert summary.passing == 3

    def test_list_metrics(self, mock_client):
        """List metrics for asset."""
        from anomalyarmor.resources.metrics import MetricsResource

        mock_client._request.return_value = {
            "data": {
                "items": [
                    {
                        "id": "metric-uuid-1",
                        "internal_id": 1,
                        "asset_id": 1,
                        "metric_type": "row_count",
                        "table_path": "catalog.schema.orders",
                        "is_active": True,
                    }
                ]
            }
        }

        resource = MetricsResource(mock_client)
        metrics = resource.list("asset-uuid")

        assert len(metrics) == 1
        assert metrics[0].metric_type == "row_count"
        assert metrics[0].id == "metric-uuid-1"

    def test_list_metrics_with_filters(self, mock_client):
        """List metrics with filters."""
        from anomalyarmor.resources.metrics import MetricsResource

        mock_client._request.return_value = {"data": {"items": []}}

        resource = MetricsResource(mock_client)
        resource.list("asset-uuid", metric_type="null_percent", is_active=True)

        call_args = mock_client._request.call_args
        call_params = call_args[1]["params"]
        assert call_params["metric_type"] == "null_percent"
        assert call_params["is_active"] is True

    def test_create_metric(self, mock_client):
        """Create a new metric."""
        from anomalyarmor.resources.metrics import MetricsResource

        mock_client._request.return_value = {
            "data": {
                "id": "metric-uuid-2",
                "internal_id": 2,
                "asset_id": 1,
                "metric_type": "null_percent",
                "table_path": "catalog.schema.orders",
                "column_name": "email",
                "is_active": True,
            }
        }

        resource = MetricsResource(mock_client)
        metric = resource.create(
            "asset-uuid",
            metric_type="null_percent",
            table_path="catalog.schema.orders",
            column_name="email",
        )

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "POST"
        assert metric.metric_type == "null_percent"
        assert metric.column_name == "email"
        assert metric.id == "metric-uuid-2"

    def test_capture_metric(self, mock_client):
        """Trigger metric capture."""
        from anomalyarmor.resources.metrics import MetricsResource

        mock_client._request.return_value = {"data": {"snapshot_count": 1, "snapshots": []}}

        resource = MetricsResource(mock_client)
        result = resource.capture("asset-uuid", "metric-uuid")

        mock_client._request.assert_called_once_with(
            "POST", "/sdk/metrics/asset-uuid/metric-uuid/capture", json=None
        )
        assert result["snapshot_count"] == 1


class TestValidityResource:
    """Tests for ValidityResource (TECH-712)."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_summary(self, mock_client):
        """Get validity summary for asset."""
        from anomalyarmor.resources.validity import ValidityResource

        mock_client._request.return_value = {
            "data": {
                "total_rules": 20,
                "passing": 15,
                "failing": 3,
                "error": 2,
            }
        }

        resource = ValidityResource(mock_client)
        summary = resource.summary("asset-uuid")

        mock_client._request.assert_called_once_with(
            "GET", "/sdk/validity/asset-uuid/summary", params=None
        )
        assert summary.total_rules == 20
        assert summary.failing == 3

    def test_list_rules(self, mock_client):
        """List validity rules for asset."""
        from anomalyarmor.resources.validity import ValidityResource

        mock_client._request.return_value = {
            "data": {
                "items": [
                    {
                        "id": 1,
                        "uuid": "rule-uuid-1",
                        "rule_type": "NOT_NULL",
                        "table_path": "catalog.schema.orders",
                        "column_name": "order_id",
                        "is_active": True,
                        "severity": "critical",
                    }
                ]
            }
        }

        resource = ValidityResource(mock_client)
        rules = resource.list("asset-uuid")

        assert len(rules) == 1
        assert rules[0].rule_type == "NOT_NULL"

    def test_create_rule(self, mock_client):
        """Create a new validity rule."""
        from anomalyarmor.resources.validity import ValidityResource

        mock_client._request.return_value = {
            "data": {
                "id": 2,
                "uuid": "rule-uuid-2",
                "rule_type": "NOT_NULL",
                "table_path": "catalog.schema.orders",
                "column_name": "email",
                "is_active": True,
                "severity": "critical",
            }
        }

        resource = ValidityResource(mock_client)
        rule = resource.create(
            "asset-uuid",
            rule_type="NOT_NULL",
            table_path="catalog.schema.orders",
            column_name="email",
            severity="critical",
        )

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "POST"
        assert rule.rule_type == "NOT_NULL"
        assert rule.severity == "critical"

    def test_check_validity(self, mock_client):
        """Trigger validity check."""
        from anomalyarmor.resources.validity import ValidityResource

        mock_client._request.return_value = {
            "data": {
                "id": 1,
                "validity_rule_id": 1,
                "status": "PASS",
                "total_rows": 1000,
                "invalid_count": 0,
                "invalid_percent": 0.0,
                "checked_at": "2025-01-08T10:00:00Z",
            }
        }

        resource = ValidityResource(mock_client)
        result = resource.check("asset-uuid", "rule-uuid")

        assert result.status == "PASS"
        assert result.invalid_count == 0


class TestReferentialResource:
    """Tests for ReferentialResource (TECH-712)."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        return client

    def test_list_checks(self, mock_client):
        """List referential checks for asset."""
        from anomalyarmor.resources.referential import ReferentialResource

        mock_client._request.return_value = {
            "data": {
                "items": [
                    {
                        "id": "check-uuid-1",
                        "internal_id": 1,
                        "asset_id": 1,
                        "child_table_path": "catalog.schema.orders",
                        "child_column_name": "customer_id",
                        "parent_table_path": "catalog.schema.customers",
                        "parent_column_name": "id",
                        "is_active": True,
                        "capture_interval": "daily",
                    }
                ]
            }
        }

        resource = ReferentialResource(mock_client)
        checks = resource.list("asset-uuid")

        assert len(checks) == 1
        assert checks[0].child_column_name == "customer_id"

    def test_create_check(self, mock_client):
        """Create a new referential check."""
        from anomalyarmor.resources.referential import ReferentialResource

        mock_client._request.return_value = {
            "data": {
                "id": "check-uuid-2",
                "internal_id": 2,
                "asset_id": 1,
                "child_table_path": "catalog.schema.orders",
                "child_column_name": "customer_id",
                "parent_table_path": "catalog.schema.customers",
                "parent_column_name": "id",
                "is_active": True,
                "capture_interval": "daily",
            }
        }

        resource = ReferentialResource(mock_client)
        check = resource.create(
            "asset-uuid",
            child_table_path="catalog.schema.orders",
            child_column_name="customer_id",
            parent_table_path="catalog.schema.customers",
            parent_column_name="id",
        )

        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "POST"
        assert check.child_table_path == "catalog.schema.orders"

    def test_execute_check(self, mock_client):
        """Execute a referential check."""
        from anomalyarmor.resources.referential import ReferentialResource

        mock_client._request.return_value = {
            "data": {
                "id": 1,
                "referential_check_id": 1,
                "status": "PASS",
                "orphan_count": 0,
                "orphan_percent": 0.0,
                "total_child_rows": 5000,
                "checked_at": "2025-01-08T10:00:00Z",
            }
        }

        resource = ReferentialResource(mock_client)
        result = resource.execute("asset-uuid", "check-uuid")

        mock_client._request.assert_called_once_with(
            "POST", "/sdk/referential/asset-uuid/check-uuid/execute", json=None
        )
        assert result.status == "PASS"
        assert result.orphan_count == 0

    def test_get_results(self, mock_client):
        """Get historical results for a check."""
        from anomalyarmor.resources.referential import ReferentialResource

        mock_client._request.return_value = {
            "data": {
                "items": [
                    {
                        "id": 1,
                        "referential_check_id": 1,
                        "status": "PASS",
                        "orphan_count": 0,
                        "orphan_percent": 0.0,
                        "total_child_rows": 5000,
                        "checked_at": "2025-01-08T10:00:00Z",
                    },
                    {
                        "id": 2,
                        "referential_check_id": 1,
                        "status": "FAIL",
                        "orphan_count": 5,
                        "orphan_percent": 0.1,
                        "total_child_rows": 5000,
                        "checked_at": "2025-01-07T10:00:00Z",
                    },
                ]
            }
        }

        resource = ReferentialResource(mock_client)
        results = resource.results("asset-uuid", "check-uuid")

        assert len(results) == 2
        assert results[0].status == "PASS"
        assert results[1].orphan_count == 5
