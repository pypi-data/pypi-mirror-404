"""Schema Context Agent - Understands database domain and business context holistically."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from urimai.utils.llm import get_model


class DatabaseContext(BaseModel):
    """Holistic understanding of database domain and business context."""

    domain: str = Field(
        description="Domain/industry of this database (e.g., 'sports_statistics', 'e-commerce', 'healthcare')"
    )
    domain_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in domain classification (0.0-1.0)",
    )
    purpose: str = Field(
        description="Business purpose and what this database tracks"
    )
    key_entities: list[str] = Field(
        description="Main entities/concepts in this database"
    )
    relationships_summary: str = Field(
        description="How the key entities relate to each other"
    )
    data_characteristics: str = Field(
        description="Important characteristics of the data (historical, real-time, transactional, etc.)"
    )
    business_priorities: list[str] = Field(
        description="What data quality aspects matter most for this domain"
    )
    refined_relationships: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Per-table refined relationships: table_name -> list of relationship descriptions grounded in actual schema knowledge"
    )


SCHEMA_CONTEXT_PROMPT = """You are a data analyst expert who understands databases holistically.

Analyze this database by examining ALL tables, their schemas, relationships, and sample data.

Your goal: Understand what this database IS, what it's used for, and what matters for its data quality.

Tables and Schemas:
{schemas}

Enriched Metadata (business descriptions):
{enriched_metadata}

Sample Data:
{sample_data}

Analyze holistically and provide:
1. What domain/industry is this database for?
2. What is its business purpose?
3. What are the key entities and how do they relate?
4. What are the data characteristics? (historical, real-time, complete, partial, etc.)
5. What data quality aspects are most critical for this domain?
6. For each table, provide refined relationship descriptions grounded in actual foreign keys and cross-table knowledge. Be specific about which columns link tables together and the nature of each relationship (one-to-many, many-to-many, lookup, etc.)

Be specific and contextual. Don't just list tables - understand the BUSINESS."""


class SchemaContextAgent:
    """Agent that understands database context holistically."""

    def __init__(self):
        """Initialize schema context agent."""
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=DatabaseContext,
            instructions=SCHEMA_CONTEXT_PROMPT,
            retries=3,
        )

    async def analyze_database(
        self,
        schemas: list,
        enriched_metadata: dict,
        sample_data: dict,
    ) -> DatabaseContext:
        """Analyze database holistically to understand domain and context.

        Args:
            schemas: List of SchemaInfo objects with table schemas
            enriched_metadata: Dict of table_name -> enriched descriptions
            sample_data: Dict of table_name -> sample rows

        Returns:
            DatabaseContext with domain understanding
        """
        # Format schemas for the prompt
        schemas_text = self._format_schemas(schemas)
        enriched_text = self._format_enriched_metadata(enriched_metadata)
        sample_text = self._format_sample_data(sample_data)

        # Format the prompt with actual data
        prompt = SCHEMA_CONTEXT_PROMPT.format(
            schemas=schemas_text,
            enriched_metadata=enriched_text,
            sample_data=sample_text,
        )

        # Run agent
        result = await self.agent.run(prompt)

        return result.output

    def _format_schemas(self, schemas: list) -> str:
        """Format schemas for prompt.

        Args:
            schemas: List of SchemaInfo objects

        Returns:
            Formatted string with schema details
        """
        formatted = []

        for schema in schemas:
            table_name = schema.table_name
            columns = schema.original_metadata.get("columns", [])
            constraints = schema.original_metadata.get("constraints", [])

            formatted.append(f"\n## Table: {table_name}")
            formatted.append("Columns:")
            for col in columns[:20]:  # Limit to 20 columns per table
                col_name = col.get("column_name", col.get("name", "unknown"))
                col_type = col.get("data_type", col.get("type", "unknown"))
                nullable = col.get("is_nullable", True)
                formatted.append(f"  - {col_name} ({col_type})" + (" NULL" if nullable else " NOT NULL"))

            if len(columns) > 20:
                formatted.append(f"  ... and {len(columns) - 20} more columns")

            # Include foreign key details
            fk_constraints = [c for c in constraints if c.get("source_column")]
            if fk_constraints:
                formatted.append("Foreign Keys:")
                for fk in fk_constraints:
                    formatted.append(
                        f"  - {fk['source_column']} -> {fk['referenced_table']}.{fk['referenced_column']}"
                    )

        return "\n".join(formatted)

    def _format_enriched_metadata(self, enriched_metadata: dict) -> str:
        """Format enriched metadata for prompt.

        Args:
            enriched_metadata: Dict of table descriptions

        Returns:
            Formatted string
        """
        if not enriched_metadata:
            return "No enriched metadata available"

        formatted = []
        for table_name, metadata in enriched_metadata.items():
            if metadata:
                purpose = metadata.get("table_purpose", "")
                if purpose:
                    formatted.append(f"\n{table_name}: {purpose}")

        return "\n".join(formatted) if formatted else "No enriched metadata available"

    def _format_sample_data(self, sample_data: dict) -> str:
        """Format sample data for prompt.

        Args:
            sample_data: Dict of table_name -> sample rows

        Returns:
            Formatted string with samples
        """
        if not sample_data:
            return "No sample data available"

        formatted = []
        for table_name, rows in sample_data.items():
            if rows:
                formatted.append(f"\n## Sample from {table_name} ({len(rows)} rows):")
                # Show first few rows
                for i, row in enumerate(rows[:3], 1):
                    # Show first 5 columns
                    sample_cols = list(row.items())[:5]
                    row_str = ", ".join(f"{k}={v}" for k, v in sample_cols)
                    formatted.append(f"  Row {i}: {row_str}")
                    if len(row) > 5:
                        formatted.append(f"         ... and {len(row) - 5} more columns")

        return "\n".join(formatted) if formatted else "No sample data available"
