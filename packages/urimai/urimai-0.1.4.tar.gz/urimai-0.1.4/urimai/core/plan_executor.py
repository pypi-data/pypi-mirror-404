"""Plan executor - orchestrates multi-step query execution."""

import re
import asyncio
from typing import Any
from urimai.storage.models import (
    ExecutionPlan, SubProblemResult, QueryPlan, ConversationalResponse,
    SuccessAnswer, RetryWithFeedback, PlanRevision, UsageStats,
)
from urimai.agents.query_planner_agent import QueryPlannerAgent
from urimai.agents.query_agent import QueryGenerationAgent
from urimai.agents.analysis_agent import ResultAnalysisAgent
from urimai.core.query_executor import QueryExecutor
from urimai.utils.display import (
    pipeline_status, print_step, print_sub, print_sql,
    print_error, print_warning, print_info, print_panel,
    print_table, print_success, console,
)
from urimai.config import Config


class PlanExecutor:
    """Executes multi-step query plans with live progress display."""

    def __init__(
        self,
        planner: QueryPlannerAgent,
        query_agent: QueryGenerationAgent,
        analysis_agent: ResultAnalysisAgent,
        query_executor: QueryExecutor,
        context_manager,
    ):
        self.planner = planner
        self.query_agent = query_agent
        self.analysis_agent = analysis_agent
        self.query_executor = query_executor
        self.context_manager = context_manager

    async def execute_plan(
        self,
        question: str,
        schema_info: dict[str, Any],
        conversation_context: str | None = None,
    ) -> tuple[SuccessAnswer | RetryWithFeedback | None, QueryPlan | None, Any, UsageStats]:
        """Execute a multi-step plan and return the final answer.

        Returns:
            Tuple of (analysis_result, final_query_plan, exec_result, usage_stats)
            Returns (None, None, None, usage_stats) on unrecoverable failure.
        """
        max_api_retries = 2
        usage_stats = UsageStats()

        # Step 1: Create the plan
        async with pipeline_status("Creating execution plan..."):
            plan = await self._with_api_retry(
                lambda: self.planner.create_plan(question, schema_info),
                max_api_retries,
            )
            usage_stats.add(self.planner.last_usage)
            if plan is None:
                return None, None, None, usage_stats

        # Display the plan
        self._display_plan(plan)

        # Step 2: Execute sub-problems
        completed_results: list[SubProblemResult] = []
        remaining = list(plan.sub_problems)
        max_revisions = Config.MAX_PLAN_REVISIONS
        revisions_used = 0

        while remaining:
            sub_problem = remaining.pop(0)

            # Check dependencies
            completed_ids = {r.sub_problem_id for r in completed_results}
            unmet = [d for d in sub_problem.depends_on if d not in completed_ids]
            if unmet:
                print_warning(f"Skipping {sub_problem.id}: unmet dependencies {unmet}")
                completed_results.append(SubProblemResult(
                    sub_problem_id=sub_problem.id,
                    success=False,
                    error=f"Unmet dependencies: {unmet}",
                ))
                continue

            # Execute this sub-problem
            result = await self._execute_sub_problem(
                sub_problem, schema_info, completed_results
            )
            usage_stats.add(self.query_agent.last_usage)
            completed_results.append(result)

            # Detect data assumption failures even on "successful" queries:
            # Case 1: Query returned 0 rows
            # Case 2: Cardinality/sanity check returned 1 row with count/sum = 0
            if result.success and any(
                kw in (sub_problem.title.lower() + " " + sub_problem.approach.lower())
                for kw in ["sanity", "cardinality", "check", "verify"]
            ):
                is_zero_result = False
                if result.row_count == 0:
                    is_zero_result = True
                elif result.row_count == 1 and result.sample_data:
                    # Single-row result where all numeric values are 0 or None
                    row = result.sample_data[0]
                    values = list(row.values())
                    if all(v in (0, 0.0, None) for v in values):
                        is_zero_result = True

                if is_zero_result:
                    result.success = False
                    result.error = (
                        f"Data assumption failed: {sub_problem.title} returned zero/empty results. "
                        f"The expected data may not exist or the join/filter logic is wrong."
                    )
                    print_warning(f"  {sub_problem.id}: zero result — data assumption may be wrong")

            # If failed, try to revise the plan
            if not result.success and revisions_used < max_revisions:
                async with pipeline_status("Revising plan..."):
                    revision = await self._with_api_retry(
                        lambda: self.planner.revise_plan(
                            plan, sub_problem.id, result.error or "Unknown error",
                            completed_results, schema_info,
                        ),
                        max_api_retries,
                    )

                usage_stats.add(self.planner.last_usage)

                if revision and revision.should_revise:
                    revisions_used += 1
                    print_step("🔄", f"[bold]Plan revised:[/bold] {revision.reason}")

                    # Drop specified steps
                    remaining = [s for s in remaining if s.id not in revision.drop_ids]

                    # Add new/updated steps
                    remaining = revision.updated_sub_problems + remaining
                    self._display_revision(revision)

        # Step 3 & 4: Generate final query, analyze, retry if analysis says to
        max_analysis_retries = Config.MAX_RETRY_ATTEMPTS
        analysis_feedback = None

        for analysis_attempt in range(1, max_analysis_retries + 1):
            if analysis_attempt > 1:
                print_step("🔄", f"[bold]Re-generating final query (attempt {analysis_attempt}/{max_analysis_retries})...[/bold]")
            else:
                print_step("📋", "[bold]All exploration complete. Generating final query...[/bold]")

            final_result = await self._generate_final_query(
                question, schema_info, completed_results,
                plan.final_assembly_strategy, conversation_context,
                analysis_feedback,
            )
            usage_stats.add(self.query_agent.last_usage)

            if final_result is None:
                return None, None, None, usage_stats

            query_result, query_plan, exec_result = final_result

            # Step 4: Analyze results
            async with pipeline_status("Analyzing results..."):
                db_context = await self.context_manager.get_database_context()
                analysis_result = await self._with_api_retry(
                    lambda: self.analysis_agent.analyze_results(
                        question=question,
                        sql_query=query_plan.sql_query,
                        execution_success=exec_result.success,
                        results=exec_result.data,
                        error=exec_result.error,
                        db_context=db_context,
                    ),
                    max_api_retries,
                )

            usage_stats.add(self.analysis_agent.last_usage)

            if isinstance(analysis_result, RetryWithFeedback):
                if analysis_attempt < max_analysis_retries:
                    print_warning(f"Analysis feedback: {analysis_result.retry_reason}")
                    analysis_feedback = (
                        f"{analysis_result.retry_reason}\n"
                        f"Suggestion: {analysis_result.suggested_fix}"
                    )
                    # On zero-row results, add explicit near-miss guidance
                    if exec_result.row_count == 0:
                        analysis_feedback += (
                            "\n\nIMPORTANT: The previous query returned 0 rows. "
                            "Do NOT just re-run with minor tweaks. Instead:\n"
                            "1. REMOVE all WHERE/HAVING filter conditions from the final SELECT.\n"
                            "2. Convert each filter into a computed flag column "
                            "(e.g., `CASE WHEN pct_change <= -0.10 THEN 1 ELSE 0 END AS store_declining`).\n"
                            "3. ORDER BY the flag columns DESC so near-misses appear first.\n"
                            "4. LIMIT to 50 rows.\n"
                            "This lets the user see what data exists and how close it is to matching."
                        )
                    continue
                # Last attempt — return as-is, caller will handle
            break

        return analysis_result, query_plan, exec_result, usage_stats

    async def _execute_sub_problem(
        self,
        sub_problem,
        schema_info: dict[str, Any],
        prior_results: list[SubProblemResult],
    ) -> SubProblemResult:
        """Execute a single sub-problem: generate SQL, run it, summarize."""
        step_label = f"{sub_problem.id}: {sub_problem.title}"

        async with pipeline_status(f"Step {step_label}..."):
            # Build sub-problem prompt for the query agent
            sub_context = self._build_sub_problem_context(sub_problem, prior_results, schema_info)

            try:
                query_result = await self.query_agent.generate_query(
                    question=sub_context,
                    schema_info=schema_info,
                    feedback=None,
                )
            except Exception as e:
                print_error(f"  Step {sub_problem.id} failed to generate SQL: {e}")
                return SubProblemResult(
                    sub_problem_id=sub_problem.id, success=False, error=str(e)
                )

            # ConversationalResponse in a sub-problem means the agent couldn't
            # generate SQL — treat as failure to trigger plan revision
            if isinstance(query_result, ConversationalResponse):
                return SubProblemResult(
                    sub_problem_id=sub_problem.id,
                    success=False,
                    data_summary=query_result.message,
                    error=f"Sub-problem could not be resolved with SQL: {query_result.message}",
                )

            # Validate
            query_plan: QueryPlan = query_result
            is_valid, validation_error = self.query_executor.validate_query(
                query_plan.sql_query
            )
            if not is_valid:
                print_error(f"  Step {sub_problem.id} validation failed: {validation_error}")
                return SubProblemResult(
                    sub_problem_id=sub_problem.id,
                    sql_query=query_plan.sql_query,
                    success=False,
                    error=validation_error,
                )

            # Execute
            exec_result = await self.query_executor.execute(query_plan.sql_query)

            if not exec_result.success:
                print_error(f"  Step {sub_problem.id} execution failed: {exec_result.error}")
                return SubProblemResult(
                    sub_problem_id=sub_problem.id,
                    sql_query=query_plan.sql_query,
                    success=False,
                    error=exec_result.error,
                )

        # Build result summary
        key_findings = self._extract_findings(
            sub_problem, exec_result.data, exec_result.row_count
        )

        # Extract verified columns (result column names prove they exist)
        verified_columns = {}
        if exec_result.data:
            for col_name in exec_result.data[0].keys():
                verified_columns[col_name] = col_name

        # Extract verified joins from the SQL that succeeded
        verified_joins = self._extract_joins(query_plan.sql_query)

        print_step("  ✅", f"[bold]{sub_problem.title}[/bold] ({exec_result.row_count} rows)")
        for finding in key_findings[:3]:
            print_sub(finding)

        return SubProblemResult(
            sub_problem_id=sub_problem.id,
            sql_query=query_plan.sql_query,
            success=True,
            data_summary=query_plan.explanation,
            row_count=exec_result.row_count,
            key_findings=key_findings,
            verified_columns=verified_columns,
            verified_joins=verified_joins,
            sample_data=exec_result.data[:5] if exec_result.data else None,
        )

    def _build_sub_problem_context(
        self, sub_problem, prior_results: list[SubProblemResult],
        schema_info: dict[str, Any],
    ) -> str:
        """Build a focused prompt for a sub-problem's SQL generation."""
        prompt = (
            f"Generate exactly ONE SQL SELECT statement for this specific sub-task.\n"
            f"Do NOT generate multiple statements or use PRAGMA.\n\n"
            f"**Task**: {sub_problem.title}\n"
            f"**Purpose**: {sub_problem.purpose}\n"
            f"**Approach**: {sub_problem.approach}\n"
            f"**Tables to use**: {', '.join(sub_problem.tables_needed)}\n\n"
        )

        # List exact columns available for each needed table
        tables = schema_info.get("tables", {})
        for table_name in sub_problem.tables_needed:
            if table_name in tables:
                table_info = tables[table_name]
                columns = table_info.get("columns", {})
                col_list = ", ".join(f"`{c}`" for c in columns.keys())
                prompt += f"**{table_name} columns**: {col_list}\n"
                rels = table_info.get("relationships", [])
                if rels:
                    prompt += f"**{table_name} relationships**: {'; '.join(rels)}\n"
            prompt += "\n"

        prompt += (
            "IMPORTANT: Use ONLY the column names listed above. "
            "Do NOT invent or guess column names.\n"
            "This is a VALIDATION query — keep it simple (1-2 joins max). "
            "LIMIT results to 20 rows unless doing aggregation.\n"
        )

        # Add context from completed sub-problems
        successful = [r for r in prior_results if r.success and r.key_findings]
        if successful:
            prompt += "\n**Results from previous steps**:\n"
            for r in successful:
                for finding in r.key_findings:
                    prompt += f"- {finding}\n"

        return prompt

    def _extract_findings(
        self, sub_problem, data: list[dict], row_count: int
    ) -> list[str]:
        """Extract key findings from sub-problem results."""
        findings = []

        if not data:
            findings.append(f"No rows returned for {sub_problem.title}")
            return findings

        # For aggregation results (small row counts), show the actual values
        if row_count <= 20:
            col_names = list(data[0].keys())
            findings.append(f"Result columns: {', '.join(col_names)}")
            for row in data[:5]:
                vals = [f"{k}={v}" for k, v in row.items()]
                findings.append(f"  {', '.join(vals[:6])}")
        else:
            findings.append(f"Returned {row_count} rows")
            col_names = list(data[0].keys())
            findings.append(f"Result columns: {', '.join(col_names)}")

        return findings

    def _extract_joins(self, sql: str) -> list[str]:
        """Extract JOIN ... ON clauses from a successful SQL query."""
        joins = re.findall(
            r'JOIN\s+(\w+)\s+\w*\s*ON\s+([^\n;]+?)(?=\s+(?:JOIN|WHERE|GROUP|ORDER|LIMIT|$))',
            sql, re.IGNORECASE
        )
        return [f"{table} ON {condition.strip()}" for table, condition in joins]

    async def _generate_final_query(
        self,
        question: str,
        schema_info: dict[str, Any],
        sub_results: list[SubProblemResult],
        assembly_strategy: str,
        conversation_context: str | None,
        analysis_feedback: str | None = None,
    ):
        """Generate the final query using all sub-problem findings."""
        max_api_retries = 2
        max_attempts = Config.MAX_RETRY_ATTEMPTS
        feedback = analysis_feedback

        for attempt in range(1, max_attempts + 1):
            if attempt > 1:
                print_step("🔄", f"Final query retry {attempt}/{max_attempts}...")

            # Build enriched question with all findings
            enriched_question = self._build_final_prompt(
                question, sub_results, assembly_strategy, conversation_context, feedback
            )

            async with pipeline_status("Generating final SQL query..."):
                query_result = await self._with_api_retry(
                    lambda: self.query_agent.generate_query(
                        enriched_question, schema_info, feedback
                    ),
                    max_api_retries,
                )
                if query_result is None:
                    return None

            if isinstance(query_result, ConversationalResponse):
                print_panel(query_result.message, "Response", style="yellow")
                return None

            query_plan: QueryPlan = query_result
            print_step("🔨", "[bold]Final SQL query generated[/bold]")
            print_sql(query_plan.sql_query)
            print_sub(query_plan.explanation)

            # Validate
            is_valid, validation_error = self.query_executor.validate_query(
                query_plan.sql_query
            )
            if is_valid:
                print_step("✅", "Query validated")
            else:
                print_error(f"Validation failed: {validation_error}")
                if attempt < max_attempts:
                    feedback = validation_error
                    continue
                return None

            # Execute
            async with pipeline_status("Executing final query..."):
                exec_result = await self.query_executor.execute(query_plan.sql_query)

            if not exec_result.success:
                print_error(f"Execution failed: {exec_result.error}")
                if attempt < max_attempts:
                    feedback = exec_result.error
                    continue
                return None

            print_step("⚙️ ", f"[bold]Query returned {exec_result.row_count} rows[/bold]")
            return query_result, query_plan, exec_result

        return None

    def _build_final_prompt(
        self,
        question: str,
        sub_results: list[SubProblemResult],
        assembly_strategy: str,
        conversation_context: str | None,
        feedback: str | None,
    ) -> str:
        """Build the final query prompt enriched with sub-problem findings."""
        prompt = ""
        if conversation_context:
            prompt += f"{conversation_context}\n"

        prompt += f"**Question**: {question}\n\n"

        # Build structured "Corrected Schema" from verified columns and joins
        successful = [r for r in sub_results if r.success]

        all_verified_columns = {}
        all_verified_joins = []
        for r in successful:
            all_verified_columns.update(r.verified_columns)
            all_verified_joins.extend(r.verified_joins)

        if all_verified_columns or all_verified_joins:
            prompt += "**VERIFIED SCHEMA** (use these exact names — do NOT guess):\n"
            if all_verified_columns:
                prompt += "Columns:\n"
                for concept, real_name in all_verified_columns.items():
                    prompt += f"  - {concept} → `{real_name}`\n"
            if all_verified_joins:
                prompt += "Joins:\n"
                for join_clause in all_verified_joins:
                    prompt += f"  - {join_clause}\n"
            prompt += "\n"

        # Add concise findings from sub-problems
        if successful:
            prompt += "**DATA VALIDATION RESULTS**:\n"
            for r in successful:
                prompt += f"- {r.sub_problem_id}: {r.data_summary} ({r.row_count} rows)\n"
                if r.sample_data and len(r.sample_data) <= 3:
                    prompt += f"  Sample: {r.sample_data}\n"
            prompt += "\n"

        prompt += f"**Assembly Strategy**: {assembly_strategy}\n\n"
        prompt += (
            "Using the verified schema and validation results above, generate the FINAL SQL query. "
            "Use CTEs (WITH clauses) to structure the query clearly. "
            "Only use column names and join patterns from the VERIFIED SCHEMA section."
        )

        if feedback:
            if "IMPORTANT: The previous query returned 0 rows" in feedback:
                prompt += f"\n\n**CRITICAL — ZERO-ROW RECOVERY**: {feedback}\n"
                prompt += (
                    "You MUST follow the zero-row recovery instructions above. "
                    "Do not add WHERE filters that could produce 0 rows again.\n"
                )
            else:
                prompt += f"\n\n**Previous attempt feedback**: {feedback}\n"

        return prompt

    async def _with_api_retry(self, fn, max_retries: int):
        """Call fn with API overload retry logic. Returns None on exhaustion."""
        for attempt in range(max_retries):
            try:
                return await fn()
            except Exception as e:
                msg = str(e)
                if "503" in msg or "overloaded" in msg.lower() or "UNAVAILABLE" in msg:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(3)
                    else:
                        print_error("API temporarily unavailable. Please try again.")
                        return None
                else:
                    raise

    def _display_plan(self, plan: ExecutionPlan) -> None:
        """Display the execution plan as a task tree."""
        console.print()
        console.print("[bold cyan]📋 Execution Plan[/bold cyan]")
        print_sub(plan.approach_summary)
        console.print()
        for sp in plan.sub_problems:
            deps = f" (after {', '.join(sp.depends_on)})" if sp.depends_on else ""
            console.print(
                f"    [dim]○[/dim] {sp.id}: {sp.title}{deps}"
            )
        console.print(
            f"    [dim]◎[/dim] Final: {plan.final_assembly_strategy}"
        )
        console.print()

    def _display_revision(self, revision: PlanRevision) -> None:
        """Display plan revision details."""
        if revision.drop_ids:
            for drop_id in revision.drop_ids:
                print_sub(f"Dropped: {drop_id}")
        for sp in revision.updated_sub_problems:
            print_sub(f"Added: {sp.id}: {sp.title}")
