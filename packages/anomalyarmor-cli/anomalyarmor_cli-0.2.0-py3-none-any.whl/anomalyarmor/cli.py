"""Command-line interface for AnomalyArmor.

Usage:
    anomalyarmor auth login
    anomalyarmor assets list
    anomalyarmor freshness get <asset>
    anomalyarmor schema changes --severity critical
    anomalyarmor alerts list --status triggered
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from anomalyarmor.config import (
    DEFAULT_API_URL,
    Config,
    clear_config,
    get_config_path,
    load_config,
    save_config,
)
from anomalyarmor.exceptions import (
    ArmorError,
    AuthenticationError,
    DataStaleError,
    NotFoundError,
    RateLimitError,
)

if TYPE_CHECKING:
    from anomalyarmor.client import Client

app = typer.Typer(
    name="anomalyarmor",
    help="AnomalyArmor CLI for data observability",
    add_completion=False,
)

console = Console()

# Exit codes per TECH-593 spec
EXIT_SUCCESS = 0
EXIT_STALENESS = 1
EXIT_AUTH_ERROR = 2
EXIT_NOT_FOUND = 3
EXIT_RATE_LIMIT = 4
EXIT_GENERAL_ERROR = 5


def handle_api_error(e: ArmorError) -> NoReturn:
    """Handle API errors with appropriate exit codes."""
    console.print(f"[red]Error:[/red] {e.message}")

    if isinstance(e, AuthenticationError):
        raise typer.Exit(EXIT_AUTH_ERROR)
    if isinstance(e, NotFoundError):
        raise typer.Exit(EXIT_NOT_FOUND)
    if isinstance(e, RateLimitError):
        retry_after = getattr(e, "retry_after", 60)
        console.print(f"[yellow]Retry after {retry_after} seconds[/yellow]")
        raise typer.Exit(EXIT_RATE_LIMIT)

    raise typer.Exit(EXIT_GENERAL_ERROR)


def get_client() -> Client:
    """Get an authenticated client."""
    from anomalyarmor import Client

    try:
        return Client()
    except AuthenticationError as e:
        console.print(f"[red]Authentication error:[/red] {e.message}")
        console.print("Run 'anomalyarmor auth login' to authenticate.")
        raise typer.Exit(EXIT_AUTH_ERROR) from e


# ============================================================================
# Auth commands
# ============================================================================

auth_app = typer.Typer(help="Authentication commands")
app.add_typer(auth_app, name="auth")


@auth_app.command("login")
def auth_login(
    api_key: str = typer.Option(
        ...,
        "--api-key",
        "-k",
        help="Your API key (starts with aa_live_)",
        prompt="Enter your API key",
        hide_input=True,
    ),
    api_url: str | None = typer.Option(
        None,
        "--api-url",
        help="API URL (defaults to production)",
    ),
) -> None:
    """Authenticate with AnomalyArmor."""
    # Validate the key format
    if not api_key.startswith("aa_live_") and not api_key.startswith("aa_test_"):
        console.print("[red]Error:[/red] Invalid API key format. Key should start with 'aa_live_'")
        raise typer.Exit(EXIT_AUTH_ERROR)

    # Test the key by making a request
    from anomalyarmor import Client

    try:
        client = Client(api_key=api_key, api_url=api_url)
        # Try to get API key usage to verify auth works
        client.api_keys.usage()
        client.close()
    except AuthenticationError as e:
        console.print(f"[red]Authentication failed:[/red] {e.message}")
        raise typer.Exit(EXIT_AUTH_ERROR)
    except ArmorError as e:
        handle_api_error(e)

    # Save config
    config = Config(
        api_key=api_key,
        api_url=api_url or DEFAULT_API_URL,
        timeout=30,
        retry_attempts=3,
    )
    save_config(config)

    console.print("[green]Successfully authenticated![/green]")
    console.print(f"Config saved to: {get_config_path()}")


@auth_app.command("status")
def auth_status() -> None:
    """Check authentication status."""
    config = load_config()

    if not config.api_key:
        console.print("[yellow]Not authenticated.[/yellow]")
        console.print("Run 'anomalyarmor auth login' to authenticate.")
        raise typer.Exit(EXIT_AUTH_ERROR)

    # Mask the key
    masked_key = config.api_key[:12] + "..." + config.api_key[-4:]
    console.print("[green]Authenticated[/green]")
    console.print(f"API Key: {masked_key}")
    console.print(f"API URL: {config.api_url}")


@auth_app.command("logout")
def auth_logout() -> None:
    """Remove stored credentials."""
    clear_config()
    console.print("[green]Logged out successfully.[/green]")


# ============================================================================
# Assets commands
# ============================================================================

assets_app = typer.Typer(help="Asset management commands")
app.add_typer(assets_app, name="assets")


@assets_app.command("list")
def assets_list(
    source: str | None = typer.Option(None, "--source", "-s", help="Filter by source type"),
    asset_type: str | None = typer.Option(None, "--type", "-t", help="Filter by asset type"),
    search: str | None = typer.Option(None, "--search", help="Search in names"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List assets."""
    client = get_client()

    try:
        assets = client.assets.list(
            source=source,
            asset_type=asset_type,
            search=search,
            limit=limit,
        )
    except ArmorError as e:
        handle_api_error(e)

    if not assets:
        console.print("No assets found.")
        return

    table = Table(title="Assets")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("Source")
    table.add_column("Active")

    for asset in assets:
        # Show first 8 chars of UUID for brevity
        short_id = asset.id[:8] if asset.id else "-"
        table.add_row(
            short_id,
            asset.name,
            asset.asset_type,
            asset.source_type or "-",
            "Yes" if asset.is_active else "No",
        )

    console.print(table)
    console.print(f"\nShowing {len(assets)} assets")


