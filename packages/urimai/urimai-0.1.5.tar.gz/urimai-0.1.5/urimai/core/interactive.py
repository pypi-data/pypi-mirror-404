"""Interactive REPL session for conversational database queries."""

import asyncio
from typing import Any
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from urimai.storage.metadata_store import MetadataStore
from urimai.storage.models import QueryPlan, ConversationalResponse, SuccessAnswer, RetryWithFeedback, UsageStats
from urimai.core.db_manager import DatabaseManager
from urimai.core.schema_extractor import SchemaExtractor
from urimai.core.query_executor import QueryExecutor
from urimai.core.chat_session import ChatSession
from urimai.agents.query_agent import QueryGenerationAgent
from urimai.agents.analysis_agent import ResultAnalysisAgent
from urimai.agents.query_planner_agent import QueryPlannerAgent
from urimai.core.plan_executor import PlanExecutor
from urimai.utils.display import (
    print_success,
    print_error,
    print_warning,
    print_info,
    print_step,
    print_sql,
    print_panel,
    print_table,
    print_welcome_banner,
    print_conversation_history,
    print_schema_info,
    print_database_overview,
    print_table_detail,
    print_schema_graph,
    print_table_list,
    print_table_profile,
    print_quality_report,
    print_usage,
    print_help,
    print_goodbye,
    pipeline_status,
    print_sub,
    console,
)
from urimai.config import Config


