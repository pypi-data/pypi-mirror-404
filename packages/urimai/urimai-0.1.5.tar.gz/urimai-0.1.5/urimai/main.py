"""urimai CLI - Main entry point."""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import typer
from typing_extensions import Annotated

from urimai.storage.metadata_store import MetadataStore
from urimai.storage.models import DatabaseInfo, QueryPlan, ConversationalResponse, SuccessAnswer, RetryWithFeedback
from urimai.core.db_manager import DatabaseManager
from urimai.core.schema_extractor import SchemaExtractor
from urimai.core.query_executor import QueryExecutor
from urimai.core.interactive import run_interactive_session
from urimai.agents.query_agent import QueryGenerationAgent
from urimai.agents.analysis_agent import ResultAnalysisAgent
from urimai.utils.display import (
    print_success,
    print_error,
    print_info,
    print_warning,
    print_databases,
    print_settings,
    print_step,
    create_progress,
    print_table,
    print_sql,
    print_panel,
)
from urimai.config import Config, CSV_DATABASES_DIR, is_setup_complete, _has_env_api_keys, ensure_data_dir


async def _enrich_schemas(schemas, extractor, enrichment_agent, store, db_id, progress, task):
    """Enrich schemas in two passes: individual tables, then cross-table relationships."""
    from urimai.agents.schema_context_agent import SchemaContextAgent

    # Build database context for cross-table awareness
    db_context = extractor.build_database_context(schemas)

    # === Pass 1: Individual table enrichment (concurrent) ===
    sem = asyncio.Semaphore(5)
    enriched_count = 0
    total = len(schemas)
    enriched_map = {}  # table_name -> enriched storage dict

    async def _enrich_one(schema):
        nonlocal enriched_count
        async with sem:
            schema_data = extractor.prepare_for_enrichment(schema, database_context=db_context)
            enriched = await enrichment_agent.enrich_schema(schema_data)
            storage_dict = enriched.to_storage_dict()
            await store.update_enriched_metadata(
                database_id=db_id,
                table_name=schema.table_name,
                enriched_metadata=storage_dict
            )
            enriched_map[schema.table_name] = storage_dict
            enriched_count += 1
            progress.update(
                task,
                description=f"Enriching schemas ({enriched_count}/{total})..."
            )

    results = await asyncio.gather(
        *[_enrich_one(s) for s in schemas],
        return_exceptions=True
    )

    for schema, result in zip(schemas, results):
        if isinstance(result, Exception):
            print_warning(f"Failed to enrich table '{schema.table_name}': {result}")

    # === Pass 2: Cross-table relationship analysis ===
    progress.update(task, description="Analyzing cross-table relationships...")

    try:
        context_agent = SchemaContextAgent()
        sample_data = {s.table_name: s.sample_data for s in schemas}

        db_context_result = await context_agent.analyze_database(
            schemas=schemas,
            enriched_metadata=enriched_map,
            sample_data=sample_data,
        )

        # Write back refined per-table relationships
        refined = db_context_result.refined_relationships
        for schema in schemas:
            if schema.table_name in refined and schema.table_name in enriched_map:
                enriched_map[schema.table_name]["relationships"] = refined[schema.table_name]
                await store.update_enriched_metadata(
                    database_id=db_id,
                    table_name=schema.table_name,
                    enriched_metadata=enriched_map[schema.table_name]
                )

        # Persist database-level context
        await store.update_database_context(db_id, db_context_result.model_dump())

    except Exception as e:
        print_warning(f"Cross-table relationship analysis failed: {e}")

    return enriched_count


# Create Typer app
app = typer.Typer(
    name="urim",
    help="urimai - Ask questions about your databases (SQLite, CSV) using AI",
    add_completion=False,
)


# ============================================================================
# Default Command (Interactive Chat)
# ============================================================================


