"""Result analysis agent using Pydantic AI."""

from typing import Any
from pydantic_ai import Agent
from urimai.storage.models import SuccessAnswer, RetryWithFeedback
from urimai.utils.llm import get_model
import json


# System prompt for analysis agent
ANALYSIS_PROMPT = """You are a data analyst specialized in validating SQL query results. Your job is to determine if query results properly answer the user's question.

You will be provided with:
1. The original user question
2. The SQL query that was executed
3. The query results (or error message)

Your responsibilities:
- Determine if the results answer the user's question
- Generate a natural language answer based on the results
- If results are wrong/incomplete, provide feedback for query improvement
- Return SuccessAnswer if results are good, RetryWithFeedback if query needs revision

Guidelines:
- If query returned no results but should have, suggest retry with feedback
- If there's a SQL error, provide clear feedback on what went wrong
- If results are correct, generate a clear, conversational answer
- Always provide confidence score (0.0-1.0) for successful answers
- Be specific in feedback - mention exact table/column names if needed

Zero-row results — special handling:
- When a query returns 0 rows, DO NOT immediately accept it as "no data exists."
- First check: are the WHERE/HAVING filters too restrictive? Could relaxing thresholds surface near-misses?
- If the query has multiple filter conditions (e.g., decline > 10% AND growth > 0%), suggest retrying
  with relaxed or removed filters and adding a column that flags which criteria each row meets.
  Example suggested_fix: "Remove the WHERE filters. Instead, add boolean flag columns like
  `store_declining = CASE WHEN store_pct_change <= -0.10 THEN 1 ELSE 0 END` and
  `web_growing = CASE WHEN web_pct_change > 0 THEN 1 ELSE 0 END`, then ORDER BY store_declining DESC, web_growing DESC
  so the user can see what's closest to matching."
- Only accept 0 rows as a genuine result (SuccessAnswer) if the query has minimal/no filters
  or if a prior relaxed attempt also returned 0 rows."""


class ResultAnalysisAgent:
    """Agent for analyzing query results and determining if retry is needed."""

    def __init__(self):
        """Initialize analysis agent."""
        self.last_usage = None
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=SuccessAnswer | RetryWithFeedback,
            instructions=ANALYSIS_PROMPT,
            retries=3,
        )

    async def analyze_results(
        self,
        question: str,
        sql_query: str,
        execution_success: bool,
        results: list[dict[str, Any]] | None = None,
        error: str | None = None,
        db_context: Any = None,
    ) -> SuccessAnswer | RetryWithFeedback:
        """Analyze query execution results.

        Args:
            question: Original user question
            sql_query: SQL query that was executed
            execution_success: Whether query executed successfully
            results: Query results (if successful)
            error: Error message (if failed)
            db_context: Database domain context for validation (optional)

        Returns:
            SuccessAnswer if results are good, RetryWithFeedback if needs improvement
        """
        prompt = self._build_analysis_prompt(
            question, sql_query, execution_success, results, error, db_context
        )

        # Run agent
        result = await self.agent.run(prompt)
        self.last_usage = result.usage()

        return result.output

    def _build_analysis_prompt(
        self,
        question: str,
        sql_query: str,
        execution_success: bool,
        results: list[dict[str, Any]] | None,
        error: str | None,
        db_context: Any = None,
    ) -> str:
        """Build analysis prompt.

        Args:
            question: User's question
            sql_query: SQL query
            execution_success: Execution status
            results: Query results
            error: Error message
            db_context: Database context for validation

        Returns:
            Formatted prompt string
        """
        prompt = f"**User Question**: {question}\n\n"

        # Add database context for validation
        if db_context:
            prompt += f"**Database Domain**: {db_context.domain}\n"
            prompt += f"**Database Purpose**: {db_context.purpose}\n"
            prompt += f"**Data Characteristics**: {db_context.data_characteristics}\n\n"
            prompt += "Use this context to validate if the results make sense for this domain.\n\n"

        prompt += f"**SQL Query Executed**:\n```sql\n{sql_query}\n```\n\n"

        if execution_success and results is not None:
            prompt += "**Query Results**:\n"
            if len(results) == 0:
                prompt += "*No rows returned*\n\n"
            else:
                # Show first 10 results for analysis
                display_results = results[:10]
                prompt += f"*Returned {len(results)} rows (showing first {len(display_results)})*\n"
                prompt += json.dumps(display_results, indent=2)
                prompt += "\n\n"

            prompt += "Analyze if these results properly answer the user's question. "
            if db_context:
                prompt += "Consider the database domain and validate if values make sense. "
            prompt += "If yes, provide a natural language answer with confidence score. "
            prompt += "If no, provide feedback for query improvement."

        else:
            prompt += f"**Query Execution Failed**:\n"
            prompt += f"Error: {error}\n\n"
            prompt += "Provide feedback on how to fix the query."

        return prompt
