"""Data models for the Armor SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Asset(BaseModel):
    """An asset (table, view, etc.) in AnomalyArmor."""

    id: str = Field(..., description="Public UUID of the asset")
    qualified_name: str = Field(..., description="Fully qualified name")
    name: str = Field(..., description="Display name")
    asset_type: str = Field(default="table", description="Type: table, view, etc.")
    source_type: str | None = Field(None, description="Database type")
    is_active: bool = Field(default=True, description="Whether monitoring is active")
    created_at: datetime | None = Field(None, description="Creation time")
    updated_at: datetime | None = Field(None, description="Last update time")

    # Extended fields (only in detail view)
    database_name: str | None = Field(None, description="Database name")
    schema_name: str | None = Field(None, description="Schema name")
    table_name: str | None = Field(None, description="Table name")
    description: str | None = Field(None, description="Asset description")
    row_count: int | None = Field(None, description="Approximate row count")
    size_bytes: int | None = Field(None, description="Storage size")


class FreshnessStatus(BaseModel):
    """Freshness status for an asset."""

    asset_id: str = Field(..., description="Asset public UUID")
    qualified_name: str = Field(..., description="Asset qualified name")
    status: str = Field(..., description="Status: fresh, stale, unknown, disabled")
    last_update_time: datetime | None = Field(None, description="Last update time")
    staleness_threshold_hours: int | None = Field(None, description="Threshold hours")
    hours_since_update: float | None = Field(None, description="Hours since update")
    is_stale: bool = Field(..., description="Whether asset is stale")
    checked_at: datetime = Field(..., description="Check timestamp")


class FreshnessSummary(BaseModel):
    """Summary of freshness across assets."""

    total_assets: int = Field(..., description="Total monitored assets")
    fresh_count: int = Field(..., description="Fresh assets")
    stale_count: int = Field(..., description="Stale assets")
    unknown_count: int = Field(..., description="Unknown freshness")
    disabled_count: int = Field(..., description="Disabled monitoring")
    freshness_rate: float = Field(..., description="Percentage fresh")


class SchemaChange(BaseModel):
    """A schema change detected on an asset."""

    id: str = Field(..., description="Change ID")
    asset_id: str = Field(..., description="Asset public UUID")
    qualified_name: str = Field(..., description="Asset qualified name")
    change_type: str = Field(..., description="Type of change")
    severity: str = Field(..., description="Severity level")
    column_name: str | None = Field(None, description="Affected column")
    old_value: str | None = Field(None, description="Previous value")
    new_value: str | None = Field(None, description="New value")
    detected_at: datetime = Field(..., description="Detection time")
    acknowledged: bool = Field(default=False, description="Acknowledged status")


class SchemaSummary(BaseModel):
    """Summary of schema changes."""

    total_changes: int = Field(..., description="Total changes")
    unacknowledged: int = Field(..., description="Unacknowledged")
    critical_count: int = Field(..., description="Critical severity")
    warning_count: int = Field(..., description="Warning severity")
    info_count: int = Field(..., description="Info severity")
    last_check: datetime | None = Field(None, description="Last check time")


class LineageNode(BaseModel):
    """A node in the lineage graph."""

    id: str = Field(..., description="Asset public UUID")
    qualified_name: str = Field(..., description="Asset qualified name")
    name: str = Field(..., description="Display name")
    asset_type: str = Field(default="table", description="Asset type")
    source_type: str | None = Field(None, description="Database type")


class LineageEdge(BaseModel):
    """An edge in the lineage graph."""

    source: str = Field(..., description="Source qualified name")
    target: str = Field(..., description="Target qualified name")
    edge_type: str = Field(default="data_flow", description="Relationship type")
    confidence: float = Field(default=1.0, description="Confidence score")


class LineageGraph(BaseModel):
    """Lineage graph for an asset."""

    root: LineageNode = Field(..., description="The queried asset")
    upstream: list[LineageNode] = Field(default_factory=list, description="Dependencies")
    downstream: list[LineageNode] = Field(default_factory=list, description="Dependents")
    edges: list[LineageEdge] = Field(default_factory=list, description="All edges")


class Alert(BaseModel):
    """An alert instance."""

    id: str = Field(..., description="Alert ID")
    rule_id: str | None = Field(None, description="Rule ID")
    rule_name: str | None = Field(None, description="Rule name")
    asset_id: str | None = Field(None, description="Asset public UUID")
    qualified_name: str | None = Field(None, description="Asset qualified name")
    severity: str = Field(default="info", description="Severity level")
    status: str = Field(default="triggered", description="Alert status")
    message: str = Field(..., description="Alert message")
    triggered_at: datetime = Field(..., description="Trigger time")
    resolved_at: datetime | None = Field(None, description="Resolution time")


class AlertSummary(BaseModel):
    """Summary of alerts."""

    total_rules: int = Field(..., description="Total rules")
    active_rules: int = Field(..., description="Active rules")
    recent_alerts: int = Field(..., description="Recent alerts")
    unresolved_alerts: int = Field(..., description="Unresolved alerts")


class AlertRule(BaseModel):
    """An alert rule configuration."""

    id: str = Field(..., description="Rule public UUID")
    name: str = Field(..., description="Rule name")
    description: str | None = Field(None, description="Description")
    rule_type: str = Field(..., description="Rule type")
    severity: str = Field(default="warning", description="Severity")
    enabled: bool = Field(default=True, description="Is enabled")
    created_at: datetime | None = Field(None, description="Creation time")


class APIKey(BaseModel):
    """An API key."""

    id: str = Field(..., description="Key public UUID")
    name: str = Field(..., description="Key name")
    key_prefix: str = Field(..., description="Key prefix")
    key_suffix: str = Field(..., description="Key suffix")
    display_key: str = Field(..., description="Masked key")
    scope: str = Field(default="read-only", description="Permission scope")
    rate_limit_per_min: int = Field(..., description="Rate limit")
    burst_limit: int = Field(..., description="Burst limit")
    created_at: datetime | None = Field(None, description="Creation time")
    last_used_at: datetime | None = Field(None, description="Last use time")
    revoked_at: datetime | None = Field(None, description="Revocation time")
    is_active: bool = Field(default=True, description="Is active")


class CreatedAPIKey(APIKey):
    """A newly created API key (includes full key)."""

    key: str = Field(..., description="Full API key (shown once)")


# ============================================================================
# TECH-646: Intelligence Q&A Models
# ============================================================================


class IntelligenceSourceInfo(BaseModel):
    """Source information for knowledge base context."""

    asset_id: int = Field(..., description="Internal asset ID")
    asset_name: str = Field(..., description="Asset display name")
    domain: str | None = Field(None, description="Knowledge domain")
    generated_at: str | None = Field(None, description="KB generation timestamp")
    token_count: int = Field(0, description="Token count for this source")
    was_regenerated: bool = Field(False, description="Whether KB was regenerated")


class TokenUsage(BaseModel):
    """Token usage information from LLM call."""

    tokens_in: int = Field(0, description="Input tokens")
    tokens_out: int = Field(0, description="Output tokens")
    tokens_total: int = Field(0, description="Total tokens")
    cost_usd: float = Field(0.0, description="Estimated cost in USD")


class IntelligenceAnswer(BaseModel):
    """Response from intelligence Q&A."""

    question: str = Field(..., description="Original question")
    answer: str = Field(..., description="Generated answer")
    confidence: str = Field(default="medium", description="Confidence level")
    sources: list[IntelligenceSourceInfo] = Field(
        default_factory=list, description="Source knowledge bases used"
    )
    token_usage: TokenUsage = Field(
        default_factory=lambda: TokenUsage(tokens_in=0, tokens_out=0, tokens_total=0, cost_usd=0.0),
        description="Token usage breakdown",
    )


class IntelligenceGenerateResult(BaseModel):
    """Result of triggering intelligence generation."""

    job_id: str = Field(..., description="Job ID for tracking progress")
    asset_id: str = Field(..., description="Asset public UUID")
    status: str = Field(default="started", description="Job status")
    message: str = Field(
        default="Intelligence generation started",
        description="Status message",
    )


# ============================================================================
# TECH-646: Tags Models
# ============================================================================


class Tag(BaseModel):
    """A tag applied to an asset."""

    id: str = Field(..., description="Tag public UUID")
    name: str = Field(..., description="Tag name")
    category: str = Field(default="business", description="Tag category")
    description: str | None = Field(None, description="Tag description")
    object_path: str | None = Field(None, description="Object path")
    object_type: str | None = Field(None, description="Object type")
    created_at: datetime | None = Field(None, description="Creation time")


class BulkApplyResult(BaseModel):
    """Result of bulk tag apply operation."""

    applied: int = Field(..., description="Number of tags applied")
    failed: int = Field(default=0, description="Number of failures")
    total: int = Field(..., description="Total operations attempted")


# ============================================================================
# TECH-646: Badges Models
# ============================================================================


class Badge(BaseModel):
    """A report badge for data observability."""

    id: str = Field(..., description="Badge public UUID")
    label: str = Field(..., description="Badge label")
    asset_id: str | None = Field(None, description="Associated asset ID")
    tag_filters: list[str] = Field(default_factory=list, description="Tag filters")
    schema_drift_enabled: bool = Field(default=True, description="Monitor schema drift")
    freshness_enabled: bool = Field(default=True, description="Monitor freshness")
    include_upstream: bool = Field(default=False, description="Include upstream deps")
    is_active: bool = Field(default=True, description="Whether badge is active")
    badge_url: str | None = Field(None, description="Public badge URL")
    created_at: datetime | None = Field(None, description="Creation time")
    updated_at: datetime | None = Field(None, description="Last update time")


# ============================================================================
# TECH-646: Alert Destination Models
# ============================================================================


class AlertDestination(BaseModel):
    """An alert destination (Slack, email, webhook, etc.)."""

    id: str = Field(..., description="Destination public UUID")
    name: str = Field(..., description="Destination name")
    destination_type: str = Field(..., description="Type: email, slack, webhook, etc.")
    is_active: bool = Field(default=True, description="Is active")
    is_verified: bool = Field(default=False, description="Is verified")
    created_at: datetime | None = Field(None, description="Creation time")


# ============================================================================
# TECH-712: Metrics Models
# ============================================================================


class MetricsSummary(BaseModel):
    """Summary of metrics for an asset."""

    total_metrics: int = Field(..., description="Total metric definitions")
    active_metrics: int = Field(..., description="Active metrics")
    total_checks: int = Field(default=0, description="Total checks configured")
    passing: int = Field(default=0, description="Checks passing")
    failing: int = Field(default=0, description="Checks failing")
    warning: int = Field(default=0, description="Checks with warnings")
    error: int = Field(default=0, description="Checks with errors")
    health_percentage: float = Field(default=100.0, description="Health percentage")


class MetricDefinition(BaseModel):
    """A metric definition (row_count, null_percent, etc.)."""

    id: str = Field(..., description="Public UUID")
    internal_id: int = Field(..., description="Internal ID")
    asset_id: int = Field(..., description="Asset internal ID")
    table_path: str = Field(..., description="Full table path")
    column_name: str | None = Field(None, description="Column name")
    metric_type: str = Field(..., description="Type: row_count, null_percent, etc.")
    capture_interval: str = Field(default="daily", description="Capture interval")
    sensitivity: int = Field(default=3, description="Sensitivity (1-5)")
    is_active: bool = Field(default=True, description="Whether active")
    group_by_columns: list[str] | None = Field(None, description="Group by columns")
    percentile_value: float | None = Field(None, description="Percentile value")
    created_at: datetime | None = Field(None, description="Creation time")


class MetricSnapshot(BaseModel):
    """A metric snapshot (point-in-time value)."""

    id: int = Field(..., description="Snapshot ID")
    metric_definition_id: int = Field(..., description="Metric definition ID")
    value: float = Field(..., description="Captured value")
    group_values: dict[str, Any] | None = Field(None, description="Group values")
    captured_at: datetime = Field(..., description="Capture time")
    is_anomaly: bool = Field(default=False, description="Is anomaly")
    z_score: float | None = Field(None, description="Z-score")
    status: str | None = Field(None, description="Status: PASS, FAIL, WARNING")


class MetricCheck(BaseModel):
    """A check configuration for a metric."""

    id: int = Field(..., description="Check ID")
    uuid: str = Field(..., description="Public UUID")
    metric_definition_id: int = Field(..., description="Metric definition ID")
    name: str | None = Field(None, description="Check name")
    threshold_type: str = Field(..., description="Type: static, percentage, std_dev")
    threshold_value: float | None = Field(None, description="Threshold value")
    threshold_min: float | None = Field(None, description="Min threshold")
    threshold_max: float | None = Field(None, description="Max threshold")
    direction: str | None = Field(None, description="Direction: increase, decrease")
    is_active: bool = Field(default=True, description="Whether active")


class MetricCheckResult(BaseModel):
    """Result of a metric check evaluation."""

    id: int = Field(..., description="Result ID")
    metric_check_id: int = Field(..., description="Check ID")
    status: str = Field(..., description="Status: PASS, FAIL, WARNING, ERROR")
    current_value: float = Field(..., description="Current value")
    expected_value: float | None = Field(None, description="Expected value")
    deviation: float | None = Field(None, description="Deviation amount")
    evaluated_at: datetime = Field(..., description="Evaluation time")
    message: str | None = Field(None, description="Result message")


# ============================================================================
# TECH-712: Validity Models
# ============================================================================


class ValiditySummary(BaseModel):
    """Summary of validity checks for an asset."""

    total_rules: int = Field(..., description="Total validity rules")
    passing: int = Field(default=0, description="Rules passing")
    failing: int = Field(default=0, description="Rules failing")
    error: int = Field(default=0, description="Rules with errors")


class ValidityRule(BaseModel):
    """A validity rule definition."""

    id: int = Field(..., description="Internal ID")
    uuid: str = Field(..., description="Public UUID")
    table_path: str = Field(..., description="Full table path")
    column_name: str | None = Field(None, description="Column name")
    rule_type: str = Field(..., description="Rule type: NOT_NULL, UNIQUE, etc.")
    rule_config: dict[str, Any] | None = Field(None, description="Rule configuration")
    name: str | None = Field(None, description="Rule name")
    description: str | None = Field(None, description="Rule description")
    severity: str = Field(default="warning", description="Severity level")
    is_active: bool = Field(default=True, description="Whether active")
    alert_threshold_percent: float | None = Field(None, description="Alert threshold %")
    treat_null_as_valid: bool = Field(default=False, description="Treat null as valid")
    check_interval: str = Field(default="daily", description="Check interval")
    created_at: datetime | None = Field(None, description="Creation time")
    latest_status: str | None = Field(None, description="Latest check status")


class ValidityCheckResult(BaseModel):
    """Result of a validity check."""

    id: int = Field(..., description="Result ID")
    validity_rule_id: int = Field(..., description="Rule ID")
    status: str = Field(..., description="Status: pass, fail, error")
    total_rows: int = Field(..., description="Total rows checked")
    invalid_count: int = Field(..., description="Invalid records")
    invalid_percent: float = Field(..., description="Invalid percentage")
    invalid_samples: dict[str, Any] | None = Field(None, description="Sample invalid records")
    execution_duration_ms: int | None = Field(None, description="Execution time ms")
    error_message: str | None = Field(None, description="Error message if failed")
    checked_at: datetime = Field(..., description="Check time")
    created_at: datetime | None = Field(None, description="Creation time")


# ============================================================================
# TECH-712: Referential Integrity Models
# ============================================================================


class ReferentialSummary(BaseModel):
    """Summary of referential checks for an asset."""

    total_checks: int = Field(..., description="Total referential checks")
    active_checks: int = Field(..., description="Active checks")
    passing_checks: int = Field(default=0, description="Checks passing")
    failing_checks: int = Field(default=0, description="Checks failing")
    last_check_at: datetime | None = Field(None, description="Last check time")


class ReferentialCheck(BaseModel):
    """A referential integrity check definition."""

    id: str = Field(..., description="Public UUID")
    internal_id: int = Field(..., description="Internal ID")
    asset_id: int = Field(..., description="Asset internal ID")
    child_table_path: str = Field(..., description="Child table path")
    child_column_name: str = Field(..., description="Child column name (FK)")
    parent_table_path: str = Field(..., description="Parent table path")
    parent_column_name: str = Field(..., description="Parent column name (PK)")
    name: str | None = Field(None, description="Check name")
    description: str | None = Field(None, description="Description")
    capture_interval: str = Field(default="daily", description="Capture interval")
    max_orphan_count: int | None = Field(None, description="Max orphan count threshold")
    max_orphan_percent: float | None = Field(None, description="Max orphan % threshold")
    min_child_count: int | None = Field(None, description="Min child count (cardinality)")
    max_child_count: int | None = Field(None, description="Max child count (cardinality)")
    is_active: bool = Field(default=True, description="Whether active")
    last_checked_at: datetime | None = Field(None, description="Last check time")
    created_at: datetime | None = Field(None, description="Creation time")


class ReferentialCheckResult(BaseModel):
    """Result of a referential integrity check."""

    id: int = Field(..., description="Result ID")
    referential_check_id: int = Field(..., description="Check ID")
    status: str = Field(..., description="Status: pass, fail, error")
    orphan_count: int = Field(..., description="Orphan records found")
    orphan_percent: float = Field(..., description="Orphan percentage")
    total_child_rows: int = Field(..., description="Total child rows")
    orphan_sample: list[Any] | None = Field(None, description="Sample orphan values")
    parents_below_min: int | None = Field(None, description="Parents below min count")
    parents_above_max: int | None = Field(None, description="Parents above max count")
    cardinality_sample: list[Any] | None = Field(None, description="Sample cardinality issues")
    query_duration_ms: int | None = Field(None, description="Query execution time ms")
    checked_at: datetime = Field(..., description="Check time")
    error_message: str | None = Field(None, description="Error message if failed")
    created_at: datetime | None = Field(None, description="Creation time")


# ============================================================================
# TECH-758: Health Summary Models
# ============================================================================


class AttentionItem(BaseModel):
    """An item requiring attention."""

    type: str = Field(..., description="Type: alert, stale_data, schema_change")
    severity: str = Field(..., description="Severity level")
    title: str = Field(..., description="Item title")
    asset_id: str | None = Field(None, description="Asset UUID")
    asset_name: str | None = Field(None, description="Asset name")


class HealthSummary(BaseModel):
    """Unified health summary across all monitoring dimensions."""

    overall_status: str = Field(..., description="Status: healthy, warning, critical")
    alerts: AlertSummary = Field(..., description="Alerts summary")
    freshness: FreshnessSummary = Field(..., description="Freshness summary")
    schema_drift: SchemaSummary = Field(..., description="Schema drift summary")
    needs_attention: list[AttentionItem] = Field(
        default_factory=list, description="Top items needing attention"
    )
    generated_at: datetime = Field(..., description="Summary generation time")


# ============================================================================
# TECH-758: Asset Creation Models
# ============================================================================


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""

    success: bool = Field(..., description="Whether connection succeeded")
    latency_ms: int | None = Field(None, description="Connection latency in ms")
    error_message: str | None = Field(None, description="Error message if failed")
    error_code: str | None = Field(None, description="Error code if failed")
    tested_at: datetime = Field(..., description="Test timestamp")


class DiscoveryJob(BaseModel):
    """A schema discovery job."""

    job_id: str = Field(..., description="Job ID for tracking")
    asset_id: str = Field(..., description="Asset public UUID")
    status: str = Field(default="started", description="Job status")
    message: str = Field(default="Discovery started", description="Status message")
    started_at: datetime = Field(..., description="Start timestamp")


# ============================================================================
# TECH-758: Freshness Schedule Models
# ============================================================================


class FreshnessSchedule(BaseModel):
    """A freshness monitoring schedule."""

    id: str = Field(..., description="Schedule public UUID")
    asset_id: str = Field(..., description="Asset public UUID")
    table_path: str = Field(..., description="Table path (e.g., schema.table_name)")
    check_interval: str = Field(..., description="Check interval (e.g., '1h', '1d')")
    freshness_column: str | None = Field(None, description="Column used for freshness")
    expected_interval_hours: float | None = Field(
        None, description="Hours until data is considered stale"
    )
    expected_update_time: str | None = Field(
        None, description="Expected update time (e.g., '05:00')"
    )
    monitoring_mode: str = Field(..., description="'auto_learn' or 'explicit'")
    is_active: bool = Field(..., description="Whether monitoring is active")
    last_check: datetime | None = Field(None, description="Last check timestamp")
    next_check: datetime | None = Field(None, description="Next scheduled check")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


# ============================================================================
# TECH-758: Schema Baseline/Monitoring Models
# ============================================================================


class SchemaBaseline(BaseModel):
    """A schema baseline for drift detection."""

    id: str = Field(..., description="Baseline public UUID")
    asset_id: str = Field(..., description="Asset public UUID")
    table_count: int = Field(..., description="Number of tables captured")
    column_count: int = Field(..., description="Number of columns captured")
    captured_at: datetime = Field(..., description="Capture timestamp")
    description: str | None = Field(None, description="Baseline description")


class SchemaMonitoringStatus(BaseModel):
    """Schema drift monitoring status."""

    asset_id: str = Field(..., description="Asset public UUID")
    monitoring_enabled: bool = Field(..., description="Whether monitoring is enabled")
    schedule_type: str | None = Field(None, description="Schedule type if enabled")
    schedule_label: str | None = Field(None, description="Human-readable schedule")
    next_check_at: datetime | None = Field(None, description="Next scheduled check")
    last_check_at: datetime | None = Field(None, description="Last check time")
    baseline_id: str | None = Field(None, description="Current baseline snapshot ID")
    baseline_captured_at: datetime | None = Field(None, description="When baseline was captured")


# ============================================================================
# TECH-772: Recommendation Models
# ============================================================================


class FreshnessRecommendation(BaseModel):
    """Single freshness monitoring recommendation."""

    table_path: str = Field(..., description="Table identifier")
    suggested_check_interval: str = Field(
        ..., description="Suggested check interval (e.g., '1h', '6h', '24h')"
    )
    suggested_threshold_hours: float = Field(
        ..., description="Suggested staleness threshold in hours"
    )
    detected_frequency: str = Field(
        ..., description="Detected update pattern: hourly, daily, weekly, irregular"
    )
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    reasoning: str = Field(..., description="Human-readable explanation")
    data_points: int = Field(..., description="Number of history entries analyzed")


class FreshnessRecommendationsResponse(BaseModel):
    """Response for freshness recommendations endpoint."""

    recommendations: list[FreshnessRecommendation] = Field(
        default_factory=list, description="List of freshness recommendations"
    )
    asset_id: str = Field(..., description="Asset public UUID")
    tables_analyzed: int = Field(..., description="Total tables analyzed")
    tables_with_recommendations: int = Field(..., description="Tables with recommendations")


class MetricRecommendation(BaseModel):
    """Single metric recommendation for a column."""

    table_path: str = Field(..., description="Table identifier")
    column_name: str = Field(..., description="Column name")
    suggested_metric_type: str = Field(..., description="Suggested metric type")
    suggested_check_type: str = Field(..., description="Check type: validity, referential, metric")
    reasoning: str = Field(..., description="Why this metric makes sense")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")


class MetricsRecommendationsResponse(BaseModel):
    """Response for metrics recommendations endpoint."""

    recommendations: list[MetricRecommendation] = Field(
        default_factory=list, description="List of metric recommendations"
    )
    asset_id: str = Field(..., description="Asset public UUID")
    columns_analyzed: int = Field(..., description="Total columns analyzed")
    columns_with_recommendations: int = Field(..., description="Columns with recommendations")


class MonitoringStatus(BaseModel):
    """Current monitoring status for a table."""

    freshness: bool = Field(..., description="Has freshness monitoring")
    metrics: bool = Field(..., description="Has metrics monitoring")
    schema_drift: bool = Field(..., description="Has schema drift monitoring")
    validity: bool = Field(..., description="Has validity rules")


class CoverageRecommendation(BaseModel):
    """Single coverage recommendation for an unmonitored table."""

    table_path: str = Field(..., description="Table identifier")
    importance_score: float = Field(..., description="Table importance score (0.0-1.0)")
    row_count: int | None = Field(None, description="Estimated row count")
    column_count: int = Field(..., description="Number of columns")
    suggested_monitoring: list[str] = Field(
        default_factory=list, description="Suggested monitoring types"
    )
    reasoning: str = Field(..., description="Why this table is important")
    currently_monitored: MonitoringStatus = Field(..., description="Current monitoring state")


class CoverageRecommendationsResponse(BaseModel):
    """Response for coverage recommendations endpoint."""

    recommendations: list[CoverageRecommendation] = Field(
        default_factory=list, description="List of coverage recommendations"
    )
    asset_id: str = Field(..., description="Asset public UUID")
    total_tables: int = Field(..., description="Total tables in asset")
    monitored_tables: int = Field(..., description="Tables with any monitoring")
    coverage_percentage: float = Field(..., description="Percentage of tables monitored")


class ThresholdRecommendation(BaseModel):
    """Single threshold adjustment recommendation."""

    table_path: str = Field(..., description="Table identifier")
    metric_type: str = Field(..., description="What is being measured")
    current_threshold: float = Field(..., description="Current threshold setting")
    suggested_threshold: float = Field(..., description="Recommended threshold")
    direction: str = Field(..., description="Adjustment direction: increase or decrease")
    reasoning: str = Field(..., description="Why this change is recommended")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    historical_alerts: int = Field(..., description="Alert count in analysis window")
    projected_reduction: str = Field(..., description="Estimated alert reduction (e.g., '80%')")


class ThresholdsRecommendationsResponse(BaseModel):
    """Response for threshold recommendations endpoint."""

    recommendations: list[ThresholdRecommendation] = Field(
        default_factory=list, description="List of threshold recommendations"
    )
    asset_id: str = Field(..., description="Asset public UUID")
    monitored_items_analyzed: int = Field(..., description="Monitored items analyzed")
    items_with_recommendations: int = Field(..., description="Items with recommendations")


# ============================================================================
# TECH-771: Dry-Run / Preview Models
# ============================================================================


class FreshnessDryRunSample(BaseModel):
    """Sample of when threshold would have fired."""

    timestamp: str = Field(..., description="When the check occurred")
    hours_since_update: float = Field(..., description="Data age at that time")


class FreshnessDryRunResponse(BaseModel):
    """Result of freshness threshold dry-run."""

    table_path: str = Field(..., description="Table tested")
    threshold_hours: float = Field(..., description="Threshold tested")
    lookback_days: int = Field(..., description="Days of history analyzed")
    total_checks: int = Field(..., description="Total data points analyzed")
    would_alert_count: int = Field(..., description="Times threshold would fire")
    alert_rate_percent: float = Field(..., description="Percentage of alerts")
    current_age_hours: float | None = Field(None, description="Current data age")
    would_alert_now: bool = Field(..., description="Would alert right now")
    sample_alerts: list[FreshnessDryRunSample] = Field(
        default_factory=list, description="Sample of times it would alert"
    )
    recommendation: str = Field(..., description="Human-readable recommendation")


class SchemaDryRunChangeSample(BaseModel):
    """Sample schema change that would be detected."""

    change_type: str = Field(..., description="Type of change")
    table_name: str | None = Field(None, description="Table name")
    column_name: str | None = Field(None, description="Column name")
    old_value: str | None = Field(None, description="Previous value")
    new_value: str | None = Field(None, description="New value")
    severity: str = Field(..., description="Change severity")


class SchemaDryRunResponse(BaseModel):
    """Result of schema drift dry-run."""

    asset_id: str = Field(..., description="Asset tested")
    schedule_type: str = Field(..., description="Schedule type tested")
    baseline_exists: bool = Field(..., description="Whether baseline exists")
    tables_in_baseline: int = Field(0, description="Tables in baseline")
    tables_in_current: int = Field(0, description="Tables in current schema")
    changes_detected: bool = Field(False, description="Any changes found")
    changes_summary: dict[str, int] = Field(
        default_factory=dict, description="Breakdown by change type"
    )
    total_changes: int = Field(0, description="Total changes detected")
    sample_changes: list[SchemaDryRunChangeSample] = Field(
        default_factory=list, description="Sample of changes"
    )
    estimated_alerts_per_week: int = Field(0, description="Estimated weekly alerts")
    recommendation: str = Field(..., description="Human-readable recommendation")


class MetricsDryRunSample(BaseModel):
    """Sample metric snapshot that would have triggered."""

    captured_at: str = Field(..., description="When snapshot was captured")
    value: float = Field(..., description="Metric value")
    threshold_type: str = Field(..., description="Threshold type")
    threshold_value: float = Field(..., description="Threshold value tested")
    would_alert: bool = Field(..., description="Would this trigger")


class MetricsDryRunResponse(BaseModel):
    """Result of metrics dry-run."""

    metric_id: str = Field(..., description="Metric tested")
    metric_type: str = Field(..., description="Type of metric")
    threshold_type: str = Field(..., description="Threshold type tested")
    threshold_value: float = Field(..., description="Threshold value tested")
    lookback_days: int = Field(..., description="Days analyzed")
    total_snapshots: int = Field(..., description="Snapshots analyzed")
    would_alert_count: int = Field(..., description="Would-alert count")
    alert_rate_percent: float = Field(..., description="Alert rate")
    avg_value: float | None = Field(None, description="Average value")
    min_value: float | None = Field(None, description="Minimum value")
    max_value: float | None = Field(None, description="Maximum value")
    sample_alerts: list[MetricsDryRunSample] = Field(
        default_factory=list, description="Sample snapshots"
    )
    recommendation: str = Field(..., description="Recommendation")


class AlertPreviewSample(BaseModel):
    """Sample alert that would have fired."""

    id: str = Field(..., description="Alert ID")
    message: str = Field(..., description="Alert message")
    severity: str = Field(..., description="Severity level")
    triggered_at: str = Field(..., description="When triggered")
    asset_name: str | None = Field(None, description="Asset name")


class AlertPreviewResponse(BaseModel):
    """Result of alert preview."""

    lookback_hours: int = Field(..., description="Hours analyzed")
    alerts_would_match: int = Field(..., description="Matching alerts count")
    alerts_by_type: dict[str, int] = Field(default_factory=dict, description="Breakdown by type")
    alerts_by_severity: dict[str, int] = Field(
        default_factory=dict, description="Breakdown by severity"
    )
    sample_alerts: list[AlertPreviewSample] = Field(
        default_factory=list, description="Sample alerts"
    )
    recommendation: str = Field(..., description="Recommendation")