@app.callback(invoke_without_command=True)
def default_callback(ctx: typer.Context):
    """urimai - Ask questions about your databases using AI."""
    # Setup gate: auto-run wizard if not configured (skip for setup/--help and env-var users)
    if ctx.invoked_subcommand not in ("setup", None) or (
        ctx.invoked_subcommand is None and "--help" not in sys.argv
    ):
        if not is_setup_complete() and not _has_env_api_keys():
            print_info("First-time setup required. Launching setup wizard...\n")
            from urimai.setup_wizard import run_setup_wizard
            run_setup_wizard()
            if not is_setup_complete():
                raise typer.Exit(0)

    # If a subcommand was invoked (init, list, etc.), do nothing
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand provided, show help
    print_info("urimai - Interactive Database Chat\n")
    print_info("Usage:")
    print_info("  urim chat <database_name>  Start interactive chat session")
    print_info("  urim init <path>           Register SQLite database or CSV file")
    print_info("  urim list                  List registered databases")
    print_info("  urim sync <name>           Re-sync database schema")
    print_info("  urim config                View/modify settings")
    print_info("  urim setup                 Run setup wizard")
    print_info("\nFor more help: urim --help")


# ============================================================================
# Chat Command (Interactive Session)
# ============================================================================


@app.command()
def chat(
    db_name: Annotated[str, typer.Argument(help="Database name for interactive session")],
):
    """Start interactive chat session with a database."""
    asyncio.run(run_interactive_session(db_name))


# ============================================================================
# Setup Command
# ============================================================================


@app.command()
def setup():
    """Run the setup wizard to configure urimai."""
    from urimai.setup_wizard import run_setup_wizard
    run_setup_wizard()


# ============================================================================
# Init Command
# ============================================================================


