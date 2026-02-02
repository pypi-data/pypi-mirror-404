"""Schema enrichment agent using Pydantic AI."""

from typing import Any
from pydantic_ai import Agent
from urimai.storage.models import EnrichedSchema
from urimai.utils.llm import get_model
import json


# System prompt for enrichment agent
ENRICHMENT_PROMPT = """You are a database schema analyst. Your job is to analyze database table schemas and provide enriched, human-readable descriptions.

Given a table schema with columns, constraints, indexes, sample data, and a database overview showing all other tables, you should:
1. Determine the table's purpose and what it stores
2. Provide clear descriptions for each column (what it represents, not just its type). For foreign key columns, mention which table and column they reference.
3. Identify relationships to other tables using foreign key details and the database overview. Be specific about which columns link to which tables.
4. Infer business context from the sample data

Be concise but informative. Focus on helping users understand what data exists and how it's organized."""


class SchemaEnrichmentAgent:
    """Agent for enriching database schemas with AI-generated descriptions."""

    def __init__(self):
        """Initialize enrichment agent."""
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=EnrichedSchema,
            instructions=ENRICHMENT_PROMPT,
            retries=3,
        )

    async def enrich_schema(self, schema_data: dict[str, Any]) -> EnrichedSchema:
        """Enrich a table schema with AI-generated descriptions.

        Args:
            schema_data: Prepared schema data from SchemaExtractor.prepare_for_enrichment()

        Returns:
            EnrichedSchema with table purpose, column descriptions, etc.
        """
        # Build a detailed prompt with schema information
        prompt = self._build_enrichment_prompt(schema_data)

        # Run agent
        result = await self.agent.run(prompt)

        return result.output

    def _build_enrichment_prompt(self, schema_data: dict[str, Any]) -> str:
        """Build enrichment prompt from schema data.

        Args:
            schema_data: Schema information

        Returns:
            Formatted prompt string
        """
        table_name = schema_data["table_name"]
        columns = schema_data["columns"]
        constraints = schema_data.get("constraints", [])
        sample_data = schema_data.get("sample_data", [])

        prompt = f"Analyze this database table and provide enriched metadata:\n\n"
        prompt += f"**Table Name**: {table_name}\n\n"

        # Columns
        prompt += "**Columns**:\n"
        for col in columns:
            prompt += f"- {col['name']}: {col['type']}"
            if not col['nullable']:
                prompt += " (NOT NULL)"
            if col.get('default'):
                prompt += f" DEFAULT {col['default']}"
            prompt += "\n"

        # Constraints
        if constraints:
            prompt += "\n**Constraints**:\n"
            for constraint in constraints:
                if constraint.get("source_column"):
                    prompt += (
                        f"- FOREIGN KEY: {constraint['source_column']} -> "
                        f"{constraint['referenced_table']}.{constraint['referenced_column']}\n"
                    )
                else:
                    prompt += f"- {constraint['name']}: {constraint['type']}\n"

        # Sample Data
        if sample_data:
            prompt += "\n**Sample Data** (first few rows):\n"
            prompt += json.dumps(sample_data, indent=2)
        else:
            prompt += "\n*No sample data available*\n"

        # Database Overview
        database_context = schema_data.get("database_context")
        if database_context:
            prompt += "\n\n**Database Overview** (all tables in this database):\n"
            prompt += database_context

        prompt += "\n\nProvide enriched metadata for this table."

        return prompt
