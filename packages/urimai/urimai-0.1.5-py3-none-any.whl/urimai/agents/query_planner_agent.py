"""Query planning agent for complex multi-step questions."""

from typing import Any
from pydantic_ai import Agent
from urimai.storage.models import QueryComplexity, ExecutionPlan, PlanRevision, SubProblemResult
from urimai.utils.llm import get_model


COMPLEXITY_PROMPT = """You classify whether a natural language question about a database
requires a simple single query or a complex multi-step approach.

A question is COMPLEX if ANY of these apply:
- Requires joining 4+ tables
- Needs multiple aggregation levels (e.g., totals AND averages in same result)
- Involves computed metrics across different fact tables (e.g., sales minus returns)
- Requires comparing groups or time periods
- Has conditional logic (e.g., "top categories WHERE revenue > X")
- Involves star-schema fact + dimension joins with aggregation

A question is SIMPLE if:
- Single table query or 1-2 joins
- Basic count/sum/avg on one fact table
- Simple lookup or filter
- Direct column selection

When in doubt, classify as COMPLEX — it's better to over-plan than to produce wrong SQL."""


PLANNING_PROMPT = """You are a SQL query architect. Given a complex analytical question and
database schema (with enriched metadata, column descriptions, and relationships already provided),
you decompose it into small, verifiable sub-problems.

IMPORTANT: You already have full schema metadata — column names, types, descriptions,
relationships, and sample data are provided. Do NOT create sub-problems to "explore" the schema.
Sub-problems should focus on TESTING QUERY LOGIC against real data.

Each sub-problem must be a minimal, isolated test. DO NOT attempt to answer the user's full
question in a sub-problem. Each step should test ONE thing.

BAD sub-problem: "Get total sales for top 5 stores" (too complex — involves joining and ranking)
GOOD sub-problem: "Check if store_sales joins to store on s_store_sk with non-zero count"
GOOD sub-problem: "Verify the SUM(ss_net_profit) aggregation returns reasonable totals"

The purpose is to TEST and VALIDATE logic incrementally before assembling a complex final query.

Sub-problem types (use as needed):
1. **Join Cardinality Check** — confirm joins produce expected row counts (not exploding or empty)
   Example: "SELECT COUNT(*) FROM store_sales ss JOIN item i ON ss.ss_item_sk = i.i_item_sk"
2. **Partial Aggregation** — compute ONE metric in isolation to verify logic
   Example: "SELECT i_category, SUM(ss_sales_price) as total_sales FROM store_sales JOIN item ... GROUP BY i_category"
3. **Sanity Check** — verify baseline numbers before combining multiple fact tables
   Example: "SELECT SUM(ss_sales_price) FROM store_sales" (compare with final to detect double-counting)
4. **CTE Fragment Test** — test a single CTE that will be part of the final query
   Example: Run the returns CTE alone to verify it produces correct per-category totals
5. **Discovery Query** — broad aggregation with loose/no filters to surface candidates BEFORE applying strict criteria
   Example: "SELECT i_category, SUM(ss_net_paid) as total, COUNT(*) as cnt FROM store_sales JOIN item ... GROUP BY i_category ORDER BY total DESC LIMIT 20"
   Use this FIRST when the user's question is exploratory (e.g., "which categories...", "find products where...", "are there any...").

Guidelines:
- 2-5 sub-problems is ideal. Don't over-decompose.
- Each sub-problem should be a simple query (1-2 joins max).
- Order by dependencies — cardinality checks first, then partial aggregations.
- The final_assembly_strategy should describe how to combine findings into a CTE-based final query.
- Sub-problems VALIDATE LOGIC — the final query is what actually answers the user's question.
- You already know the schema. Focus on testing the DATA, not discovering columns.
- In the `approach` field, use EXACT column names from the provided schema. Never invent column names.
- Each sub-problem must produce exactly ONE SQL SELECT statement. Never use PRAGMA or multiple statements.

**Exploratory vs Confirmatory questions**:
- EXPLORATORY questions ask "which?", "are there?", "find categories where..." — the user doesn't know the answer yet.
  For these, start with a Discovery Query (broad aggregation, loose filters) to surface candidates,
  then validate specific patterns. The final query should show results even if they don't perfectly match
  all criteria — include near-misses with a flag column indicating which criteria are met.
- CONFIRMATORY questions ask "how many X did Y have?" or "what was the total Z?" — the user expects a specific answer.
  For these, use the existing validation-first approach (cardinality checks, partial aggregations)."""