@app.command()
def init(
    db_path: Annotated[Path, typer.Argument(help="Path to SQLite database or CSV file")],
    name: Annotated[
        Optional[str],
        typer.Option(help="Custom name for the database (default: filename)"),
    ] = None,
    table_name: Annotated[
        Optional[str],
        typer.Option(help="Table name for CSV import (default: LLM-suggested)"),
    ] = None,
    delimiter: Annotated[
        str,
        typer.Option(help="CSV delimiter character (default: comma)"),
    ] = ',',
    encoding: Annotated[
        str,
        typer.Option(help="CSV file encoding (default: utf-8)"),
    ] = 'utf-8',
):
    """Initialize and register a new database (SQLite or CSV)."""
    async def _init():
        try:
            # Resolve path
            db_path_resolved = db_path.resolve()

            # Check if file exists
            if not db_path_resolved.exists():
                print_error(f"File not found: {db_path_resolved}")
                raise typer.Exit(1)

            # Check if this is a CSV file
            from urimai.core.csv_ingestion import is_csv_file, create_sqlite_from_csv, CSVIngestionError

            is_csv = is_csv_file(db_path_resolved)

            # If CSV, convert to SQLite first
            if is_csv:
                print_step("📊", f"CSV file detected: {db_path_resolved.name}")
                print_info("Starting LLM-powered schema inference and ingestion...")

                with create_progress() as progress:
                    task = progress.add_task(
                        "Analyzing CSV and inferring schema with LLM...",
                        total=None,
                    )

                    try:
                        # Create SQLite from CSV
                        sqlite_path, ingestion_info = await create_sqlite_from_csv(
                            csv_path=db_path_resolved,
                            output_dir=CSV_DATABASES_DIR,
                            table_name=table_name,
                            delimiter=delimiter,
                            encoding=encoding,
                        )

                        progress.update(
                            task,
                            description=f"CSV ingested: {ingestion_info['total_rows']} rows",
                        )

                    except CSVIngestionError as e:
                        print_error("CSV ingestion failed")
                        # Print full error details to console (includes traceback from CSVIngestionError)
                        print(f"\n{str(e)}", file=sys.stderr)
                        raise typer.Exit(1)

                # Show ingestion results
                print_success(
                    f"CSV converted to SQLite: {sqlite_path.name}"
                )
                print_info(
                    f"Table: {ingestion_info['table_name']} | "
                    f"Rows: {ingestion_info['total_rows']} | "
                    f"Columns: {ingestion_info['num_columns']}"
                )

                # Show inferred schema
                inferred = ingestion_info['inferred_schema']
                print_panel(
                    f"**LLM Schema Inference (Confidence: {inferred.confidence})**\n\n"
                    + "\n".join([
                        f"• {col.column_name}: {col.sqlite_type} - {col.detected_pattern}"
                        for col in inferred.columns[:10]  # Show first 10
                    ])
                    + (f"\n• ... and {len(inferred.columns) - 10} more columns" if len(inferred.columns) > 10 else ""),
                    title="Inferred Schema"
                )

                # Use the SQLite database for registration
                db_path_resolved = sqlite_path

            # Determine database name
            db_name = name if name else db_path_resolved.stem

            print_step("🔍", f"Registering database: {db_name}")

            # Initialize metadata store
            store = MetadataStore()
            await store.initialize()

            # Check if database already registered
            existing_db = await store.get_database(db_name)
            if existing_db:
                print_warning(f"Database '{db_name}' is already registered. Re-registering...")

                # Delete old CSV-derived SQLite file if it exists
                # Check by database name (safer than tracking source type)
                csv_db_path = CSV_DATABASES_DIR / f"{db_path_resolved.stem}.db"
                if csv_db_path.exists():
                    csv_db_path.unlink()
                    print_info(f"Removed old CSV-derived database: {csv_db_path.name}")

                # Delete from metadata store (cascades to schemas/profiles/reports)
                await store.delete_database(db_name)
                print_success("Old database metadata removed")

            # Test connection
            print_step("🔌", "Testing connection...")
            db_manager = DatabaseManager(db_path_resolved)
            if not db_manager.test_connection():
                print_error("Failed to connect to database")
                raise typer.Exit(1)
            print_success("Connection successful")

            # Get sample_rows from settings
            sample_rows_str = await store.get_setting("sample_rows")
            sample_rows = (
                int(sample_rows_str) if sample_rows_str else Config.DEFAULT_SAMPLE_ROWS
            )

            # Extract metadata
            with create_progress() as progress:
                # Get table count
                table_names = db_manager.get_table_names()
                num_tables = len(table_names)

                task = progress.add_task(
                    f"Extracting metadata ({num_tables} tables found)...",
                    total=None,
                )

                # Register database
                db_info = DatabaseInfo(
                    name=db_name,
                    path=str(db_path_resolved),
                )
                db_id = await store.add_database(db_info)

                progress.update(task, description="Extracting schema and sample data...")

                # Extract schemas
                extractor = SchemaExtractor(db_manager)
                schemas = extractor.extract_all_schemas(db_id, sample_rows=sample_rows)

                progress.update(
                    task,
                    description=f"Storing metadata for {len(schemas)} tables...",
                )

                # Store schemas
                for schema in schemas:
                    await store.add_schema(schema)

                # Enrich schemas with LLM-generated descriptions
                progress.update(task, description=f"Enriching schemas (0/{len(schemas)})...")
                from urimai.agents.enrichment_agent import SchemaEnrichmentAgent
                enrichment_agent = SchemaEnrichmentAgent()

                enriched_count = await _enrich_schemas(
                    schemas, extractor, enrichment_agent, store, db_id, progress, task
                )

            print_success(
                f"Database '{db_name}' registered successfully with {len(schemas)} tables ({enriched_count}/{len(schemas)} enriched)"
            )
            print_info(
                f"Schema extracted with {sample_rows} sample rows per table"
            )
            print_info(
                "Next steps:\n"
                f"  1. Use 'urim chat {db_name}' to start interactive chat\n"
                f"  2. Use 'urim sync {db_name}' to refresh schema if source changes"
            )

        except typer.Exit:
            raise
        except Exception as e:
            print_error(f"Failed to initialize database: {str(e)}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)

    asyncio.run(_init())


# ============================================================================
# List Command
# ============================================================================


@app.command()
def list():
    """List all registered databases."""
    async def _list():
        try:
            # Initialize metadata store
            store = MetadataStore()
            await store.initialize()

            # Get all databases
            databases = await store.list_databases()

            if not databases:
                print_info("No databases registered yet. Use 'urim init' to register a database.")
                return

            # Convert to dicts for display
            db_dicts = [
                {
                    "name": db.name,
                    "path": db.path,
                    "last_synced_at": db.last_synced_at,
                }
                for db in databases
            ]

            print_databases(db_dicts)

        except Exception as e:
            print_error(f"Failed to list databases: {str(e)}")
            raise typer.Exit(1)

    asyncio.run(_list())


# ============================================================================
# Config Command
# ============================================================================


@app.command()
def config(
    ctx: typer.Context,
    key: Annotated[Optional[str], typer.Argument(help="Config key (dot-notation, e.g. provider.default)")] = None,
    value: Annotated[Optional[str], typer.Argument(help="Value to set")] = None,
    reset: Annotated[bool, typer.Option("--reset", help="Reset config to defaults")] = False,
    path: Annotated[bool, typer.Option("--path", help="Show config/data directory paths")] = False,
):
    """View or modify configuration settings.

    \b
    Examples:
        urim config                          Show all settings
        urim config provider.default openai  Set default provider
        urim config settings.query_timeout 120
        urim config --reset                  Reset to defaults
        urim config --path                   Show directory paths
    """
    from urimai.config import load_config, save_config, URIMAI_HOME, CONFIG_FILE, METADATA_DB, CSV_DATABASES_DIR, DEFAULT_CONFIG

    if path:
        print_info(f"Home directory:   {URIMAI_HOME}")
        print_info(f"Config file:      {CONFIG_FILE}")
        print_info(f"Metadata DB:      {METADATA_DB}")
        print_info(f"CSV databases:    {CSV_DATABASES_DIR}")
        return

    if reset:
        save_config(DEFAULT_CONFIG)
        print_success("Configuration reset to defaults")
        return

    data = load_config()

    # Set mode: urim config <key> <value>
    if key and value is not None:
        # Integer coercion for known int fields
        int_fields = {"sample_rows", "query_timeout", "max_retry_attempts", "max_plan_revisions"}
        parts = key.split(".")
        if len(parts) == 2:
            section, field = parts
            if section in data:
                coerced = int(value) if field in int_fields else value
                data[section][field] = coerced
                save_config(data)
                print_success(f"{key} = {coerced}")
            else:
                print_error(f"Unknown section: {section}")
                raise typer.Exit(1)
        else:
            print_error("Use dot-notation: section.key (e.g. provider.default, settings.query_timeout)")
            raise typer.Exit(1)
        return

    if key and value is None:
        print_error("Usage: urim config <key> <value>")
        raise typer.Exit(1)

    # Show mode: display all settings
    from rich.table import Table as RichTable
    from urimai.utils.display import console

    table = RichTable(title="urimai Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    for section_name, section in sorted(data.items()):
        if isinstance(section, dict):
            for k, v in sorted(section.items()):
                table.add_row(f"{section_name}.{k}", str(v))
        else:
            table.add_row(section_name, str(section))

    console.print(table)
    console.print(f"\n[dim]Config file: {CONFIG_FILE}[/dim]")


# ============================================================================
# Sync Command
# ============================================================================


@app.command()
def sync(
    db_name: Annotated[str, typer.Argument(help="Name of the registered database")],
):
    """Re-sync database schema metadata."""
    async def _sync():
        try:
            # Initialize metadata store
            store = MetadataStore()
            await store.initialize()

            # Get database
            db_info = await store.get_database(db_name)
            if not db_info:
                print_error(f"Database '{db_name}' not found. Use 'urim list' to see registered databases.")
                raise typer.Exit(1)

            print_step("🔄", f"Syncing database '{db_name}'...")

            # Check if database file still exists
            db_path = Path(db_info.path)
            if not db_path.exists():
                print_error(f"Database file not found: {db_path}")
                raise typer.Exit(1)

            # Test connection
            db_manager = DatabaseManager(db_path)
            if not db_manager.test_connection():
                print_error("Failed to connect to database")
                raise typer.Exit(1)

            # Get sample_rows from settings
            sample_rows_str = await store.get_setting("sample_rows")
            sample_rows = (
                int(sample_rows_str) if sample_rows_str else Config.DEFAULT_SAMPLE_ROWS
            )

            # Delete existing schemas
            await store.delete_schemas(db_info.id)

            # Extract metadata
            with create_progress() as progress:
                table_names = db_manager.get_table_names()
                num_tables = len(table_names)

                task = progress.add_task(
                    f"Re-extracting metadata ({num_tables} tables)...",
                    total=None,
                )

                extractor = SchemaExtractor(db_manager)
                schemas = extractor.extract_all_schemas(db_info.id, sample_rows=sample_rows)

                progress.update(
                    task,
                    description=f"Storing updated metadata for {len(schemas)} tables...",
                )

                # Store new schemas
                for schema in schemas:
                    await store.add_schema(schema)

                # Enrich schemas with LLM-generated descriptions
                progress.update(task, description=f"Enriching schemas (0/{len(schemas)})...")
                from urimai.agents.enrichment_agent import SchemaEnrichmentAgent
                enrichment_agent = SchemaEnrichmentAgent()

                enriched_count = await _enrich_schemas(
                    schemas, extractor, enrichment_agent, store, db_info.id, progress, task
                )

                # Update last_synced_at
                await store.update_last_synced(db_info.id)

            print_success(f"Database '{db_name}' synced successfully with {len(schemas)} tables ({enriched_count}/{len(schemas)} enriched)")
            print_info(f"Schema extracted with {sample_rows} sample rows per table")

        except typer.Exit:
            raise
        except Exception as e:
            print_error(f"Failed to sync database: {str(e)}")
            import traceback
            traceback.print_exc()
            raise typer.Exit(1)

    asyncio.run(_sync())


# ============================================================================
# Export Command
# ============================================================================


@app.command()
def export(
    db_name: Annotated[str, typer.Argument(help="Database name to export")],
    format: Annotated[str, typer.Option("--format", "-f", help="Output format: xlsx or markdown")] = "xlsx",
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output file path")] = None,
    include_sample_data: Annotated[bool, typer.Option("--include-sample-data", help="Include sample data rows")] = False,
    include_profile: Annotated[bool, typer.Option(help="Include column profile statistics")] = True,
    include_quality: Annotated[bool, typer.Option(help="Include quality report data")] = True,
):
    """Export data dictionary for a registered database."""
    async def _export():
        from urimai.core.export import gather_export_data, export_to_excel, export_to_markdown

        store = MetadataStore()
        await store.initialize()

        db_info = await store.get_database(db_name)
        if not db_info:
            print_error(f"Database '{db_name}' not found. Use 'urim list' to see registered databases.")
            raise typer.Exit(1)

        if format not in ("xlsx", "markdown"):
            print_error("Invalid format. Use 'xlsx' or 'markdown'.")
            raise typer.Exit(1)

        print_step("📦", f"Exporting data dictionary for '{db_name}'...")

        data = await gather_export_data(db_name, include_profile, include_quality, include_sample_data)

        ext = "xlsx" if format == "xlsx" else "md"
        out = output or Path(f"{db_name}_data_dictionary.{ext}")

        if format == "xlsx":
            export_to_excel(data, out)
        else:
            export_to_markdown(data, out)

        print_success(f"Data dictionary exported to {out}")

    asyncio.run(_export())


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Main entry point for CLI."""
    # Pre-parse --model flag (position-independent)
    args = sys.argv[1:]
    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            Config._provider_override = args[idx + 1]
            sys.argv = [sys.argv[0]] + args[:idx] + args[idx + 2:]

    try:
        app()
    except KeyboardInterrupt:
        print_info("\nOperation cancelled by user")
        raise typer.Exit(0)


if __name__ == "__main__":
    main()
