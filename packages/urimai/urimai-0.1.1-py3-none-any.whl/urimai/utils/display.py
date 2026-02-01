"""Rich console utilities for beautiful CLI output."""

from contextlib import asynccontextmanager
from typing import Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.tree import Tree

# Global console instance
console = Console()


@asynccontextmanager
async def pipeline_status(message: str):
    """Show a spinner during an async operation, then clear it."""
    with console.status(f"[bold]{message}[/bold]", spinner="dots"):
        yield


def print_sub(message: str) -> None:
    """Print an indented sub-result line."""
    console.print(f"    [dim]↳[/dim] {message}")


def print_success(message: str) -> None:
    """Print success message in green.

    Args:
        message: Success message to display
    """
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print error message in red.

    Args:
        message: Error message to display
    """
    console.print(f"[red]✗[/red] {message}", style="red")


def print_info(message: str) -> None:
    """Print info message in blue.

    Args:
        message: Info message to display
    """
    console.print(f"[blue]ℹ[/blue] {message}")


def print_warning(message: str) -> None:
    """Print warning message in yellow.

    Args:
        message: Warning message to display
    """
    console.print(f"[yellow]⚠[/yellow] {message}", style="yellow")


def print_step(step: str, message: str) -> None:
    """Print a step in a process.

    Args:
        step: Step emoji or icon
        message: Step description
    """
    console.print(f"{step} {message}")


def print_sql(sql: str, title: str = "SQL Query") -> None:
    """Print SQL query with syntax highlighting.

    Args:
        sql: SQL query string
        title: Title for the panel
    """
    syntax = Syntax(sql, "sql", theme="monokai", line_numbers=False)
    panel = Panel(syntax, title=title, border_style="cyan")
    console.print(panel)


def print_table(
    data: list[dict[str, Any]], title: str | None = None, max_rows: int | None = None
) -> None:
    """Print data as a Rich table.

    Args:
        data: List of dictionaries to display
        title: Optional table title
        max_rows: Maximum number of rows to display (None for all)
    """
    if not data:
        print_warning("No data to display")
        return

    # Create table
    table = Table(title=title, show_header=True, header_style="bold magenta")

    # Add columns
    for column in data[0].keys():
        table.add_column(column, style="cyan")

    # Add rows (limit if specified)
    display_data = data[:max_rows] if max_rows else data
    for row in display_data:
        table.add_row(*[str(value) for value in row.values()])

    # Show truncation message if needed
    if max_rows and len(data) > max_rows:
        console.print(table)
        print_info(f"Showing {max_rows} of {len(data)} rows")
    else:
        console.print(table)


def print_databases(databases: list[dict[str, Any]]) -> None:
    """Print list of databases as a table.

    Args:
        databases: List of database information dictionaries
    """
    if not databases:
        print_warning("No databases registered")
        return

    table = Table(title="Registered Databases", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Last Synced", style="yellow")

    for db in databases:
        table.add_row(
            db.get("name", ""),
            db.get("path", ""),
            db.get("last_synced_at", "").split("T")[0],  # Show only date
        )

    console.print(table)


def print_settings(settings: list[dict[str, str]]) -> None:
    """Print settings as a table.

    Args:
        settings: List of setting key-value pairs
    """
    if not settings:
        print_info("No settings configured (using defaults)")
        return

    table = Table(title="Settings", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for setting in settings:
        table.add_row(setting.get("key", ""), setting.get("value", ""))

    console.print(table)


def create_progress() -> Progress:
    """Create a Rich progress bar.

    Returns:
        Progress instance with spinner and text columns
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def print_panel(content: str, title: str, style: str = "blue") -> None:
    """Print content in a panel.

    Args:
        content: Panel content
        title: Panel title
        style: Panel border style color
    """
    panel = Panel(content, title=title, border_style=style)
    console.print(panel)


# ============================================================================
# Interactive Chat UI Helpers
# ============================================================================


