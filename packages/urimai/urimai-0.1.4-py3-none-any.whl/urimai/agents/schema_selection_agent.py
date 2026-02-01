"""Schema selection agent for intelligent table filtering.

When a database has many tables, this agent identifies which tables
are relevant to a user's question, reducing noise for the query agent.
"""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from urimai.utils.llm import get_model


class TableSelection(BaseModel):
    """Result of table selection for a user query."""

    tables: list[str] = Field(
        description="List of table names needed to answer the question, including tables needed for JOINs"
    )
    reasoning: str = Field(
        description="Brief explanation of why these tables were selected"
    )


SCHEMA_SELECTION_PROMPT = """You are a schema analyst. Given a user question and a database schema summary, identify which tables are needed to answer the question.

Rules:
- Include tables that directly contain the data needed
- Include tables needed for JOINs to connect the relevant data
- Do NOT include tables that are unrelated to the question
- When in doubt, include the table rather than exclude it
- Return exact table names as they appear in the schema"""


class SchemaSelectionAgent:
    """Agent that selects relevant tables for a user query."""

    def __init__(self):
        """Initialize schema selection agent."""
        self.last_usage = None
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=TableSelection,
            instructions=SCHEMA_SELECTION_PROMPT,
            retries=2,
        )

    async def select_tables(self, query: str, schema_summary: str) -> TableSelection:
        """Select relevant tables for a user query.

        Args:
            query: User's natural language question
            schema_summary: Condensed schema summary with table names, purposes, and columns

        Returns:
            TableSelection with selected tables and reasoning
        """
        prompt = f"**User Question**: {query}\n\n**Database Schema**:\n{schema_summary}"
        result = await self.agent.run(prompt)
        self.last_usage = result.usage()
        return result.output
