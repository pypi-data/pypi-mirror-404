# AnomalyArmor Python SDK

Python SDK and CLI for AnomalyArmor data observability platform.

## Installation

```bash
pip install anomalyarmor-cli
```

## Quick Start

```python
from anomalyarmor import Client

client = Client(
    api_key="your-api-key",
    api_url="https://api.anomalyarmor.com"
)

# List assets
assets = client.assets.list()
```

## CLI Usage

```bash
# Configure credentials
anomalyarmor auth login

# List assets
anomalyarmor assets list

# Check freshness
anomalyarmor freshness summary
```

## Data Quality

### Metrics

Track quantitative metrics like row counts, null percentages, and distinct counts.

```python
# Get metrics summary
summary = client.metrics.summary("asset-uuid")
print(f"Active metrics: {summary.active_metrics}")

# Create a row count metric
metric = client.metrics.create(
    "asset-uuid",
    metric_type="row_count",
    table_path="catalog.schema.orders",
)

# Trigger capture
client.metrics.capture("asset-uuid", metric.id)
```

CLI:
```bash
anomalyarmor metrics summary <asset-uuid>
anomalyarmor metrics list <asset-uuid>
anomalyarmor metrics capture <asset-uuid> <metric-uuid>
```

### Validity Rules

Define and monitor data quality rules like NOT_NULL, UNIQUE, REGEX, and RANGE checks.

```python
# Get validity summary
summary = client.validity.summary("asset-uuid")
print(f"Failing rules: {summary.failing_rules}")

# Create a NOT NULL rule
rule = client.validity.create(
    "asset-uuid",
    rule_type="NOT_NULL",
    table_path="catalog.schema.orders",
    column_name="order_id",
    severity="critical",
)

# Run a check
result = client.validity.check("asset-uuid", rule.id)
print(f"Status: {result.status}, Invalid: {result.invalid_count}")
```

CLI:
```bash
anomalyarmor validity summary <asset-uuid>
anomalyarmor validity list <asset-uuid>
anomalyarmor validity check <asset-uuid> <rule-uuid>
```

### Referential Integrity

Monitor foreign key relationships and detect orphan records.

```python
# List referential checks
checks = client.referential.list("asset-uuid")

# Create a referential check
check = client.referential.create(
    "asset-uuid",
    child_table_path="catalog.schema.orders",
    child_column_name="customer_id",
    parent_table_path="catalog.schema.customers",
    parent_column_name="id",
)

# Execute check
result = client.referential.execute("asset-uuid", check.id)
print(f"Orphan count: {result.orphan_count}")
```

CLI:
```bash
anomalyarmor referential list <asset-uuid>
anomalyarmor referential execute <asset-uuid> <check-uuid>
```

## Documentation

See [docs.anomalyarmor.com](https://docs.anomalyarmor.com) for full documentation.