@assets_app.command("get")
def assets_get(asset_id: str = typer.Argument(..., help="Asset ID or qualified name")) -> None:
    """Get asset details."""
    client = get_client()

    try:
        asset = client.assets.get(asset_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Asset:[/bold] {asset.qualified_name}")
    console.print(f"ID: {asset.id}")
    console.print(f"Type: {asset.asset_type}")
    console.print(f"Source: {asset.source_type or '-'}")
    console.print(f"Active: {'Yes' if asset.is_active else 'No'}")
    if asset.description:
        console.print(f"Description: {asset.description}")


# ============================================================================
# Freshness commands
# ============================================================================

freshness_app = typer.Typer(help="Freshness monitoring commands")
app.add_typer(freshness_app, name="freshness")


@freshness_app.command("summary")
def freshness_summary() -> None:
    """Get freshness summary."""
    client = get_client()

    try:
        summary = client.freshness.summary()
    except ArmorError as e:
        handle_api_error(e)

    console.print("[bold]Freshness Summary[/bold]")
    console.print(f"Total Assets: {summary.total_assets}")
    console.print(f"Fresh: [green]{summary.fresh_count}[/green]")
    console.print(f"Stale: [red]{summary.stale_count}[/red]")
    console.print(f"Unknown: [yellow]{summary.unknown_count}[/yellow]")
    console.print(f"Freshness Rate: {summary.freshness_rate}%")


@freshness_app.command("get")
def freshness_get(
    asset_id: str = typer.Argument(..., help="Asset ID or qualified name"),
) -> None:
    """Check freshness for an asset."""
    client = get_client()

    try:
        status = client.freshness.get(asset_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Asset:[/bold] {status.qualified_name}")
    console.print("Status: ", end="")

    if status.status == "fresh":
        console.print("[green]Fresh[/green]")
    elif status.status == "stale":
        console.print("[red]Stale[/red]")
    elif status.status == "unknown":
        console.print("[yellow]Unknown[/yellow]")
    else:
        console.print(status.status)

    if status.last_update_time:
        console.print(f"Last Update: {status.last_update_time}")
    if status.hours_since_update is not None:
        console.print(f"Hours Since Update: {status.hours_since_update:.1f}")
    if status.staleness_threshold_hours:
        console.print(f"Threshold: {status.staleness_threshold_hours}h")

    # Exit with staleness code if stale
    if status.is_stale:
        raise typer.Exit(EXIT_STALENESS)


@freshness_app.command("list")
def freshness_list(
    status_filter: str | None = typer.Option(
        None, "--status", "-s", help="Filter by status (fresh, stale, unknown)"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List freshness status for all assets."""
    client = get_client()

    try:
        statuses = client.freshness.list(status=status_filter, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not statuses:
        console.print("No results found.")
        return

    table = Table(title="Freshness Status")
    table.add_column("Asset", style="cyan")
    table.add_column("Status")
    table.add_column("Hours Since Update")
    table.add_column("Threshold")

    for s in statuses:
        status_style = {
            "fresh": "[green]Fresh[/green]",
            "stale": "[red]Stale[/red]",
            "unknown": "[yellow]Unknown[/yellow]",
            "disabled": "[dim]Disabled[/dim]",
        }.get(s.status, s.status)

        table.add_row(
            s.qualified_name,
            status_style,
            f"{s.hours_since_update:.1f}" if s.hours_since_update else "-",
            f"{s.staleness_threshold_hours}h" if s.staleness_threshold_hours else "-",
        )

    console.print(table)


@freshness_app.command("check")
def freshness_check(
    asset_id: str = typer.Argument(..., help="Asset ID or qualified name"),
    max_age_hours: float | None = typer.Option(
        None, "--max-age", "-m", help="Max acceptable age in hours"
    ),
) -> None:
    """Check if an asset is fresh, fail if stale.

    Useful for CI/CD pipelines to gate on data freshness.
    Exit codes:
        0 - Data is fresh
        1 - Data is stale
        3 - Asset not found

    Example:
        anomalyarmor freshness check postgresql.mydb.public.users --max-age 24
    """
    client = get_client()

    try:
        status = client.freshness.require_fresh(asset_id, max_age_hours=max_age_hours)
    except DataStaleError as e:
        console.print(f"[red]STALE:[/red] {e.message}")
        console.print(f"Hours since update: {e.hours_since_update:.1f}h")
        console.print(f"Threshold: {e.threshold_hours:.1f}h")
        raise typer.Exit(EXIT_STALENESS)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]FRESH:[/green] {status.qualified_name}")
    if status.hours_since_update is not None:
        console.print(f"Hours since update: {status.hours_since_update:.1f}h")


@freshness_app.command("refresh")
def freshness_refresh(
    asset_id: str = typer.Argument(..., help="Asset ID or qualified name"),
) -> None:
    """Trigger a freshness check for an asset.

    Requires an API key with read-write or admin scope.

    Example:
        anomalyarmor freshness refresh postgresql.mydb.public.users
    """
    client = get_client()

    try:
        result = client.freshness.refresh(asset_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[green]Refresh initiated[/green]")
    console.print(f"Job ID: {result.get('job_id', 'N/A')}")
    console.print(f"Status: {result.get('status', 'queued')}")


# ============================================================================
# Schema commands
# ============================================================================

schema_app = typer.Typer(help="Schema drift monitoring commands")
app.add_typer(schema_app, name="schema")


@schema_app.command("summary")
def schema_summary() -> None:
    """Get schema changes summary."""
    client = get_client()

    try:
        summary = client.schema.summary()
    except ArmorError as e:
        handle_api_error(e)

    console.print("[bold]Schema Changes Summary[/bold]")
    console.print(f"Total Changes: {summary.total_changes}")
    console.print(f"Unacknowledged: [yellow]{summary.unacknowledged}[/yellow]")
    console.print(f"Critical: [red]{summary.critical_count}[/red]")
    console.print(f"Warning: [yellow]{summary.warning_count}[/yellow]")
    console.print(f"Info: {summary.info_count}")


@schema_app.command("changes")
def schema_changes(
    asset_id: str | None = typer.Option(None, "--asset", "-a", help="Filter by asset"),
    severity: str | None = typer.Option(None, "--severity", "-s", help="Filter by severity"),
    unacknowledged: bool = typer.Option(
        False, "--unacknowledged", "-u", help="Only unacknowledged"
    ),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List schema changes."""
    client = get_client()

    try:
        changes = client.schema.changes(
            asset_id=asset_id,
            severity=severity,
            unacknowledged_only=unacknowledged,
            limit=limit,
        )
    except ArmorError as e:
        handle_api_error(e)

    if not changes:
        console.print("No schema changes found.")
        return

    table = Table(title="Schema Changes")
    table.add_column("Asset", style="cyan")
    table.add_column("Change")
    table.add_column("Severity")
    table.add_column("Column")
    table.add_column("Ack")

    for c in changes:
        sev_style = {
            "critical": "[red]Critical[/red]",
            "warning": "[yellow]Warning[/yellow]",
            "info": "Info",
        }.get(c.severity, c.severity)

        table.add_row(
            c.qualified_name,
            c.change_type,
            sev_style,
            c.column_name or "-",
            "Yes" if c.acknowledged else "No",
        )

    console.print(table)


# ============================================================================
# Alerts commands
# ============================================================================

alerts_app = typer.Typer(help="Alert management commands")
app.add_typer(alerts_app, name="alerts")


@alerts_app.command("summary")
def alerts_summary() -> None:
    """Get alerts summary."""
    client = get_client()

    try:
        summary = client.alerts.summary()
    except ArmorError as e:
        handle_api_error(e)

    console.print("[bold]Alerts Summary[/bold]")
    console.print(f"Total Rules: {summary.total_rules}")
    console.print(f"Active Rules: {summary.active_rules}")
    console.print(f"Recent Alerts: {summary.recent_alerts}")
    console.print(f"Unresolved: [yellow]{summary.unresolved_alerts}[/yellow]")


@alerts_app.command("list")
def alerts_list(
    status: str | None = typer.Option(None, "--status", "-s", help="Filter by status"),
    severity: str | None = typer.Option(None, "--severity", help="Filter by severity"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List alerts."""
    client = get_client()

    try:
        alerts = client.alerts.list(status=status, severity=severity, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not alerts:
        console.print("No alerts found.")
        return

    table = Table(title="Alerts")
    table.add_column("Asset", style="cyan")
    table.add_column("Message")
    table.add_column("Severity")
    table.add_column("Status")

    for a in alerts:
        sev_style = {
            "critical": "[red]Critical[/red]",
            "warning": "[yellow]Warning[/yellow]",
            "info": "Info",
        }.get(a.severity, a.severity)

        status_style = {
            "triggered": "[red]Triggered[/red]",
            "acknowledged": "[yellow]Acknowledged[/yellow]",
            "resolved": "[green]Resolved[/green]",
        }.get(a.status, a.status)

        table.add_row(
            a.qualified_name or "-",
            a.message[:50] + "..." if len(a.message) > 50 else a.message,
            sev_style,
            status_style,
        )

    console.print(table)


# TECH-646: Alert rules subcommands
rules_app = typer.Typer(help="Alert rule management")
alerts_app.add_typer(rules_app, name="rules")


@rules_app.command("list")
def alert_rules_list(
    enabled_only: bool = typer.Option(False, "--enabled", help="Only enabled rules"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List alert rules."""
    client = get_client()

    try:
        rules = client.alerts.rules(enabled_only=enabled_only, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not rules:
        console.print("No alert rules found.")
        return

    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("ID")
    table.add_column("Enabled")
    table.add_column("Severity")

    for rule in rules:
        table.add_row(
            rule.name,
            rule.id[:8] + "..." if len(rule.id) > 8 else rule.id,
            "Yes" if rule.enabled else "No",
            rule.severity,
        )

    console.print(table)


@rules_app.command("get")
def alert_rules_get(
    rule_id: str = typer.Argument(..., help="Rule ID"),
) -> None:
    """Get alert rule details."""
    client = get_client()

    try:
        rule = client.alerts.get_rule(rule_id)
    except ArmorError as e:
        handle_api_error(e)

    if not rule:
        console.print(f"Rule {rule_id} not found.")
        return

    console.print(f"[bold]Rule:[/bold] {rule.name}")
    console.print(f"  ID: {rule.id}")
    console.print(f"  Type: {rule.rule_type}")
    console.print(f"  Severity: {rule.severity}")
    console.print(f"  Active: {'Yes' if rule.enabled else 'No'}")


@rules_app.command("delete")
def alert_rules_delete(
    rule_id: str = typer.Argument(..., help="Rule ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete an alert rule."""
    if not confirm:
        console.print(f"Delete rule {rule_id}?")
        if not typer.confirm("Are you sure?"):
            raise typer.Abort()

    client = get_client()

    try:
        client.alerts.delete_rule(rule_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]Rule {rule_id} deleted[/green]")


# TECH-646: Alert destinations subcommands
dests_app = typer.Typer(help="Alert destination management")
alerts_app.add_typer(dests_app, name="destinations")


@dests_app.command("list")
def alert_destinations_list(
    active_only: bool = typer.Option(False, "--active", help="Only active destinations"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List alert destinations."""
    client = get_client()

    try:
        destinations = client.alerts.list_destinations(active_only=active_only, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not destinations:
        console.print("No alert destinations found.")
        return

    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("ID")
    table.add_column("Active")
    table.add_column("Verified")

    for dest in destinations:
        table.add_row(
            dest.name,
            dest.destination_type,
            dest.id[:8] + "..." if len(dest.id) > 8 else dest.id,
            "Yes" if dest.is_active else "No",
            "Yes" if dest.is_verified else "No",
        )

    console.print(table)


@dests_app.command("get")
def alert_destinations_get(
    destination_id: str = typer.Argument(..., help="Destination ID"),
) -> None:
    """Get destination details."""
    client = get_client()

    try:
        dest = client.alerts.get_destination(destination_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Destination:[/bold] {dest.name}")
    console.print(f"  ID: {dest.id}")
    console.print(f"  Type: {dest.destination_type}")
    console.print(f"  Active: {'Yes' if dest.is_active else 'No'}")
    console.print(f"  Verified: {'Yes' if dest.is_verified else 'No'}")


@dests_app.command("delete")
def alert_destinations_delete(
    destination_id: str = typer.Argument(..., help="Destination ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete an alert destination."""
    if not confirm:
        console.print(f"Delete destination {destination_id}?")
        if not typer.confirm("Are you sure?"):
            raise typer.Abort()

    client = get_client()

    try:
        client.alerts.delete_destination(destination_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]Destination {destination_id} deleted[/green]")


# ============================================================================
# API Keys commands
# ============================================================================

api_keys_app = typer.Typer(help="API key management commands")
app.add_typer(api_keys_app, name="api-keys")


@api_keys_app.command("list")
def api_keys_list(
    include_revoked: bool = typer.Option(False, "--include-revoked", help="Include revoked keys"),
) -> None:
    """List API keys."""
    client = get_client()

    try:
        keys = client.api_keys.list(include_revoked=include_revoked)
    except ArmorError as e:
        handle_api_error(e)

    if not keys:
        console.print("No API keys found.")
        return

    table = Table(title="API Keys")
    table.add_column("Name", style="cyan")
    table.add_column("Key")
    table.add_column("Scope")
    table.add_column("Active")
    table.add_column("Last Used")

    for k in keys:
        table.add_row(
            k.name,
            k.display_key,
            k.scope,
            "[green]Yes[/green]" if k.is_active else "[red]No[/red]",
            str(k.last_used_at)[:10] if k.last_used_at else "Never",
        )

    console.print(table)


@api_keys_app.command("create")
def api_keys_create(
    name: str = typer.Option(..., "--name", "-n", help="Key name", prompt="Key name"),
    scope: str = typer.Option(
        "read-only",
        "--scope",
        "-s",
        help="Permission scope (read-only, read-write, admin)",
    ),
) -> None:
    """Create a new API key."""
    client = get_client()

    try:
        key = client.api_keys.create(name=name, scope=scope)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[green]API key created successfully![/green]")
    console.print()
    console.print(f"[bold]Key:[/bold] {key.key}")
    console.print()
    console.print("[yellow]IMPORTANT: This key will only be shown once![/yellow]")
    console.print("Store it securely.")


@api_keys_app.command("revoke")
def api_keys_revoke(
    key_id: str = typer.Argument(..., help="Key ID to revoke"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Revoke an API key."""
    if not confirm:
        typer.confirm("Are you sure you want to revoke this key?", abort=True)

    client = get_client()

    try:
        client.api_keys.revoke(key_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[green]API key revoked successfully.[/green]")


# ============================================================================
# Lineage commands
# ============================================================================

lineage_app = typer.Typer(help="Data lineage commands")
app.add_typer(lineage_app, name="lineage")


@lineage_app.command("get")
def lineage_get(
    asset_id: str = typer.Argument(..., help="Asset ID or qualified name"),
    depth: int = typer.Option(1, "--depth", "-d", help="Depth of lineage (1-5)"),
    direction: str = typer.Option(
        "both", "--direction", help="Direction: upstream, downstream, both"
    ),
) -> None:
    """Get lineage for an asset."""
    client = get_client()

    try:
        lineage = client.lineage.get(asset_id, depth=depth, direction=direction)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Lineage for:[/bold] {lineage.root.qualified_name}")
    console.print()

    if lineage.upstream:
        console.print("[bold]Upstream (dependencies):[/bold]")
        for node in lineage.upstream:
            console.print(f"  - {node.qualified_name}")

    if lineage.downstream:
        console.print("[bold]Downstream (dependents):[/bold]")
        for node in lineage.downstream:
            console.print(f"  - {node.qualified_name}")

    if not lineage.upstream and not lineage.downstream:
        console.print("No lineage information available.")


# ============================================================================
# Intelligence commands (TECH-646)
# ============================================================================

intelligence_app = typer.Typer(help="Intelligence Q&A commands")
app.add_typer(intelligence_app, name="intelligence")


@intelligence_app.command("ask")
def intelligence_ask(
    asset: str = typer.Argument(..., help="Asset identifier (UUID or qualified name)"),
    question: str = typer.Argument(..., help="Question to ask"),
    include_related: bool = typer.Option(
        False, "--include-related", help="Include related assets in context"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Ask a question about an asset using Intelligence Q&A.

    Uses the generated knowledge base to answer questions about
    database structure, lineage, and metadata.

    Examples:
        aa intelligence ask postgresql.analytics "What tables have customer data?"

        aa intelligence ask postgresql.analytics "list upstream tables" --json
    """
    client = get_client()

    try:
        answer = client.intelligence.ask(
            asset=asset,
            question=question,
            include_related_assets=include_related,
        )
    except ArmorError as e:
        # Check for intelligence not generated error
        if e.code == "INTELLIGENCE_NOT_GENERATED":
            console.print()
            console.print("[yellow]Intelligence has not been generated for this asset.[/yellow]")
            console.print()
            console.print("To generate intelligence, run:")
            console.print(f"  [bold]armor intelligence generate {asset}[/bold]")
            console.print()
            console.print(
                "[dim]This will analyze the asset's schema and create a "
                "knowledge base for Q&A.[/dim]"
            )
            raise typer.Exit(1)
        handle_api_error(e)

    if json_output:
        import json

        console.print_json(json.dumps(answer.model_dump()))
    else:
        console.print(f"[bold]Question:[/bold] {answer.question}")
        console.print()
        console.print("[bold]Answer:[/bold]")
        console.print(answer.answer)
        console.print()
        console.print(f"[dim]Confidence: {answer.confidence}[/dim]")
        if answer.sources:
            source_names = [s.asset_name for s in answer.sources[:5]]
            console.print(f"[dim]Sources: {', '.join(source_names)}[/dim]")


@intelligence_app.command("generate")
def intelligence_generate(
    asset: str = typer.Argument(..., help="Asset identifier (UUID, short UUID, or name)"),
    schemas: str | None = typer.Option(
        None,
        "--schemas",
        "-s",
        help="Comma-separated schemas to analyze (default: all)",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force regeneration"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Generate intelligence for an asset.

    Analyzes the asset's schema using AI to create descriptions,
    summaries, and a knowledge base for Q&A.

    Examples:
        armor intelligence generate postgresql.analytics

        armor intelligence generate 28f1942b --schemas bronze,silver

        armor intelligence generate BalloonBazaar --force
    """
    client = get_client()

    try:
        result = client.intelligence.generate(
            asset=asset,
            include_schemas=schemas,
            force_refresh=force,
        )
    except ArmorError as e:
        if e.code == "SCHEMA_NOT_DISCOVERED":
            console.print()
            console.print("[yellow]Schema discovery has not been run for this asset.[/yellow]")
            console.print()
            console.print(
                "Intelligence generation requires schema data. "
                "Run schema discovery first via the UI or API."
            )
            console.print()
            raise typer.Exit(EXIT_GENERAL_ERROR)
        handle_api_error(e)

    if json_output:
        import json

        console.print_json(json.dumps(result.model_dump()))
    else:
        console.print("[green]✓[/green] Intelligence generation started")
        console.print(f"  Job ID: {result.job_id}")
        console.print(f"  Asset: {result.asset_id}")
        console.print()
        console.print(
            "[dim]This may take a few minutes. Use 'armor jobs status' to check progress.[/dim]"
        )


# ============================================================================
# Jobs commands (TECH-646)
# ============================================================================

jobs_app = typer.Typer(help="Job status monitoring commands")
app.add_typer(jobs_app, name="jobs")


@jobs_app.command("status")
def jobs_status(
    job_id: str = typer.Argument(..., help="Job ID (UUID)"),
) -> None:
    """Get the status of a job.

    Example:
        armor jobs status b74fc72f-0332-427e-b508-e718f7b71a5d
    """
    client = get_client()

    try:
        result = client.jobs.status(job_id)

        # Display status
        status = result.get("status", "unknown")
        status_color = {
            "pending": "yellow",
            "running": "blue",
            "completed": "green",
            "failed": "red",
        }.get(status, "white")

        console.print(f"Job ID: {result.get('job_id')}")
        console.print(f"Status: [{status_color}]{status}[/{status_color}]")

        if result.get("workflow_name"):
            console.print(f"Workflow: {result.get('workflow_name')}")

        if result.get("asset_id"):
            console.print(f"Asset: {result.get('asset_id')}")

        if result.get("progress"):
            console.print(f"Progress: {result.get('progress')}%")

        if result.get("error"):
            console.print(f"[red]Error: {result.get('error')}[/red]")

        if result.get("created_at"):
            console.print(f"Created: {result.get('created_at')}")

        if result.get("completed_at"):
            console.print(f"Completed: {result.get('completed_at')}")

    except ArmorError as e:
        handle_api_error(e)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(EXIT_GENERAL_ERROR) from e


# ============================================================================
# Tags commands (TECH-646)
# ============================================================================

tags_app = typer.Typer(help="Tag management commands")
app.add_typer(tags_app, name="tags")


@tags_app.command("create")
def tags_create(
    name: str = typer.Argument(..., help="Tag name"),
    asset: str = typer.Option(..., "--asset", "-a", help="Asset (UUID or qualified name)"),
    object_path: str = typer.Option(
        ...,
        "--path",
        "-p",
        help="Object path (e.g., schema.table or schema.table.column)",
    ),
    category: str = typer.Option(
        "business",
        "--category",
        "-c",
        help="Category: business, technical, governance",
    ),
    description: str | None = typer.Option(None, "--description", "-d", help="Description"),
) -> None:
    """Create a custom tag on a database object.

    Examples:
        armor tags create pii_data --asset postgresql.analytics --path gold.customers

        armor tags create financial --asset pg.db --path public.orders --category governance
    """
    client = get_client()

    try:
        tag = client.tags.create(
            asset=asset,
            name=name,
            category=category,
            object_path=object_path,
            description=description,
        )
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]Tag created:[/green] {tag.name}")
    console.print(f"  Category: {tag.category}")
    if tag.object_path:
        console.print(f"  Path: {tag.object_path}")


@tags_app.command("apply")
def tags_apply(
    tag_names: str = typer.Argument(..., help="Comma-separated tag names"),
    asset: str = typer.Option(..., "--asset", "-a", help="Asset (UUID or qualified name)"),
    paths: str = typer.Option(
        ...,
        "--paths",
        "-p",
        help="Comma-separated object paths (e.g., 'schema.table1,schema.table2')",
    ),
    category: str = typer.Option(
        "business", "--category", "-c", help="Category: business, technical, governance"
    ),
) -> None:
    """Apply multiple tags to database objects.

    Each tag is applied to each object path, so total = tags × paths.

    Examples:
        armor tags apply "pii,gdpr" --asset pg.db --paths "gold.users,gold.orders"

        armor tags apply "financial" --asset postgresql.analytics --paths "gold.revenue"
    """
    client = get_client()

    tag_list = [t.strip() for t in tag_names.split(",")]
    path_list = [p.strip() for p in paths.split(",")]

    try:
        result = client.tags.apply(
            asset=asset,
            tag_names=tag_list,
            object_paths=path_list,
            category=category,
        )
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]Applied {result.applied} tags[/green]")
    if result.failed > 0:
        console.print(f"[yellow]Failed: {result.failed}[/yellow]")


@tags_app.command("bulk-apply")
def tags_bulk_apply(
    tag_name: str = typer.Argument(..., help="Tag name to apply"),
    assets: str = typer.Option(..., "--assets", help="Comma-separated asset identifiers"),
    category: str = typer.Option("business", "--category", "-c", help="Category"),
) -> None:
    """Apply a tag to multiple assets.

    Examples:
        aa tags bulk-apply finance-q4 --assets "postgresql.analytics,postgresql.warehouse"
    """
    client = get_client()

    asset_list = [a.strip() for a in assets.split(",")]

    try:
        result = client.tags.bulk_apply(
            tag_name=tag_name,
            asset_ids=asset_list,
            category=category,
        )
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]Applied tag to {result.applied} assets[/green]")
    if result.failed > 0:
        console.print(f"[yellow]Failed: {result.failed}[/yellow]")


@tags_app.command("list")
def tags_list(
    asset: str = typer.Option(..., "--asset", "-a", help="Asset (UUID or qualified name)"),
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    limit: int = typer.Option(100, "--limit", "-l", help="Max results"),
) -> None:
    """List tags for an asset.

    Examples:
        aa tags list --asset postgresql.analytics

        aa tags list --asset postgresql.analytics --category compliance
    """
    client = get_client()

    try:
        tags = client.tags.list(asset=asset, category=category, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not tags:
        console.print("No tags found.")
        return

    table = Table()
    table.add_column("Name", style="cyan")
    table.add_column("Category")
    table.add_column("Path")

    for tag in tags:
        table.add_row(
            tag.name,
            tag.category,
            tag.object_path or "(asset level)",
        )

    console.print(table)
    console.print(f"\nTotal: {len(tags)} tags")


# ============================================================================
# Badges commands (TECH-646)
# ============================================================================

badges_app = typer.Typer(help="Report badge management commands")
app.add_typer(badges_app, name="badges")


@badges_app.command("create")
def badges_create(
    label: str = typer.Argument(..., help="Badge label text"),
    asset: str = typer.Option(..., "--asset", "-a", help="Asset (UUID or qualified name)"),
    tags: str | None = typer.Option(None, "--tags", "-t", help="Comma-separated tag filters"),
    no_schema_drift: bool = typer.Option(
        False, "--no-schema-drift", help="Disable schema drift monitoring"
    ),
    no_freshness: bool = typer.Option(False, "--no-freshness", help="Disable freshness monitoring"),
    include_upstream: bool = typer.Option(
        False, "--include-upstream", help="Include upstream deps"
    ),
) -> None:
    """Create a new report badge.

    Examples:
        aa badges create "Data Quality" --asset postgresql.analytics

        aa badges create "Finance ETL" --asset postgresql.analytics --tags "financial,quarterly"
    """
    client = get_client()

    tag_filters = [t.strip() for t in tags.split(",")] if tags else None

    try:
        badge = client.badges.create(
            asset=asset,
            label=label,
            tag_filters=tag_filters,
            schema_drift_enabled=not no_schema_drift,
            freshness_enabled=not no_freshness,
            include_upstream=include_upstream,
        )
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[green]Badge created:[/green] {badge.label}")
    console.print(f"  ID: {badge.id}")
    console.print(f"  URL: {badge.badge_url}")


@badges_app.command("list")
def badges_list(
    all_badges: bool = typer.Option(False, "--all", help="Include inactive badges"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List all badges.

    Examples:
        aa badges list

        aa badges list --all
    """
    client = get_client()

    try:
        badges = client.badges.list(active_only=not all_badges, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not badges:
        console.print("No badges found.")
        return

    table = Table()
    table.add_column("Label", style="cyan")
    table.add_column("ID")
    table.add_column("Active")
    table.add_column("URL")

    for badge in badges:
        table.add_row(
            badge.label,
            badge.id[:8] + "..." if badge.id and len(badge.id) > 8 else badge.id,
            "Yes" if badge.is_active else "No",
            badge.badge_url or "",
        )

    console.print(table)
    console.print(f"\nTotal: {len(badges)} badges")


@badges_app.command("get")
def badges_get(
    badge_id: str = typer.Argument(..., help="Badge ID"),
) -> None:
    """Get badge details.

    Examples:
        aa badges get 123e4567-e89b-12d3-a456-426614174000
    """
    client = get_client()

    try:
        badge = client.badges.get(badge_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Badge:[/bold] {badge.label}")
    console.print(f"  ID: {badge.id}")
    console.print(f"  Asset: {badge.asset_id}")
    console.print(f"  Active: {'Yes' if badge.is_active else 'No'}")
    console.print(f"  Schema Drift: {'Yes' if badge.schema_drift_enabled else 'No'}")
    console.print(f"  Freshness: {'Yes' if badge.freshness_enabled else 'No'}")
    if badge.tag_filters:
        console.print(f"  Tags: {', '.join(badge.tag_filters)}")
    console.print(f"  URL: {badge.badge_url}")


@badges_app.command("delete")
def badges_delete(
    badge_id: str = typer.Argument(..., help="Badge ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete a badge.

    Examples:
        aa badges delete 123e4567-e89b-12d3-a456-426614174000 --yes
    """
    if not confirm:
        console.print(f"Delete badge {badge_id}?")
        if not typer.confirm("Are you sure?"):
            raise typer.Abort()

    client = get_client()

    try:
        client.badges.delete(badge_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[green]Badge deleted[/green]")


@badges_app.command("status")
def badges_status(
    badge_id: str = typer.Argument(..., help="Badge ID"),
) -> None:
    """Get current badge status.

    Examples:
        aa badges status 123e4567-e89b-12d3-a456-426614174000
    """
    client = get_client()

    try:
        status = client.badges.get_status(badge_id)
    except ArmorError as e:
        handle_api_error(e)

    badge_status = status.get("status", "unknown")
    color = (
        "green" if badge_status == "passing" else "red" if badge_status == "failing" else "yellow"
    )

    console.print(f"Badge: {status.get('badge_id', badge_id)}")
    console.print(f"Status: [{color}]{badge_status}[/{color}]")
    console.print(f"URL: {status.get('badge_url', '')}")


# ============================================================================
# Metrics commands (TECH-712)
# ============================================================================

metrics_app = typer.Typer(help="Data quality metrics commands")
app.add_typer(metrics_app, name="metrics")


@metrics_app.command("summary")
def metrics_summary(
    asset: str = typer.Argument(..., help="Asset UUID or qualified name"),
) -> None:
    """Get metrics summary for an asset.

    Example:
        anomalyarmor metrics summary postgresql.analytics
    """
    client = get_client()

    try:
        summary = client.metrics.summary(asset)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[bold]Metrics Summary[/bold]")
    console.print(f"Total Metrics: {summary.total_metrics}")
    console.print(f"Active: [green]{summary.active_metrics}[/green]")
    console.print(f"Total Checks: {summary.total_checks}")
    console.print(f"Passing: [green]{summary.passing}[/green]")
    console.print(f"Failing: [red]{summary.failing}[/red]")
    console.print(f"Health: {summary.health_percentage:.1f}%")


@metrics_app.command("list")
def metrics_list(
    asset: str = typer.Argument(..., help="Asset UUID or qualified name"),
    metric_type: str | None = typer.Option(None, "--type", "-t", help="Filter by metric type"),
    active_only: bool = typer.Option(False, "--active", help="Only active metrics"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List metrics for an asset.

    Example:
        anomalyarmor metrics list postgresql.analytics
        anomalyarmor metrics list postgresql.analytics --type null_percent
    """
    client = get_client()

    try:
        metrics = client.metrics.list(
            asset,
            metric_type=metric_type,
            is_active=True if active_only else None,
            limit=limit,
        )
    except ArmorError as e:
        handle_api_error(e)

    if not metrics:
        console.print("No metrics found.")
        return

    table = Table(title="Metrics")
    table.add_column("UUID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Table")
    table.add_column("Column")
    table.add_column("Active")

    for m in metrics:
        id_display = str(m.id)[:8] + "..." if len(str(m.id)) > 8 else str(m.id)
        table.add_row(
            id_display,
            m.metric_type,
            m.table_path,
            m.column_name or "-",
            "Yes" if m.is_active else "No",
        )

    console.print(table)
    console.print(f"\nShowing {len(metrics)} metrics")


@metrics_app.command("get")
def metrics_get(
    asset: str = typer.Argument(..., help="Asset UUID"),
    metric_id: str = typer.Argument(..., help="Metric UUID"),
) -> None:
    """Get metric details.

    Example:
        anomalyarmor metrics get postgresql.analytics abc123
    """
    client = get_client()

    try:
        metric = client.metrics.get(asset, metric_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Metric:[/bold] {metric.metric_type}")
    console.print(f"  UUID: {metric.id}")
    console.print(f"  Table: {metric.table_path}")
    if metric.column_name:
        console.print(f"  Column: {metric.column_name}")
    console.print(f"  Capture Interval: {metric.capture_interval}")
    console.print(f"  Active: {'Yes' if metric.is_active else 'No'}")


@metrics_app.command("capture")
def metrics_capture(
    asset: str = typer.Argument(..., help="Asset UUID"),
    metric_id: str = typer.Argument(..., help="Metric UUID"),
) -> None:
    """Trigger immediate metric capture.

    Requires read-write API key scope.

    Example:
        anomalyarmor metrics capture postgresql.analytics abc123
    """
    client = get_client()

    try:
        result = client.metrics.capture(asset, metric_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[green]Capture completed[/green]")
    console.print(f"Snapshots created: {result.get('snapshot_count', 0)}")


# ============================================================================
# Validity commands (TECH-712)
# ============================================================================

validity_app = typer.Typer(help="Validity rule commands")
app.add_typer(validity_app, name="validity")


@validity_app.command("summary")
def validity_summary(
    asset: str = typer.Argument(..., help="Asset UUID or qualified name"),
) -> None:
    """Get validity summary for an asset.

    Example:
        anomalyarmor validity summary postgresql.analytics
    """
    client = get_client()

    try:
        summary = client.validity.summary(asset)
    except ArmorError as e:
        handle_api_error(e)

    console.print("[bold]Validity Summary[/bold]")
    console.print(f"Total Rules: {summary.total_rules}")
    console.print(f"Passing: [green]{summary.passing}[/green]")
    console.print(f"Failing: [red]{summary.failing}[/red]")
    console.print(f"Errors: [yellow]{summary.error}[/yellow]")


@validity_app.command("list")
def validity_list(
    asset: str = typer.Argument(..., help="Asset UUID or qualified name"),
    rule_type: str | None = typer.Option(None, "--type", "-t", help="Filter by rule type"),
    active_only: bool = typer.Option(False, "--active", help="Only active rules"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List validity rules for an asset.

    Example:
        anomalyarmor validity list postgresql.analytics
        anomalyarmor validity list postgresql.analytics --type NOT_NULL
    """
    client = get_client()

    try:
        rules = client.validity.list(
            asset,
            rule_type=rule_type,
            is_active=True if active_only else None,
            limit=limit,
        )
    except ArmorError as e:
        handle_api_error(e)

    if not rules:
        console.print("No validity rules found.")
        return

    table = Table(title="Validity Rules")
    table.add_column("UUID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Table")
    table.add_column("Column")
    table.add_column("Severity")
    table.add_column("Status")

    for r in rules:
        sev_style = {
            "critical": "[red]Critical[/red]",
            "warning": "[yellow]Warning[/yellow]",
            "info": "Info",
        }.get(r.severity, r.severity)

        status_style = {
            "pass": "[green]pass[/green]",
            "fail": "[red]fail[/red]",
            "error": "[red]error[/red]",
        }.get(r.latest_status or "", r.latest_status or "-")

        table.add_row(
            r.uuid[:8] + "..." if len(r.uuid) > 8 else r.uuid,
            r.rule_type,
            r.table_path,
            r.column_name or "-",
            sev_style,
            status_style,
        )

    console.print(table)
    console.print(f"\nShowing {len(rules)} rules")


@validity_app.command("get")
def validity_get(
    asset: str = typer.Argument(..., help="Asset UUID"),
    rule_id: str = typer.Argument(..., help="Rule UUID"),
) -> None:
    """Get validity rule details.

    Example:
        anomalyarmor validity get postgresql.analytics abc123
    """
    client = get_client()

    try:
        rule = client.validity.get(asset, rule_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Rule:[/bold] {rule.name or rule.rule_type}")
    console.print(f"  UUID: {rule.uuid}")
    console.print(f"  Type: {rule.rule_type}")
    console.print(f"  Table: {rule.table_path}")
    if rule.column_name:
        console.print(f"  Column: {rule.column_name}")
    console.print(f"  Severity: {rule.severity}")
    console.print(f"  Active: {'Yes' if rule.is_active else 'No'}")
    if rule.latest_status:
        console.print(f"  Latest Status: {rule.latest_status}")


@validity_app.command("check")
def validity_check(
    asset: str = typer.Argument(..., help="Asset UUID"),
    rule_id: str = typer.Argument(..., help="Rule UUID"),
    sample_limit: int = typer.Option(10, "--samples", "-s", help="Max invalid samples"),
) -> None:
    """Trigger immediate validity check.

    Requires read-write API key scope.

    Example:
        anomalyarmor validity check postgresql.analytics abc123
    """
    client = get_client()

    try:
        result = client.validity.check(asset, rule_id, sample_limit=sample_limit)
    except ArmorError as e:
        handle_api_error(e)

    status_color = "green" if result.status == "pass" else "red"
    console.print(f"Status: [{status_color}]{result.status}[/{status_color}]")
    console.print(f"Total Rows: {result.total_rows}")
    console.print(f"Invalid Count: {result.invalid_count}")
    console.print(f"Invalid Percent: {result.invalid_percent:.2f}%")

    if result.status in ("fail", "error"):
        raise typer.Exit(EXIT_STALENESS)


# ============================================================================
# Referential integrity commands (TECH-712)
# ============================================================================

referential_app = typer.Typer(help="Referential integrity check commands")
app.add_typer(referential_app, name="referential")


@referential_app.command("list")
def referential_list(
    asset: str = typer.Argument(..., help="Asset UUID or qualified name"),
    active_only: bool = typer.Option(False, "--active", help="Only active checks"),
    limit: int = typer.Option(50, "--limit", "-l", help="Max results"),
) -> None:
    """List referential integrity checks for an asset.

    Example:
        anomalyarmor referential list postgresql.analytics
    """
    client = get_client()

    try:
        checks = client.referential.list(
            asset,
            is_active=True if active_only else None,
            limit=limit,
        )
    except ArmorError as e:
        handle_api_error(e)

    if not checks:
        console.print("No referential checks found.")
        return

    table = Table(title="Referential Checks")
    table.add_column("UUID", style="dim")
    table.add_column("Child Table")
    table.add_column("Column")
    table.add_column("Parent Table")
    table.add_column("Active")
    table.add_column("Status")

    for c in checks:
        # id is now the UUID in the updated model
        id_display = str(c.id)[:8] + "..." if len(str(c.id)) > 8 else str(c.id)
        table.add_row(
            id_display,
            c.child_table_path,
            c.child_column_name,
            c.parent_table_path,
            "Yes" if c.is_active else "No",
            "-",  # Status not included in list response
        )

    console.print(table)
    console.print(f"\nShowing {len(checks)} checks")


@referential_app.command("get")
def referential_get(
    asset: str = typer.Argument(..., help="Asset UUID"),
    check_id: str = typer.Argument(..., help="Check UUID"),
) -> None:
    """Get referential check details.

    Example:
        anomalyarmor referential get postgresql.analytics abc123
    """
    client = get_client()

    try:
        check = client.referential.get(asset, check_id)
    except ArmorError as e:
        handle_api_error(e)

    console.print(f"[bold]Check:[/bold] {check.name or 'Referential Check'}")
    console.print(f"  UUID: {check.id}")
    console.print(f"  Child: {check.child_table_path}.{check.child_column_name}")
    console.print(f"  Parent: {check.parent_table_path}.{check.parent_column_name}")
    console.print(f"  Interval: {check.capture_interval}")
    console.print(f"  Active: {'Yes' if check.is_active else 'No'}")
    if check.last_checked_at:
        console.print(f"  Last Check: {check.last_checked_at}")


@referential_app.command("execute")
def referential_execute(
    asset: str = typer.Argument(..., help="Asset UUID"),
    check_id: str = typer.Argument(..., help="Check UUID"),
) -> None:
    """Execute referential check immediately.

    Requires read-write API key scope.

    Example:
        anomalyarmor referential execute postgresql.analytics abc123
    """
    client = get_client()

    try:
        result = client.referential.execute(asset, check_id)
    except ArmorError as e:
        handle_api_error(e)

    status_color = "green" if result.status == "pass" else "red"
    console.print(f"Status: [{status_color}]{result.status}[/{status_color}]")
    console.print(f"Total Child Rows: {result.total_child_rows}")
    console.print(f"Orphan Count: {result.orphan_count}")
    console.print(f"Orphan Percent: {result.orphan_percent:.2f}%")

    if result.status in ("fail", "error"):
        raise typer.Exit(EXIT_STALENESS)


@referential_app.command("results")
def referential_results(
    asset: str = typer.Argument(..., help="Asset UUID"),
    check_id: str = typer.Argument(..., help="Check UUID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Max results"),
) -> None:
    """List historical results for a referential check.

    Example:
        anomalyarmor referential results postgresql.analytics abc123
    """
    client = get_client()

    try:
        results = client.referential.results(asset, check_id, limit=limit)
    except ArmorError as e:
        handle_api_error(e)

    if not results:
        console.print("No results found.")
        return

    table = Table(title="Check Results")
    table.add_column("Checked At")
    table.add_column("Status")
    table.add_column("Orphans")
    table.add_column("Percent")

    for r in results:
        status_style = {
            "pass": "[green]pass[/green]",
            "fail": "[red]fail[/red]",
            "error": "[red]error[/red]",
        }.get(r.status, r.status)

        table.add_row(
            str(r.checked_at)[:19] if r.checked_at else "-",
            status_style,
            str(r.orphan_count),
            f"{r.orphan_percent:.2f}%",
        )

    console.print(table)


if __name__ == "__main__":
    app()