def print_welcome_banner(db_name: str, table_count: int) -> None:
    """Print welcome banner for interactive session.

    Args:
        db_name: Name of the database
        table_count: Number of tables in the database
    """
    welcome_text = f"""[bold cyan]urimai - Interactive Session[/bold cyan]

[green]Database:[/green] {db_name} ({table_count} tables)

Type your questions in natural language or use these commands:
  [yellow]/schema[/yellow]   - Show database overview (use /schema <table> for details)
  [yellow]/tables[/yellow]   - List all tables
  [yellow]/profile[/yellow]  - Profile a table (usage: /profile <table_name>)
  [yellow]/quality[/yellow]  - Assess data quality (usage: /quality <table_name>)
  [yellow]/history[/yellow]  - Show query history
  [yellow]/clear[/yellow]    - Clear conversation history
  [yellow]/help[/yellow]     - Show this help
  [yellow]/exit[/yellow]     - Exit session

Ready to answer your questions!"""

    panel = Panel(welcome_text, border_style="bold blue", padding=(1, 2))
    console.print(panel)
    console.print()


def print_user_prompt() -> None:
    """Print user input prompt."""
    console.print("[bold cyan]You:[/bold cyan] ", end="")


def print_assistant_header() -> None:
    """Print assistant response header."""
    console.print("\n[bold green]Assistant:[/bold green]")


def print_conversation_history(query_results: list[Any]) -> None:
    """Print conversation history in a formatted panel.

    Args:
        query_results: List of QueryResult objects
    """
    if not query_results:
        print_info("No query history yet")
        return

    history_text = ""
    for i, result in enumerate(query_results, 1):
        history_text += f"[cyan]{i}. {result.question}[/cyan]\n"
        history_text += f"   [dim]→ {result.answer}[/dim]\n"
        history_text += f"   [dim]({result.row_count} rows)[/dim]\n\n"

    panel = Panel(
        history_text.strip(),
        title=f"Conversation History ({len(query_results)} queries)",
        border_style="yellow",
    )
    console.print(panel)