async def run_interactive_session(db_name: str) -> None:
    """Run interactive chat session for a database.

    Args:
        db_name: Name of the registered database
    """
    try:
        # Validate API key
        try:
            Config.validate()
        except RuntimeError as e:
            print_error(str(e))
            return

        # Initialize metadata store
        store = MetadataStore()
        await store.initialize()

        # Get database
        db_info = await store.get_database(db_name)
        if not db_info:
            print_error(f"Database '{db_name}' not found. Use 'urim init <db_path>' first.")
            return

        # Initialize context manager (unified source of database context)
        from urimai.core.context_manager import ContextManager
        context_manager = ContextManager(db_name)
        await context_manager.initialize()

        # Load schemas
        schemas = await context_manager.get_schemas()
        if not schemas:
            print_error(f"No schema metadata found for '{db_name}'. Try re-running init.")
            return

        # Initialize components
        db_manager = DatabaseManager(db_info.path)
        query_executor = QueryExecutor(db_manager)

        # Initialize agents
        query_agent = QueryGenerationAgent()
        analysis_agent = ResultAnalysisAgent()
        planner_agent = QueryPlannerAgent()

        # Create chat session
        chat_session = ChatSession(db_name)

        # Display welcome banner
        table_count = len(schemas)
        print_welcome_banner(db_name, table_count)

        # Create prompt session with history
        session = PromptSession(history=InMemoryHistory())

        # Main REPL loop
        while True:
            try:
                # Get user input
                user_input = await session.prompt_async("You: ", multiline=False)
                user_input = user_input.strip()

                # Skip empty input
                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    command = user_input.lower()

                    if command in ["/exit", "/quit"]:
                        print_goodbye()
                        break

                    elif command == "/help":
                        print_help()
                        continue

                    elif command == "/schema" or command.startswith("/schema "):
                        parts = user_input.split()
                        if len(parts) == 1:
                            # No args: show overview
                            db_context = await context_manager.get_database_context()
                            print_database_overview(db_context, schemas)
                        elif parts[1].strip().lower() == "graph":
                            print_schema_graph(schemas)
                        elif parts[1].strip().lower() == "all":
                            # Show detail for every table
                            for s in schemas:
                                print_table_detail(s)
                        else:
                            # One or more table names
                            table_names = [p.strip().lower() for p in parts[1:]]
                            matching = [s for s in schemas if s.table_name.lower() in table_names]
                            if matching:
                                for s in matching:
                                    print_table_detail(s)
                            else:
                                not_found = ", ".join(parts[1:])
                                print_warning(f"Table(s) '{not_found}' not found. Use /schema to see all tables.")
                        continue

                    elif command == "/tables":
                        table_names = [s.table_name for s in schemas]
                        print_table_list(table_names)
                        continue

                    elif command == "/history":
                        query_results = chat_session.get_recent_queries(limit=20)
                        print_conversation_history(query_results)
                        continue

                    elif command == "/clear":
                        chat_session.clear_history()
                        print_success("Conversation history cleared")
                        continue

                    elif command.startswith("/profile"):
                        # Handle /profile <table_name>
                        parts = user_input.split(maxsplit=1)
                        if len(parts) < 2:
                            print_warning("Usage: /profile <table_name>")
                            continue

                        table_name = parts[1].strip()
                        table_names = [s.table_name for s in schemas]

                        if table_name not in table_names:
                            print_error(f"Table '{table_name}' not found. Use /tables to see available tables.")
                            continue

                        # Profile the table
                        await handle_profile_command(
                            table_name=table_name,
                            db_info=db_info,
                            store=store,
                            schemas=schemas,
                        )
                        continue

                    elif command.startswith("/export"):
                        parts = user_input.split()
                        # Parse inline flags
                        fmt = "xlsx"
                        out_path = None
                        inc_sample = False
                        inc_profile = True
                        inc_quality = True
                        i = 1
                        while i < len(parts):
                            p = parts[i]
                            if p in ("--format", "-f") and i + 1 < len(parts):
                                fmt = parts[i + 1]
                                i += 2
                            elif p in ("--output", "-o") and i + 1 < len(parts):
                                out_path = parts[i + 1]
                                i += 2
                            elif p == "--include-sample-data":
                                inc_sample = True
                                i += 1
                            elif p == "--no-include-profile":
                                inc_profile = False
                                i += 1
                            elif p == "--no-include-quality":
                                inc_quality = False
                                i += 1
                            elif p == "markdown":
                                fmt = "markdown"
                                i += 1
                            elif p == "xlsx":
                                fmt = "xlsx"
                                i += 1
                            else:
                                i += 1

                        await handle_export_command(
                            db_name=db_name,
                            fmt=fmt,
                            output_path=out_path,
                            include_sample_data=inc_sample,
                            include_profile=inc_profile,
                            include_quality=inc_quality,
                        )
                        continue

                    elif command.startswith("/quality"):
                        # Handle /quality <table_name>
                        parts = user_input.split(maxsplit=1)
                        if len(parts) < 2:
                            print_warning("Usage: /quality <table_name>")
                            continue

                        table_name = parts[1].strip()
                        table_names = [s.table_name for s in schemas]

                        if table_name not in table_names:
                            print_error(f"Table '{table_name}' not found. Use /tables to see available tables.")
                            continue

                        # Assess data quality
                        await handle_quality_command(
                            table_name=table_name,
                            db_info=db_info,
                            store=store,
                            schemas=schemas,
                        )
                        continue

                    else:
                        print_warning(f"Unknown command: {command}. Type /help for available commands.")
                        continue

                # Handle question (not a command)
                console.print()  # Blank line for spacing
                await handle_question(
                    question=user_input,
                    chat_session=chat_session,
                    context_manager=context_manager,
                    query_agent=query_agent,
                    analysis_agent=analysis_agent,
                    query_executor=query_executor,
                    planner_agent=planner_agent,
                )
                console.print()  # Blank line after response

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                console.print()
                confirm = await session.prompt_async("Exit? (y/n): ")
                if confirm.lower() in ["y", "yes"]:
                    print_goodbye()
                    break

            except EOFError:
                # Handle Ctrl+D
                print_goodbye()
                break

    except Exception as e:
        print_error(f"Session error: {str(e)}")
        import traceback
        traceback.print_exc()