REVISION_PROMPT = """You are revising a query execution plan because a sub-problem failed
or returned unexpected results.

Given the original plan, the failed step, its error, and results from completed steps,
decide whether and how to revise the remaining plan.

Options:
- Adjust the failed step (different columns, different join, different table)
- Add a new exploration step to investigate the issue
- Drop unnecessary remaining steps
- Keep the plan as-is if the failure is non-critical

Be conservative — only change what's necessary.

IMPORTANT:
- Use ONLY column names from the schema provided. Do not invent or guess column names.
- Each sub-problem must produce exactly ONE SQL SELECT statement. No PRAGMA, no multiple statements."""


class QueryPlannerAgent:
    """Agent for classifying complexity and creating execution plans."""

    def __init__(self):
        self.last_usage = None
        self.model = get_model()

        self.classifier = Agent(
            self.model,
            output_type=QueryComplexity,
            instructions=COMPLEXITY_PROMPT,
            retries=2,
        )

        self.planner = Agent(
            self.model,
            output_type=ExecutionPlan,
            instructions=PLANNING_PROMPT,
            retries=3,
        )

        self.reviser = Agent(
            self.model,
            output_type=PlanRevision,
            instructions=REVISION_PROMPT,
            retries=2,
        )

    async def classify_complexity(
        self,
        question: str,
        schema_info: dict[str, Any],
    ) -> QueryComplexity:
        """Classify whether question needs multi-step planning."""
        # Build a concise schema summary (table names + purposes + column names)
        tables_summary = []
        tables = schema_info.get("tables", {})
        for table_name, info in tables.items():
            cols = list(info.get("columns", {}).keys())
            purpose = info.get("purpose", "")
            tables_summary.append(
                f"- {table_name}: {purpose} | Columns: {', '.join(cols[:15])}"
            )

        prompt = (
            f"Question: {question}\n\n"
            f"Database ({schema_info.get('domain', 'unknown')} domain):\n"
            + "\n".join(tables_summary)
        )

        result = await self.classifier.run(prompt)
        self.last_usage = result.usage()
        return result.output

    async def create_plan(
        self,
        question: str,
        schema_info: dict[str, Any],
    ) -> ExecutionPlan:
        """Create a multi-step execution plan for a complex question."""
        # Build detailed schema for planning (reuse query_agent's format)
        prompt = f"**Question**: {question}\n\n"
        prompt += f"**Database Domain**: {schema_info.get('domain', '')}\n"
        prompt += f"**Purpose**: {schema_info.get('database_purpose', '')}\n\n"

        prompt += "**Available Tables**:\n\n"
        tables = schema_info.get("tables", {})
        for table_name, info in tables.items():
            prompt += f"### {table_name}\n"
            purpose = info.get("purpose", "")
            if purpose:
                prompt += f"Purpose: {purpose}\n"
            columns = info.get("columns", {})
            for col_name, col_desc in columns.items():
                prompt += f"  - `{col_name}`: {col_desc}\n"
            relationships = info.get("relationships", [])
            if relationships:
                prompt += "  Relationships: " + "; ".join(relationships) + "\n"
            prompt += "\n"

        result = await self.planner.run(prompt)
        self.last_usage = result.usage()
        return result.output

    async def revise_plan(
        self,
        plan: ExecutionPlan,
        failed_step: str,
        error: str,
        completed_results: list[SubProblemResult],
        schema_info: dict[str, Any] | None = None,
    ) -> PlanRevision:
        """Revise the plan after a sub-problem failure."""
        completed_summary = "\n".join(
            f"- {r.sub_problem_id}: {r.data_summary}"
            for r in completed_results
        )

        prompt = (
            f"**Original Question**: {plan.question}\n\n"
            f"**Failed Step**: {failed_step}\n"
            f"**Error**: {error}\n\n"
            f"**Completed Steps**:\n{completed_summary}\n\n"
            f"**Remaining Sub-problems**:\n"
        )
        for sp in plan.sub_problems:
            if sp.id != failed_step and sp.id not in [r.sub_problem_id for r in completed_results]:
                prompt += f"- {sp.id}: {sp.title} — {sp.purpose}\n"

        if schema_info:
            prompt += "\n**Available Schema** (use ONLY these column names in approach descriptions):\n"
            tables = schema_info.get("tables", {})
            for table_name, info in tables.items():
                cols = list(info.get("columns", {}).keys())
                prompt += f"- {table_name}: {', '.join(cols)}\n"

        prompt += (
            "\nIMPORTANT: In approach descriptions, reference ONLY column names from the schema above. "
            "Each sub-problem must produce exactly ONE SQL SELECT statement (no PRAGMA, no multiple statements)."
        )

        result = await self.reviser.run(prompt)
        self.last_usage = result.usage()
        return result.output
