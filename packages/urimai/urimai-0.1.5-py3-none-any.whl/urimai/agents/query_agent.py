"""Query generation agent using Pydantic AI."""

from typing import Any
from pydantic_ai import Agent
from urimai.storage.models import QueryPlan, ConversationalResponse
from urimai.utils.llm import get_model
import json


# System prompt for query agent
QUERY_GENERATION_PROMPT = """You are an expert SQL query generator. Your job is to convert natural language questions into accurate SQL queries for SQLite databases.

You will be provided with:
1. A user's question (which may include conversation history)
2. Database schema information (tables, columns, descriptions, relationships)

Your responsibilities:
- Generate syntactically correct SQLite queries
- Use appropriate JOINs when multiple tables are needed
- Apply filters, aggregations, and sorting as needed
- Return results in a user-friendly format
- Pay attention to conversation context - the user may reference previous queries
- If the question cannot be answered with the available data, return a conversational response explaining why

Guidelines:
- Use LIMIT clauses for queries that might return many rows
- Use descriptive column aliases for clarity
- Prefer INNER JOIN unless outer joins are specifically needed
- Always validate that tables and columns exist in the schema
- If conversation history is provided, use it to understand context and references
- Return ConversationalResponse if the question is unclear or cannot be answered with SQL

Context Awareness:
- If the user says "show me more details" or "what about X", look at previous conversation
- Understand references like "the first one", "those users", "same table", etc.
- Build upon previous queries when appropriate

Analytical Style:
- When the user asks if something is "significant" or "meaningful", default to DESCRIPTIVE analysis:
  show magnitudes, percentages, counts, and let the user judge. Do NOT add statistical tests
  (z-scores, p-values, confidence intervals, sample-size thresholds) unless the user explicitly
  asks for them (e.g., "statistically significant", "p-value", "confidence interval", "hypothesis test").
- For comparison queries, prefer showing the raw numbers side-by-side with computed differences
  and percentage gaps rather than adding boolean significance flags with arbitrary thresholds.
- Prefer weighted averages (SUM(value)/SUM(quantity)) over unweighted averages (AVG(value/quantity))
  for per-unit metrics."""


class QueryGenerationAgent:
    """Agent for generating SQL queries from natural language questions."""

    def __init__(self):
        """Initialize query generation agent."""
        self.last_usage = None
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=QueryPlan | ConversationalResponse,
            instructions=QUERY_GENERATION_PROMPT,
            retries=3,
        )

    async def generate_query(
        self,
        question: str,
        schema_info: dict[str, Any],
        feedback: str | None = None,
    ) -> QueryPlan | ConversationalResponse:
        """Generate SQL query from natural language question.

        Args:
            question: User's question in natural language
            schema_info: Formatted schema information from SchemaExtractor
            feedback: Optional feedback from previous query attempt (for retry)

        Returns:
            QueryPlan with SQL query or ConversationalResponse if cannot generate query
        """
        prompt = self._build_query_prompt(question, schema_info, feedback)

        # Run agent
        result = await self.agent.run(prompt)
        self.last_usage = result.usage()

        return result.output

    def _build_query_prompt(
        self,
        question: str,
        schema_info: dict[str, Any],
        feedback: str | None = None,
    ) -> str:
        """Build query generation prompt.

        Args:
            question: User's question
            schema_info: Schema information with domain context
            feedback: Optional feedback for retry

        Returns:
            Formatted prompt string
        """
        prompt = f"**User Question**: {question}\n\n"

        # Add database domain context if available
        domain = schema_info.get("domain", "")
        db_purpose = schema_info.get("database_purpose", "")
        data_chars = schema_info.get("data_characteristics", "")

        if domain:
            prompt += f"**Database Domain**: {domain}\n"
        if db_purpose:
            prompt += f"**Database Purpose**: {db_purpose}\n"
        if data_chars:
            prompt += f"**Data Characteristics**: {data_chars}\n"

        if domain or db_purpose or data_chars:
            prompt += "\n"

        # Add table selection notice if tables were pre-filtered
        selection_reasoning = schema_info.get("selection_reasoning")
        if selection_reasoning:
            prompt += f"Note: The following tables were pre-selected as relevant to your question.\n"
            prompt += f"Reasoning: {selection_reasoning}\n\n"

        # Add schema information
        prompt += "**Available Tables and Columns**:\n\n"
        tables = schema_info.get("tables", schema_info)  # Support both formats

        for table_name, table_info in tables.items():
            if table_name in ["domain", "database_purpose", "key_entities", "data_characteristics", "business_priorities"]:
                continue  # Skip context fields

            prompt += f"### Table: {table_name}\n"

            purpose = table_info.get("purpose", "")
            if purpose:
                prompt += f"*Purpose*: {purpose}\n\n"

            prompt += "**Columns**:\n"
            columns = table_info.get("columns", {})
            column_constraints = table_info.get("column_constraints", {})

            for col_name, col_desc in columns.items():
                prompt += f"- `{col_name}`: {col_desc}"

                # Add value constraints if available
                if col_name in column_constraints:
                    constraints = column_constraints[col_name]
                    if "valid_values" in constraints:
                        valid_vals = constraints["valid_values"]
                        prompt += f" (valid values: {', '.join(str(v) for v in valid_vals[:10])})"
                    elif "range" in constraints:
                        prompt += f" (range: {constraints['range']})"

                prompt += "\n"

            relationships = table_info.get("relationships", [])
            if relationships:
                prompt += "\n**Relationships**:\n"
                for rel in relationships:
                    prompt += f"- {rel}\n"

            # Render sample data if available
            sample_rows = table_info.get("sample_rows", [])
            if sample_rows:
                col_names = list(sample_rows[0].keys())
                prompt += "\n**Sample Data** (first rows):\n"
                prompt += "| " + " | ".join(col_names) + " |\n"
                prompt += "| " + " | ".join("---" for _ in col_names) + " |\n"
                for row in sample_rows:
                    values = [str(row.get(c, "")) for c in col_names]
                    # Truncate long values for readability
                    values = [v[:30] + "..." if len(v) > 30 else v for v in values]
                    prompt += "| " + " | ".join(values) + " |\n"

            prompt += "\n"

        # Add feedback if this is a retry
        if feedback:
            prompt += f"\n**Previous Attempt Feedback**: {feedback}\n"
            prompt += "Please generate an improved query based on this feedback.\n"

        prompt += "\nGenerate an appropriate SQL query to answer the user's question."

        return prompt