def print_schema_info(schemas: list[Any]) -> None:
    """Print database schema information.

    Args:
        schemas: List of SchemaInfo objects
    """
    if not schemas:
        print_warning("No schema information available")
        return

    for schema in schemas:
        table_name = schema.table_name
        columns = schema.original_metadata.get("columns", [])
        enriched = schema.enriched_metadata  # dict or None
        col_descriptions = enriched.get("column_descriptions", {}) if enriched else {}

        # Build title with optional table purpose
        title = f"Table: {table_name}"
        if enriched and enriched.get("table_purpose"):
            title += f"\n{enriched['table_purpose']}"

        # Create table for this schema
        table = Table(
            title=title,
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Nullable", style="yellow")
        if col_descriptions:
            table.add_column("Description", style="dim")

        for col in columns:
            nullable = "✓" if col.get("is_nullable", True) else "✗"
            row = [
                col.get("column_name", ""),
                col.get("data_type", ""),
                nullable,
            ]
            if col_descriptions:
                row.append(col_descriptions.get(col.get("column_name", ""), ""))
            table.add_row(*row)

        console.print(table)

        # Relationships
        if enriched and enriched.get("relationships"):
            console.print("  Relationships:", style="bold")
            for rel in enriched["relationships"]:
                console.print(f"    - {rel}")

        # Business context
        if enriched and enriched.get("business_context"):
            console.print(f"  Context: {enriched['business_context']}", style="italic dim")

        console.print()


def print_database_overview(db_context: Any, schemas: list[Any]) -> None:
    """Print database overview with context panel and table summary.

    Args:
        db_context: DatabaseContext object (or None)
        schemas: List of SchemaInfo objects
    """
    if not schemas:
        print_warning("No schema information available")
        return

    # Database context panel
    if db_context:
        entities = ", ".join(db_context.key_entities) if db_context.key_entities else "N/A"
        context_text = (
            f"[bold]Domain:[/bold] {db_context.domain}\n"
            f"[bold]Purpose:[/bold] {db_context.purpose}\n"
            f"[bold]Key Entities:[/bold] {entities}\n"
            f"[bold]Data Characteristics:[/bold] {db_context.data_characteristics}"
        )
        console.print(Panel(context_text, title="Database Context", border_style="cyan"))
        console.print()

    # Table summary table
    table = Table(
        title=f"Tables ({len(schemas)})",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Table Name", style="cyan")
    table.add_column("Purpose", style="green")
    table.add_column("Columns", justify="right")
    table.add_column("Relationships", justify="right")

    for schema in schemas:
        enriched = schema.enriched_metadata or {}
        purpose = enriched.get("table_purpose", "")

        col_count = len(schema.original_metadata.get("columns", []))
        rel_count = len(enriched.get("relationships", []))

        table.add_row(
            schema.table_name,
            purpose,
            str(col_count),
            str(rel_count),
        )

    console.print(table)
    console.print()
    console.print("[dim]Use /schema <table_name> for details or /schema graph for relationships[/dim]")


def print_table_detail(schema: Any) -> None:
    """Print detailed schema for a single table.

    Args:
        schema: SchemaInfo object
    """
    columns = schema.original_metadata.get("columns", [])
    enriched = schema.enriched_metadata
    col_descriptions = enriched.get("column_descriptions", {}) if enriched else {}

    # Build title with optional table purpose
    title = f"Table: {schema.table_name}"
    if enriched and enriched.get("table_purpose"):
        title += f"\n{enriched['table_purpose']}"

    # Create table for this schema
    table = Table(
        title=title,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Column", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Nullable", style="yellow")
    if col_descriptions:
        table.add_column("Description", style="dim")

    for col in columns:
        nullable = "\u2713" if col.get("is_nullable", True) else "\u2717"
        row = [
            col.get("column_name", ""),
            col.get("data_type", ""),
            nullable,
        ]
        if col_descriptions:
            row.append(col_descriptions.get(col.get("column_name", ""), ""))
        table.add_row(*row)

    console.print(table)

    # Relationships
    if enriched and enriched.get("relationships"):
        console.print("  Relationships:", style="bold")
        for rel in enriched["relationships"]:
            console.print(f"    - {rel}")

    # Business context
    if enriched and enriched.get("business_context"):
        console.print(f"  Context: {enriched['business_context']}", style="italic dim")

    console.print()


def print_schema_graph(schemas: list[Any]) -> None:
    """Print an ASCII relationship graph using Rich Tree.

    Args:
        schemas: List of SchemaInfo objects
    """
    if not schemas:
        print_warning("No schema information available")
        return

    tree = Tree("[bold cyan]Database Schema[/bold cyan]")

    # Build FK index: for each table, collect incoming FKs
    # incoming[table_name] = list of "source_table.column"
    incoming: dict[str, list[str]] = {}
    # outgoing[table_name] = list of (column, ref_table, ref_column)
    outgoing: dict[str, list[tuple[str, str, str]]] = {}

    for schema in schemas:
        constraints = schema.original_metadata.get("constraints", [])
        for constraint in constraints:
            if constraint.get("constraint_type") == "FOREIGN KEY":
                src_col = constraint.get("source_column", "")
                ref_table = constraint.get("referenced_table", "")
                ref_col = constraint.get("referenced_column", "")
                if ref_table and src_col:
                    outgoing.setdefault(schema.table_name, []).append(
                        (src_col, ref_table, ref_col)
                    )
                    incoming.setdefault(ref_table, []).append(
                        f"{schema.table_name}.{src_col}"
                    )

    # Build set of FK source columns per table for annotation
    fk_source_cols: dict[str, set[str]] = {}
    for table_name, fk_list in outgoing.items():
        fk_source_cols[table_name] = {src_col for src_col, _, _ in fk_list}

    for schema in schemas:
        table_name = schema.table_name
        columns = schema.original_metadata.get("columns", [])
        enriched = schema.enriched_metadata or {}

        col_count = len(columns)
        branch = tree.add(f"[bold green]{table_name}[/bold green] [dim]({col_count} cols)[/dim]")

        # Show columns with type and FK annotation
        table_fk_cols = fk_source_cols.get(table_name, set())
        for col in columns:
            col_name = col.get("column_name", "")
            col_type = col.get("data_type", "")
            # Check if this column is an FK source
            fk_target = None
            for src_col, ref_table, ref_col in outgoing.get(table_name, []):
                if src_col == col_name:
                    fk_target = f"{ref_table}.{ref_col}" if ref_col else ref_table
                    break
            if fk_target:
                branch.add(f"[cyan]{col_name}[/cyan] [dim]{col_type}[/dim] [magenta]-> {fk_target}[/magenta]")
            else:
                branch.add(f"[cyan]{col_name}[/cyan] [dim]{col_type}[/dim]")

        # Show relationships from enriched metadata (inferred joins)
        relationships = enriched.get("relationships", [])
        if relationships:
            rel_branch = branch.add("[yellow]Relationships[/yellow]")
            for rel in relationships:
                rel_branch.add(f"[dim]{rel}[/dim]")

        # Show incoming FKs
        inc = incoming.get(table_name, [])
        if inc:
            for src in inc:
                branch.add(f"[dim]<- {src}[/dim]")

    console.print(tree)
    console.print()


def print_table_list(table_names: list[str]) -> None:
    """Print simple list of table names.

    Args:
        table_names: List of table names
    """
    if not table_names:
        print_warning("No tables found")
        return

    tables_text = "\n".join(f"  • [cyan]{name}[/cyan]" for name in table_names)
    panel = Panel(
        tables_text,
        title=f"Tables ({len(table_names)})",
        border_style="green",
    )
    console.print(panel)


def print_help() -> None:
    """Print help information for interactive session."""
    help_text = """[bold]Available Commands:[/bold]

[yellow]/schema[/yellow]              - Show database overview and table summary
[yellow]/schema <table>[/yellow]      - Show detailed schema for a specific table
[yellow]/schema graph[/yellow]        - Show relationship graph
[yellow]/tables[/yellow]              - Show a quick list of all table names
[yellow]/profile <table>[/yellow]     - Generate statistical profile for a table
[yellow]/quality <table>[/yellow]     - AI-powered data quality assessment with context-aware checks
[yellow]/export[/yellow]              - Export data dictionary as Excel (.xlsx)
[yellow]/export markdown[/yellow]     - Export as Markdown (.md)
[yellow]/history[/yellow]             - Display all questions and answers from this session
[yellow]/clear[/yellow]               - Clear the conversation history (fresh start)
[yellow]/help[/yellow]                - Show this help message
[yellow]/exit[/yellow]                - Exit the interactive session
[yellow]/quit[/yellow]                - Same as /exit

[bold]Asking Questions:[/bold]

Just type your question in natural language! The AI will:
  1. Understand your question
  2. Generate appropriate SQL queries
  3. Execute them on your database
  4. Provide natural language answers

[bold]Examples:[/bold]

  • How many users are in the database?
  • Show me the top 10 products by revenue
  • What's the average order value?
  • List all customers from California

The assistant remembers context, so you can ask follow-up questions!"""

    panel = Panel(help_text, title="Help", border_style="blue", padding=(1, 2))
    console.print(panel)


def print_goodbye() -> None:
    """Print goodbye message when exiting."""
    console.print("\n[bold cyan]👋 Goodbye![/bold cyan]")
    console.print("[dim]Thank you for using urimai[/dim]\n")


def print_table_profile(profile: Any) -> None:
    """Print table profile with column statistics.

    Args:
        profile: TableProfile object
    """
    # Header
    header = f"""[bold cyan]Table Profile:[/bold cyan] {profile.table_name}
[green]Rows:[/green] {profile.row_count:,} | [green]Columns:[/green] {profile.column_count}
[dim]Profiled at: {profile.created_at.split('T')[0]}[/dim]"""

    console.print(Panel(header, border_style="blue"))
    console.print()

    # Column profiles table
    table = Table(
        title=f"Column Statistics ({profile.column_count} columns)",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Column", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Role", style="yellow")
    table.add_column("Nulls %", justify="right")
    table.add_column("Distinct %", justify="right")
    table.add_column("Stats", style="dim")

    for col in profile.columns:
        # Role with confidence
        role_display = ""
        if col.inferred_role:
            confidence_color = "green" if col.role_confidence >= 0.8 else "yellow" if col.role_confidence >= 0.6 else "red"
            role_display = f"[{confidence_color}]{col.inferred_role}[/{confidence_color}]"

        # Stats summary
        stats = []
        if col.mean is not None:
            stats.append(f"μ={col.mean:.2f}")
        if col.min_length is not None:
            stats.append(f"len={col.min_length}-{col.max_length}")
        stats_display = " ".join(stats) if stats else "-"

        table.add_row(
            col.column_name,
            col.data_type,
            role_display,
            f"{col.null_percentage:.1f}%",
            f"{col.distinct_percentage:.1f}%",
            stats_display,
        )

    console.print(table)
    console.print()

    # Summary insights
    high_null_cols = [c.column_name for c in profile.columns if c.null_percentage > 50]
    high_distinct_cols = [c.column_name for c in profile.columns if c.distinct_percentage > 95]

    if high_null_cols or high_distinct_cols:
        insights = []
        if high_null_cols:
            insights.append(f"[yellow]High nulls:[/yellow] {', '.join(high_null_cols)}")
        if high_distinct_cols:
            insights.append(f"[cyan]High cardinality:[/cyan] {', '.join(high_distinct_cols)}")

        console.print(Panel("\n".join(insights), title="Quick Insights", border_style="yellow"))
        console.print()


def print_usage(usage_stats) -> None:
    """Print token usage summary line."""
    if usage_stats.total_tokens > 0:
        console.print(
            f"\n[dim]tokens: {usage_stats.total_tokens:,} "
            f"(in: {usage_stats.input_tokens:,} / out: {usage_stats.output_tokens:,}) "
            f"| api calls: {usage_stats.requests}[/dim]"
        )


def print_quality_report(quality_report: Any) -> None:
    """Print data quality report with scores and issues.

    Args:
        quality_report: QualityReport object
    """
    # Determine overall color based on score
    overall_score = quality_report.overall_score
    if overall_score >= 90:
        score_color = "green"
        score_emoji = "✅"
    elif overall_score >= 70:
        score_color = "yellow"
        score_emoji = "⚠️"
    else:
        score_color = "red"
        score_emoji = "❌"

    # Header with overall score
    header = f"""[bold]Quality Report:[/bold] {quality_report.table_name}
[bold {score_color}]{score_emoji} Overall Score: {overall_score:.1f}/100[/bold {score_color}]
[dim]Assessed at: {quality_report.created_at.split('T')[0]}[/dim]"""

    console.print(Panel(header, border_style=score_color))
    console.print()

    # Dimension scores table
    table = Table(
        title="Quality Dimensions",
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Dimension", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status", justify="center")

    dimensions = [
        ("Completeness", quality_report.completeness_score),
        ("Uniqueness", quality_report.uniqueness_score),
        ("Validity", quality_report.validity_score),
        ("Consistency", quality_report.consistency_score),
    ]

    for dimension, score in dimensions:
        # Color code the score
        if score >= 90:
            score_str = f"[green]{score:.1f}[/green]"
            status = "[green]✓[/green]"
        elif score >= 70:
            score_str = f"[yellow]{score:.1f}[/yellow]"
            status = "[yellow]⚠[/yellow]"
        else:
            score_str = f"[red]{score:.1f}[/red]"
            status = "[red]✗[/red]"

        table.add_row(dimension, score_str, status)

    console.print(table)
    console.print()

    # Issues breakdown
    if quality_report.issues:
        # Group issues by severity
        critical = [i for i in quality_report.issues if i.severity == "critical"]
        warnings = [i for i in quality_report.issues if i.severity == "warning"]
        info = [i for i in quality_report.issues if i.severity == "info"]

        # Summary
        issues_summary = f"[red]{len(critical)} Critical[/red]  |  [yellow]{len(warnings)} Warnings[/yellow]  |  [blue]{len(info)} Info[/blue]"
        console.print(Panel(issues_summary, title=f"Issues Found ({len(quality_report.issues)} total)", border_style="yellow"))
        console.print()

        # Display critical issues
        if critical:
            console.print("[bold red]Critical Issues:[/bold red]")
            for issue in critical[:5]:  # Show max 5 critical
                col_text = f" [{issue.column_name}]" if issue.column_name else ""
                console.print(f"  [red]✗[/red] {issue.issue}{col_text}")
                console.print(f"    [dim]→ {issue.recommendation}[/dim]")
            if len(critical) > 5:
                console.print(f"  [dim]... and {len(critical) - 5} more[/dim]")
            console.print()

        # Display warnings
        if warnings:
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for issue in warnings[:5]:  # Show max 5 warnings
                col_text = f" [{issue.column_name}]" if issue.column_name else ""
                console.print(f"  [yellow]⚠[/yellow] {issue.issue}{col_text}")
                console.print(f"    [dim]→ {issue.recommendation}[/dim]")
            if len(warnings) > 5:
                console.print(f"  [dim]... and {len(warnings) - 5} more[/dim]")
            console.print()

        # Display info issues (collapsed by default)
        if info:
            console.print(f"[bold blue]Info:[/bold blue] {len(info)} informational items")
            console.print()

    else:
        console.print(Panel("[green]✓ No quality issues detected![/green]", border_style="green"))
        console.print()
