"""SQL query commands for VirtualDojo CLI."""

import typer
from rich.table import Table

from ..client import SyncVirtualDojoClient
from ..utils.output import (
    console,
    print_error,
    print_info,
    print_json,
    print_success,
    print_yaml,
)

app = typer.Typer(help="SQL query operations", no_args_is_help=True)


def _get_client(profile: str | None = None) -> SyncVirtualDojoClient:
    """Get a configured API client."""
    return SyncVirtualDojoClient(profile)


@app.command("query")
def sql_query(
    query: str = typer.Argument(..., help="SQL query to execute"),
    confirm: bool = typer.Option(
        False, "--confirm", "-c", help="Confirm write operations (INSERT/UPDATE/DELETE)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Validate query without executing"
    ),
    limit: int = typer.Option(
        100, "--limit", "-l", help="Row limit for SELECT (1-1000)"
    ),
    timeout: int = typer.Option(
        30, "--timeout", "-t", help="Query timeout in seconds (1-300)"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, yaml"
    ),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Execute a SQL query.

    For SELECT queries, results are returned directly.
    For INSERT/UPDATE/DELETE, use --confirm to execute.

    Examples:
        vdojo sql query "SELECT * FROM accounts LIMIT 5"
        vdojo sql query "SELECT name, email FROM contacts WHERE status = 'active'"
        vdojo sql query "UPDATE accounts SET status = 'inactive' WHERE id = '123'" --confirm
        vdojo sql query "INSERT INTO tasks (name) VALUES ('Follow up')" --confirm
        vdojo sql query "DELETE FROM tasks WHERE status = 'done'" --confirm
        vdojo sql query "SELECT * FROM opportunities" --dry-run
    """
    client = _get_client(profile)

    data = {
        "query": query,
        "limit": min(max(limit, 1), 1000),
        "timeout": min(max(timeout, 1), 300),
        "dry_run": dry_run,
    }

    if confirm:
        data["confirm_write"] = True

    try:
        with console.status("[dim]Executing query...[/dim]", spinner="dots"):
            result = client.post("/api/v1/sql/query", data)
    except Exception as e:
        print_error(f"Query failed: {e}")
        raise typer.Exit(1) from None

    if not result.get("success", False):
        error = result.get("error", "Unknown error")
        error_type = result.get("error_type", "")
        suggestions = result.get("suggestions", [])

        print_error(f"{error}")
        if error_type:
            console.print(f"[dim]Error type: {error_type}[/dim]")
        if suggestions:
            console.print("\n[bold]Suggestions:[/bold]")
            for suggestion in suggestions:
                console.print(f"  - {suggestion}")
        raise typer.Exit(1) from None

    # Handle dry run
    if dry_run:
        print_success("Query validation passed")
        if result.get("estimated_rows"):
            console.print(f"  Estimated rows: {result.get('estimated_rows')}")
        if result.get("operation"):
            console.print(f"  Operation: {result.get('operation')}")
        return

    # Handle results
    operation = result.get("operation", "SELECT")
    rows = result.get("rows", [])
    columns = result.get("columns", [])
    row_count = result.get("row_count", len(rows))
    execution_time = result.get("execution_time_ms", 0)

    if format == "json":
        print_json(result)
        return
    if format == "yaml":
        print_yaml(result)
        return

    # For write operations
    if operation in ["INSERT", "UPDATE", "DELETE"]:
        print_success(f"{operation} completed: {row_count} row(s) affected")
        if execution_time:
            console.print(f"[dim]Execution time: {execution_time}ms[/dim]")
        return

    # For SELECT operations
    if not rows:
        print_info("No rows returned")
        return

    table = Table(show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)

    for row in rows:
        # Convert row values to strings for display
        str_values = [
            str(v) if v is not None else "[dim]NULL[/dim]" for v in row.values()
        ]
        table.add_row(*str_values)

    console.print(table)
    console.print(f"\n[dim]{row_count} row(s) · {execution_time}ms[/dim]")


@app.command("validate")
def sql_validate(
    query: str = typer.Argument(..., help="SQL query to validate"),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Validate a SQL query without executing it.

    Checks syntax, permissions, and provides optimization suggestions.

    Examples:
        vdojo sql validate "SELECT * FROM accounts"
        vdojo sql validate "UPDATE contacts SET status = 'active'"
    """
    client = _get_client(profile)

    try:
        with console.status("[dim]Validating query...[/dim]", spinner="dots"):
            result = client.post("/api/v1/sql/validate", {"query": query})
    except Exception as e:
        print_error(f"Validation failed: {e}")
        raise typer.Exit(1) from None

    if result.get("valid", False):
        print_success("Query is valid")

        if result.get("operation"):
            console.print(f"  Operation: {result.get('operation')}")
        if result.get("estimated_rows"):
            console.print(f"  Estimated rows: {result.get('estimated_rows')}")

        warnings = result.get("warnings", [])
        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  - {warning}")

        suggestions = result.get("suggestions", [])
        if suggestions:
            console.print("\n[bold]Optimization suggestions:[/bold]")
            for suggestion in suggestions:
                console.print(f"  - {suggestion}")
    else:
        print_error(f"Query is invalid: {result.get('error', 'Unknown error')}")
        raise typer.Exit(1) from None


@app.command("schema")
def sql_schema(
    object_name: str | None = typer.Argument(
        None, help="Object name to get schema for"
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, yaml"
    ),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """Get database schema information.

    Without arguments, lists all available objects.
    With an object name, shows fields for that object.

    Examples:
        vdojo sql schema                    # List all objects
        vdojo sql schema accounts           # Show accounts fields
        vdojo sql schema opportunities      # Show opportunities fields
        vdojo sql schema projects_co        # Show custom object fields
    """
    client = _get_client(profile)

    params = {}
    if object_name:
        params["object_name"] = object_name

    try:
        with console.status("[dim]Fetching schema...[/dim]", spinner="dots"):
            result = client.get("/api/v1/sql/schema", params=params)
    except Exception as e:
        print_error(f"Failed to get schema: {e}")
        raise typer.Exit(1) from None

    if not result.get("success", True):
        print_error(result.get("error", "Unknown error"))
        raise typer.Exit(1) from None

    if format == "json":
        print_json(result)
        return
    if format == "yaml":
        print_yaml(result)
        return

    if object_name:
        # Show fields for specific object
        obj_data = result.get("object", {})
        fields = obj_data.get("fields", []) if obj_data else result.get("fields", [])
        if not fields:
            print_info(f"No fields found for {object_name}")
            return

        obj_label = obj_data.get("label", object_name) if obj_data else object_name
        table = Table(
            show_header=True, header_style="bold cyan", title=f"Schema: {obj_label}"
        )
        table.add_column("Field")
        table.add_column("Label")
        table.add_column("Type")
        table.add_column("Required")

        for field in fields:
            required = (
                "[red]Yes[/red]" if field.get("required", False) else "[dim]No[/dim]"
            )
            table.add_row(
                field.get("name", "-"),
                field.get("label", "-")[:25],
                field.get("type", "-"),
                required,
            )

        console.print(table)
        console.print(f"\n[dim]{len(fields)} fields[/dim]")
    else:
        # List all objects
        objects = result.get("objects", {})
        if not objects:
            print_info("No objects found")
            return

        table = Table(
            show_header=True, header_style="bold cyan", title="Available Objects"
        )
        table.add_column("Object")
        table.add_column("Label")
        table.add_column("Type")
        table.add_column("Fields")

        # Handle both dict and list formats
        if isinstance(objects, dict):
            obj_items = [(name, data) for name, data in objects.items()]
        else:
            obj_items = [(obj.get("name", "-"), obj) for obj in objects]

        for obj_name, obj_data in sorted(obj_items):
            obj_type = (
                obj_data.get("type", "standard")
                if isinstance(obj_data, dict)
                else "standard"
            )
            if obj_name.endswith("_co"):
                obj_type = "[cyan]custom[/cyan]"
            label = obj_data.get("label", "-") if isinstance(obj_data, dict) else "-"
            fields = obj_data.get("fields", []) if isinstance(obj_data, dict) else []
            field_count = len(fields) if fields else "-"
            table.add_row(
                obj_name,
                label[:30] if label else "-",
                obj_type,
                str(field_count),
            )

        console.print(table)
        console.print(f"\n[dim]{len(objects)} objects[/dim]")


@app.command("history")
def sql_history(
    limit: int = typer.Option(
        20, "--limit", "-l", help="Number of queries to return (1-100)"
    ),
    operation: str | None = typer.Option(
        None,
        "--operation",
        "-o",
        help="Filter by operation: SELECT, INSERT, UPDATE, DELETE",
    ),
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, yaml"
    ),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """View SQL query execution history.

    Examples:
        vdojo sql history
        vdojo sql history --limit 50
        vdojo sql history --operation SELECT
        vdojo sql history --operation DELETE --limit 10
    """
    client = _get_client(profile)

    params = {"limit": min(max(limit, 1), 100)}
    if operation:
        params["operation"] = operation.upper()

    try:
        with console.status("[dim]Fetching history...[/dim]", spinner="dots"):
            result = client.get("/api/v1/sql/history", params=params)
    except Exception as e:
        print_error(f"Failed to get history: {e}")
        raise typer.Exit(1) from None

    if format == "json":
        print_json(result)
        return
    if format == "yaml":
        print_yaml(result)
        return

    queries = result.get("queries", [])
    if not queries:
        print_info("No query history found")
        return

    table = Table(show_header=True, header_style="bold cyan", title="Query History")
    table.add_column("Time")
    table.add_column("Operation")
    table.add_column("Query")
    table.add_column("Rows")
    table.add_column("Duration")
    table.add_column("Status")

    op_colors = {
        "SELECT": "cyan",
        "INSERT": "green",
        "UPDATE": "yellow",
        "DELETE": "red",
    }

    for q in queries:
        op = q.get("operation", "-")
        op_color = op_colors.get(op, "white")
        status = "[green]OK[/green]" if q.get("success", True) else "[red]FAIL[/red]"
        query_text = q.get("query", "-")[:50]
        if len(q.get("query", "")) > 50:
            query_text += "..."

        table.add_row(
            str(q.get("executed_at", "-"))[:19],
            f"[{op_color}]{op}[/{op_color}]",
            query_text,
            str(q.get("row_count", "-")),
            f"{q.get('execution_time_ms', '-')}ms",
            status,
        )

    console.print(table)
    console.print(f"\n[dim]{len(queries)} queries[/dim]")


@app.command("stats")
def sql_stats(
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, yaml"
    ),
    profile: str | None = typer.Option(None, "--profile", "-p", help="Profile to use"),
) -> None:
    """View SQL execution statistics.

    Shows query performance metrics and usage statistics.

    Examples:
        vdojo sql stats
        vdojo sql stats --format json
    """
    client = _get_client(profile)

    try:
        with console.status("[dim]Fetching stats...[/dim]", spinner="dots"):
            result = client.get("/api/v1/sql/stats")
    except Exception as e:
        print_error(f"Failed to get stats: {e}")
        raise typer.Exit(1) from None

    if format == "json":
        print_json(result)
        return
    if format == "yaml":
        print_yaml(result)
        return

    console.print("\n[bold cyan]SQL Execution Statistics[/bold cyan]")

    # Operations summary
    ops = result.get("operations", {})
    if ops:
        console.print("\n[bold]Operations:[/bold]")
        op_table = Table(show_header=True, header_style="bold")
        op_table.add_column("Operation")
        op_table.add_column("Count", justify="right")
        op_table.add_column("Avg Time", justify="right")
        op_table.add_column("Success Rate", justify="right")

        for op_name, op_data in ops.items():
            count = op_data.get("count", 0)
            avg_time = op_data.get("avg_execution_time_ms", 0)
            success_rate = op_data.get("success_rate", 100)
            rate_color = (
                "green"
                if success_rate >= 95
                else "yellow" if success_rate >= 80 else "red"
            )

            op_table.add_row(
                op_name,
                str(count),
                f"{avg_time:.0f}ms",
                f"[{rate_color}]{success_rate:.1f}%[/{rate_color}]",
            )

        console.print(op_table)

    # Performance metrics
    perf = result.get("performance", {})
    if perf:
        console.print("\n[bold]Performance:[/bold]")
        console.print(f"  Total queries: {perf.get('total_queries', 0)}")
        console.print(
            f"  Avg execution time: {perf.get('avg_execution_time_ms', 0):.0f}ms"
        )
        console.print(f"  Total rows processed: {perf.get('total_rows', 0)}")

    # Rate limit status
    rate_limit = result.get("rate_limit", {})
    if rate_limit:
        console.print("\n[bold]Rate Limits (remaining/limit):[/bold]")
        for op, data in rate_limit.items():
            remaining = data.get("remaining", 0)
            limit = data.get("limit", 0)
            color = (
                "green"
                if remaining > limit * 0.5
                else "yellow" if remaining > limit * 0.2 else "red"
            )
            console.print(f"  {op}: [{color}]{remaining}/{limit}[/{color}]")
