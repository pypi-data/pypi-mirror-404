"""Role Classification Agent - Context-aware semantic role classifier."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from urimai.utils.llm import get_model
from urimai.agents.schema_context_agent import DatabaseContext


class ColumnRole(BaseModel):
    """Semantic role classification for a column."""

    column_name: str = Field(description="Name of the column")
    semantic_role: str = Field(
        description="Semantic role of this column (e.g., 'unique_identifier', 'birth_year', 'person_name', 'currency_amount')"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence in this classification"
    )
    reasoning: str = Field(
        description="Explanation of why this classification was chosen"
    )
    related_columns: list[str] = Field(
        default_factory=list,
        description="Other columns this relates to semantically",
    )


class TableRoles(BaseModel):
    """Role classifications for all columns in a table."""

    table_name: str
    column_roles: list[ColumnRole]


ROLE_CLASSIFICATION_PROMPT = """You are a data semantics expert. Your job is to understand what each column means in the context of this specific database.

Database Context:
Domain: {domain}
Purpose: {purpose}
Key entities: {key_entities}
Data characteristics: {data_characteristics}

Current Table: {table_name}
Table purpose: {table_purpose}

Column Details:
{column_details}

Related Tables:
{related_tables}

For EACH column, determine its semantic role. DO NOT use a predefined list of roles - infer the actual meaning based on:
1. The database domain and purpose
2. The column name, type, and statistics
3. Sample values
4. Relationships to other columns/tables

Be specific and contextual. For example:
- In a sports DB, "year" in "birth_year" is different from "year" in "season_year"
- "ID" fields should specify what they identify
- Date fields should indicate what event they represent

Classify ALL columns provided."""


class RoleClassificationAgent:
    """Agent that classifies column roles using full database context."""

    def __init__(self):
        """Initialize role classification agent."""
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=TableRoles,
            instructions=ROLE_CLASSIFICATION_PROMPT,
            retries=3,
        )

    async def classify_table(
        self,
        table_name: str,
        columns: list,
        db_context: DatabaseContext,
        table_purpose: str,
        sample_data: list[dict],
        related_tables: dict,
    ) -> TableRoles:
        """Classify roles for all columns in a table.

        Args:
            table_name: Name of the table
            columns: List of ColumnProfile objects
            db_context: Database context from SchemaContextAgent
            table_purpose: LLM-generated purpose of this table
            sample_data: Sample rows from this table
            related_tables: Dict of related table names and their schemas

        Returns:
            TableRoles with classifications for all columns
        """
        # Format column details
        column_details = self._format_column_details(columns, sample_data)
        related_text = self._format_related_tables(related_tables)

        # Format the prompt with actual data
        prompt = ROLE_CLASSIFICATION_PROMPT.format(
            domain=db_context.domain,
            purpose=db_context.purpose,
            key_entities=", ".join(db_context.key_entities),
            data_characteristics=db_context.data_characteristics,
            table_name=table_name,
            table_purpose=table_purpose,
            column_details=column_details,
            related_tables=related_text,
        )

        # Run agent
        result = await self.agent.run(prompt)

        return result.output

    def _format_column_details(
        self, columns: list, sample_data: list[dict]
    ) -> str:
        """Format column details with statistics and samples.

        Args:
            columns: List of ColumnProfile objects
            sample_data: Sample rows

        Returns:
            Formatted string
        """
        formatted = []

        for col in columns:
            formatted.append(f"\n## Column: {col.column_name}")
            formatted.append(f"Type: {col.data_type}")
            formatted.append(f"Null: {col.null_percentage:.1f}%")
            formatted.append(f"Distinct: {col.distinct_count} ({col.distinct_percentage:.1f}%)")

            # Add numeric stats if available
            if col.mean is not None:
                formatted.append(
                    f"Range: {col.min_value} to {col.max_value} (mean: {col.mean:.2f})"
                )

            # Add string stats if available
            if col.min_length is not None:
                formatted.append(
                    f"Length: {col.min_length} to {col.max_length} (avg: {col.avg_length:.1f})"
                )

            # Add sample values
            if sample_data:
                sample_values = [
                    str(row.get(col.column_name))
                    for row in sample_data[:5]
                    if row.get(col.column_name) is not None
                ]
                if sample_values:
                    formatted.append(f"Sample values: {', '.join(sample_values[:5])}")

        return "\n".join(formatted)

    def _format_related_tables(self, related_tables: dict) -> str:
        """Format related tables information.

        Args:
            related_tables: Dict of table_name -> schema summary

        Returns:
            Formatted string
        """
        if not related_tables:
            return "No related tables identified"

        formatted = []
        for table_name, schema in related_tables.items():
            formatted.append(f"\n{table_name}:")
            if isinstance(schema, str):
                formatted.append(f"  {schema}")
            else:
                formatted.append(f"  (schema available)")

        return "\n".join(formatted) if formatted else "No related tables"