async def handle_question(
    question: str,
    chat_session: ChatSession,
    context_manager,
    query_agent: QueryGenerationAgent,
    analysis_agent: ResultAnalysisAgent,
    query_executor: QueryExecutor,
    planner_agent: QueryPlannerAgent | None = None,
) -> None:
    """Handle a user question in the interactive session.

    Args:
        question: User's question
        chat_session: Current chat session
        context_manager: ContextManager with database context
        query_agent: Query generation agent
        analysis_agent: Result analysis agent
        query_executor: Query executor
        planner_agent: Query planner agent for complex queries
    """
    # Add question to session history
    chat_session.add_user_message(question)

    # Get conversation context
    conversation_context = chat_session.get_conversation_context()

    # Track token usage across all agent calls
    usage_stats = UsageStats()

    # Multi-step query loop with retry logic
    max_attempts = Config.MAX_RETRY_ATTEMPTS
    feedback = None

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print_step("🔄", f"Retry attempt {attempt}/{max_attempts}...")

        # Step 1: Table selection + context building
        max_api_retries = 2

        # Get rich context (with table selection for large DBs)
        async with pipeline_status("Selecting relevant tables..."):
            for api_retry in range(max_api_retries):
                try:
                    schema_info = await context_manager.format_context_for_query_agent(query=question)
                    break
                except Exception as e:
                    error_msg = str(e)
                    if ("503" in error_msg or "overloaded" in error_msg.lower() or "UNAVAILABLE" in error_msg):
                        if api_retry < max_api_retries - 1:
                            await asyncio.sleep(3)
                        else:
                            print_error("API temporarily unavailable. Please wait a moment and try your question again.")
                            return
                    else:
                        raise

        # Capture table selection usage
        if context_manager._selection_agent:
            usage_stats.add(context_manager._selection_agent.last_usage)

        # Display table selection results
        if not schema_info.get("table_selection_skipped"):
            selected = schema_info.get("selected_tables", [])
            print_step("🗂️ ", f"[bold]Selected {len(selected)} tables:[/bold] {', '.join(selected)}")

            for detail in schema_info.get("expansion_details", []):
                print_sub(detail)
        else:
            table_count = len(schema_info.get("tables", {}))
            print_step("🗂️ ", f"[bold]Using all {table_count} tables[/bold]")

        # Step 2: Classify complexity and route
        if planner_agent:
            async with pipeline_status("Assessing query complexity..."):
                for api_retry in range(max_api_retries):
                    try:
                        complexity = await planner_agent.classify_complexity(question, schema_info)
                        break
                    except Exception as e:
                        error_msg = str(e)
                        if ("503" in error_msg or "overloaded" in error_msg.lower() or "UNAVAILABLE" in error_msg):
                            if api_retry < max_api_retries - 1:
                                await asyncio.sleep(3)
                            else:
                                print_error("API temporarily unavailable. Please wait a moment and try your question again.")
                                return
                        else:
                            raise
        else:
            complexity = None

        if planner_agent:
            usage_stats.add(planner_agent.last_usage)

        if complexity and complexity.is_complex:
            print_step("🧠", f"[bold]Complex query detected[/bold] (~{complexity.estimated_steps} steps)")
            print_sub(complexity.reasoning)

            # Execute via multi-step plan
            plan_exec = PlanExecutor(
                planner=planner_agent,
                query_agent=query_agent,
                analysis_agent=analysis_agent,
                query_executor=query_executor,
                context_manager=context_manager,
            )

            analysis_result, query_plan, exec_result, plan_usage = await plan_exec.execute_plan(
                question=question,
                schema_info=schema_info,
                conversation_context=conversation_context if conversation_context else None,
            )
            usage_stats.add(plan_usage)

            if analysis_result is None:
                chat_session.add_assistant_response(
                    "Failed to generate a satisfactory answer via multi-step planning."
                )
                print_usage(usage_stats)
                return

            # Handle retry feedback from analysis
            if isinstance(analysis_result, RetryWithFeedback):
                print_warning(f"Results need improvement: {analysis_result.retry_reason}")
                chat_session.add_assistant_response(analysis_result.retry_reason)
                print_usage(usage_stats)
                return

            # Display answer
            success_answer = analysis_result
            console.print()
            print_panel(
                success_answer.answer,
                f"Answer (confidence: {success_answer.confidence:.0%})",
                style="green",
            )
            chat_session.add_assistant_response(
                success_answer.answer,
                query_plan.sql_query if query_plan else None,
                exec_result.row_count if exec_result else 0,
            )
            if exec_result and exec_result.data:
                console.print()
                print_table(exec_result.data, max_rows=20)
            print_usage(usage_stats)
            return

        else:
            if complexity:
                print_step("⚡", "[bold]Simple query[/bold] — direct generation")

        # Simple query path (existing one-shot logic)
        # Build question with context
        question_with_context = question
        if conversation_context and attempt == 1:
            question_with_context = f"{conversation_context}\nCurrent question: {question}"

        # Generate query (with API error handling)
        async with pipeline_status("Generating SQL query..."):
            for api_retry in range(max_api_retries):
                try:
                    query_result = await query_agent.generate_query(
                        question_with_context, schema_info, feedback
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_msg = str(e)
                    if ("503" in error_msg or "overloaded" in error_msg.lower() or "UNAVAILABLE" in error_msg):
                        if api_retry < max_api_retries - 1:
                            await asyncio.sleep(3)
                        else:
                            print_error("API temporarily unavailable. Please wait a moment and try your question again.")
                            return
                    else:
                        raise  # Re-raise if it's a different error

        usage_stats.add(query_agent.last_usage)

        # Check if agent returned conversational response
        if isinstance(query_result, ConversationalResponse):
            chat_session.add_assistant_response(query_result.message)
            print_panel(query_result.message, "Response", style="yellow")
            print_usage(usage_stats)
            return

        # Extract query plan
        query_plan: QueryPlan = query_result
        print_step("🔨", "[bold]SQL query generated[/bold]")
        print_sql(query_plan.sql_query)
        print_sub(query_plan.explanation)

        # Step 3: Validate query
        is_valid, validation_error = query_executor.validate_query(query_plan.sql_query)
        if is_valid:
            print_step("✅", "Query validated")

        if not is_valid:
            print_error(f"Query validation failed: {validation_error}")
            if attempt < max_attempts:
                feedback = validation_error
                continue
            else:
                chat_session.add_assistant_response(
                    f"Failed to generate valid query: {validation_error}"
                )
                return

        # Step 4: Execute query
        async with pipeline_status("Executing query..."):
            exec_result = await query_executor.execute(query_plan.sql_query)

        if not exec_result.success:
            print_error(f"Query execution failed: {exec_result.error}")
            if attempt < max_attempts:
                feedback = exec_result.error
                continue
            else:
                chat_session.add_assistant_response(
                    f"Query failed: {exec_result.error}"
                )
                return

        print_step("⚙️ ", f"[bold]Query returned {exec_result.row_count} rows[/bold]")

        # Step 5: Analyze results
        # Get database context and analyze results (with API error handling)
        async with pipeline_status("Analyzing results..."):
            for api_retry in range(max_api_retries):
                try:
                    db_context = await context_manager.get_database_context()
                    analysis_result = await analysis_agent.analyze_results(
                        question=question,
                        sql_query=query_plan.sql_query,
                        execution_success=exec_result.success,
                        results=exec_result.data,
                        error=exec_result.error,
                        db_context=db_context,
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_msg = str(e)
                    if ("503" in error_msg or "overloaded" in error_msg.lower() or "UNAVAILABLE" in error_msg):
                        if api_retry < max_api_retries - 1:
                            await asyncio.sleep(3)
                        else:
                            print_error("API temporarily unavailable. Please wait a moment and try again.")
                            return
                    else:
                        raise  # Re-raise if it's a different error

        usage_stats.add(analysis_agent.last_usage)

        # Check if retry needed
        if isinstance(analysis_result, RetryWithFeedback):
            print_warning(f"Results need improvement: {analysis_result.retry_reason}")
            if attempt < max_attempts:
                feedback = f"{analysis_result.retry_reason}\nSuggestion: {analysis_result.suggested_fix}"
                continue
            else:
                chat_session.add_assistant_response(
                    analysis_result.retry_reason,
                    query_plan.sql_query,
                    exec_result.row_count,
                )
                print_error("Maximum retry attempts reached")
                return

        # Success! Display answer
        success_answer: SuccessAnswer = analysis_result
        console.print()
        print_panel(
            success_answer.answer,
            f"Answer (confidence: {success_answer.confidence:.0%})",
            style="green",
        )

        # Add to session history
        chat_session.add_assistant_response(
            success_answer.answer,
            query_plan.sql_query,
            exec_result.row_count,
        )

        # Display data table if results exist
        if exec_result.data:
            console.print()
            print_table(exec_result.data, max_rows=20)

        print_usage(usage_stats)
        return

    # If we exhausted all attempts
    print_error("Failed to generate satisfactory results after maximum attempts")
    chat_session.add_assistant_response(
        "I apologize, but I couldn't generate a satisfactory answer after multiple attempts."
    )
    print_usage(usage_stats)


async def handle_profile_command(
    table_name: str,
    db_info: Any,
    store: MetadataStore,
    schemas: list[Any],
) -> None:
    """Handle the /profile command to generate table profile.

    Args:
        table_name: Name of the table to profile
        db_info: Database information
        store: Metadata store
        schemas: List of SchemaInfo objects
    """
    from urimai.core.profiling.column_profiler import profile_table
    from urimai.core.profiling.role_classifier import enrich_profile_with_roles
    from urimai.utils.display import create_progress

    try:
        # Check if profile already exists
        existing_profile = await store.get_table_profile(db_info.id, table_name)

        if existing_profile:
            print_info(f"Using cached profile from {existing_profile.created_at.split('T')[0]}")
            print_table_profile(existing_profile)
            console.print("[dim]Tip: Delete the metadata.db file to regenerate profiles[/dim]")
            return

        # Generate new profile with progress indicator
        with create_progress() as progress:
            task = progress.add_task(f"Profiling table '{table_name}'...", total=None)

            # Find the schema for this table
            schema_info = next((s for s in schemas if s.table_name == table_name), None)
            if not schema_info:
                raise ValueError(f"Schema not found for table '{table_name}'")

            # Profile the table
            table_profile = await profile_table(
                db_path=db_info.path,
                table_name=table_name,
                database_id=db_info.id,
                schema_info=schema_info,
            )

            # Enrich with role classification
            db_manager = DatabaseManager(db_info.path)
            query = f"SELECT * FROM {table_name} LIMIT 100"
            sample_rows = db_manager.execute_query(query)

            for col_profile in table_profile.columns:
                col_name = col_profile.column_name
                sample_values = [row.get(col_name) for row in sample_rows]
                enrich_profile_with_roles(col_profile, sample_values)

            progress.update(task, completed=True)

        # Save to store
        await store.save_table_profile(table_profile)

        # Display
        print_success(f"Profile generated for table '{table_name}'")
        console.print()
        print_table_profile(table_profile)

    except Exception as e:
        print_error(f"Failed to profile table: {str(e)}")
        import traceback
        traceback.print_exc()


async def handle_quality_command(
    table_name: str,
    db_info: Any,
    store: MetadataStore,
    schemas: list[Any],
) -> None:
    """Handle the /quality command with agentic intelligence.

    Args:
        table_name: Name of the table to assess
        db_info: Database information
        store: Metadata store
        schemas: List of SchemaInfo objects
    """
    from urimai.agents.schema_context_agent import SchemaContextAgent
    from urimai.agents.role_classification_agent import RoleClassificationAgent
    from urimai.agents.quality_generation_agent import QualityGenerationAgent
    from urimai.agents.quality_interpreter_agent import QualityInterpreterAgent
    from urimai.utils.display import create_progress

    try:
        print_step("🤖", "Using AI agents for intelligent quality assessment...")
        console.print()

        # Step 1: Understand the database holistically
        print_step("1️⃣ ", "Analyzing database context...")

        db_manager = DatabaseManager(db_info.path)

        # Gather enriched metadata
        enriched_metadata = {}
        sample_data = {}
        for schema in schemas:
            if schema.enriched_metadata:
                enriched_metadata[schema.table_name] = schema.enriched_metadata

            # Get sample data
            query = f"SELECT * FROM {schema.table_name} LIMIT 10"
            samples = db_manager.execute_query(query)
            sample_data[schema.table_name] = samples

        # Run Schema Context Agent
        context_agent = SchemaContextAgent()
        db_context = await context_agent.analyze_database(
            schemas=schemas,
            enriched_metadata=enriched_metadata,
            sample_data=sample_data,
        )

        print_success(f"Domain understood: {db_context.domain}")
        console.print(f"[dim]{db_context.purpose}[/dim]")
        console.print()

        # Step 2: Get/generate profile for target table
        print_step("2️⃣ ", f"Profiling table '{table_name}'...")

        table_profile = await store.get_table_profile(db_info.id, table_name)

        if not table_profile:
            schema_info = next((s for s in schemas if s.table_name == table_name), None)
            if not schema_info:
                raise ValueError(f"Schema not found for table '{table_name}'")

            from urimai.core.profiling.column_profiler import profile_table

            table_profile = await profile_table(
                db_path=db_info.path,
                table_name=table_name,
                database_id=db_info.id,
                schema_info=schema_info,
            )
            await store.save_table_profile(table_profile)

        print_success("Profile ready")
        console.print()

        # Step 3: Classify column roles with context
        print_step("3️⃣ ", "Classifying column roles...")

        table_purpose = enriched_metadata.get(table_name, {}).get("table_purpose", "")
        table_samples = sample_data.get(table_name, [])

        # Build related tables context
        related_tables = {
            s.table_name: s.enriched_metadata.get("table_purpose", "") if s.enriched_metadata else ""
            for s in schemas if s.table_name != table_name
        }

        role_agent = RoleClassificationAgent()
        table_roles = await role_agent.classify_table(
            table_name=table_name,
            columns=table_profile.columns,
            db_context=db_context,
            table_purpose=table_purpose,
            sample_data=table_samples,
            related_tables=related_tables,
        )

        print_success(f"{len(table_roles.column_roles)} roles classified")
        console.print()

        # Step 4: Generate quality checks dynamically
        print_step("4️⃣ ", "Generating contextual quality checks...")

        quality_gen_agent = QualityGenerationAgent()
        check_plan = await quality_gen_agent.generate_checks(
            table_name=table_name,
            db_context=db_context,
            table_purpose=table_purpose,
            table_roles=table_roles,
            column_profiles=table_profile.columns,
            sample_data=table_samples,
        )

        print_success(f"{len(check_plan.checks)} checks generated")
        console.print(f"[dim]Focus: {', '.join(check_plan.focus_areas)}[/dim]")
        console.print()

        # Step 5: Execute the checks
        print_step("5️⃣ ", "Running quality checks...")

        results = []
        failure_examples = {}

        with create_progress() as progress:
            task = progress.add_task(f"Executing {len(check_plan.checks)} checks...", total=None)

            for check in check_plan.checks:
                try:
                    query_result = db_manager.execute_query(check.sql_query)
                    violations_count = query_result[0].get(list(query_result[0].keys())[0], 0) if query_result else 0

                    passed = violations_count == 0
                    results.append({
                        "check_id": check.check_id,
                        "violations_count": violations_count,
                        "passed": passed,
                    })

                    # Get failure examples if check failed
                    if not passed:
                        # TODO: Get sample rows that fail this check
                        failure_examples[check.check_id] = []

                except Exception as e:
                    # If check fails to execute, mark as error
                    results.append({
                        "check_id": check.check_id,
                        "violations_count": 0,
                        "passed": False,
                        "error": str(e),
                    })

            progress.update(task, completed=True)

        passed_count = sum(1 for r in results if r.get("passed", False))
        print_success(f"{passed_count}/{len(check_plan.checks)} checks passed")
        console.print()

        # Step 6: Interpret results with business context
        print_step("6️⃣ ", "Interpreting results...")

        interpreter_agent = QualityInterpreterAgent()
        interpretation = await interpreter_agent.interpret_results(
            table_name=table_name,
            db_context=db_context,
            checks=check_plan.checks,
            results=results,
            failure_examples=failure_examples,
        )

        print_success("Analysis complete!")
        console.print()

        # Step 7: Display intelligent results
        _display_agentic_quality_report(
            table_name=table_name,
            interpretation=interpretation,
            check_plan=check_plan,
            results=results,
        )

    except Exception as e:
        print_error(f"Failed to assess quality: {str(e)}")
        import traceback
        traceback.print_exc()


def _display_agentic_quality_report(
    table_name: str,
    interpretation: Any,
    check_plan: Any,
    results: list[dict],
) -> None:
    """Display agentic quality report.

    Args:
        table_name: Table name
        interpretation: QualityInterpretation from agent
        check_plan: QualityCheckPlan from agent
        results: List of check results
    """
    from rich.table import Table
    from rich.panel import Panel

    # Header
    score = interpretation.overall_score
    if score >= 90:
        score_color = "green"
        emoji = "✅"
    elif score >= 70:
        score_color = "yellow"
        emoji = "⚠️"
    else:
        score_color = "red"
        emoji = "❌"

    header = f"""[bold]AI Quality Analysis:[/bold] {table_name}
[bold {score_color}]{emoji} Overall Score: {score:.1f}/100[/bold {score_color}]

[bold]Summary:[/bold]
{interpretation.overall_summary}

[bold]Context:[/bold]
{interpretation.context_notes}"""

    console.print(Panel(header, border_style=score_color, title="🤖 Intelligent Assessment"))
    console.print()

    # Critical Findings
    if interpretation.critical_findings:
        console.print("[bold red]🚨 Critical Issues:[/bold red]")
        for finding in interpretation.critical_findings:
            console.print(f"  [red]✗[/red] {finding.issue}")
            console.print(f"    [dim]Impact: {finding.business_impact}[/dim]")
            console.print(f"    [dim]Priority: {finding.priority}/10[/dim]")
        console.print()

    # Warnings
    if interpretation.warnings:
        console.print("[bold yellow]⚠️  Warnings:[/bold yellow]")
        for finding in interpretation.warnings[:5]:
            console.print(f"  [yellow]⚠[/yellow] {finding.issue}")
            console.print(f"    [dim]{finding.business_impact}[/dim]")
        console.print()

    # Acceptable Issues
    if interpretation.acceptable_issues:
        console.print(f"[bold blue]ℹ️  Acceptable Issues:[/bold blue] {len(interpretation.acceptable_issues)} patterns expected for this domain")
        console.print()

    # Recommendations
    if interpretation.recommendations:
        console.print("[bold green]💡 Recommendations:[/bold green]")
        for rec in interpretation.recommendations[:5]:
            console.print(f"  • {rec.action}")
            console.print(f"    [dim]Why: {rec.reason} (Effort: {rec.effort})[/dim]")
        console.print()


async def handle_export_command(
    db_name: str,
    fmt: str = "xlsx",
    output_path: str | None = None,
    include_sample_data: bool = False,
    include_profile: bool = True,
    include_quality: bool = True,
) -> None:
    """Handle the /export command inside an interactive chat session."""
    from pathlib import Path
    from urimai.core.export import gather_export_data, export_to_excel, export_to_markdown

    if fmt not in ("xlsx", "markdown"):
        print_error("Invalid format. Use 'xlsx' or 'markdown'.")
        return

    try:
        print_step("📦", f"Exporting data dictionary for '{db_name}'...")

        data = await gather_export_data(db_name, include_profile, include_quality, include_sample_data)

        ext = "xlsx" if fmt == "xlsx" else "md"
        out = Path(output_path) if output_path else Path(f"{db_name}_data_dictionary.{ext}")

        if fmt == "xlsx":
            export_to_excel(data, out)
        else:
            export_to_markdown(data, out)

        print_success(f"Data dictionary exported to {out}")

    except Exception as e:
        print_error(f"Export failed: {str(e)}")
        import traceback
        traceback.print_exc()
