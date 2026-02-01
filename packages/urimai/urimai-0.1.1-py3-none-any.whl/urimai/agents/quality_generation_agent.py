"""Quality Check Generation Agent - Generates dynamic quality checks based on context."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from urimai.utils.llm import get_model
from urimai.agents.schema_context_agent import DatabaseContext
from urimai.agents.role_classification_agent import TableRoles


class QualityCheck(BaseModel):
    """A dynamically generated quality check."""

    check_id: str = Field(description="Unique identifier for this check")
    category: str = Field(
        description="Category: completeness, validity, consistency, integrity, uniqueness"
    )
    description: str = Field(description="What this check validates")
    rationale: str = Field(
        description="Why this check matters for this specific domain/business"
    )
    sql_query: str = Field(description="SQL query to execute (returns count of violations)")
    severity: str = Field(description="critical, warning, or info based on business impact")
    expected_pass_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Expected percentage of rows that should pass (e.g., 0.95 = 95%)",
    )


class QualityCheckPlan(BaseModel):
    """Plan of quality checks for a table."""

    table_name: str
    checks: list[QualityCheck] = Field(
        description="List of 8-12 quality checks to run"
    )
    focus_areas: list[str] = Field(
        description="What aspects of quality this plan focuses on"
    )
    reasoning: str = Field(
        description="Overall rationale for this quality check strategy"
    )


QUALITY_GENERATION_PROMPT = """You are a data quality expert who generates contextual quality checks.

Database Context:
Domain: {domain}
Purpose: {purpose}
Business priorities: {priorities}
Data characteristics: {characteristics}

Table: {table_name}
Table purpose: {table_purpose}

Column Roles (semantic understanding):
{column_roles}

Column Profiles (statistics):
{column_profiles}

Sample Data:
{sample_data}

Generate 8-12 quality checks that are SPECIFIC to this data and domain.

For EACH check, you MUST provide:
1. A clear check_id (lowercase_with_underscores)
2. The category (completeness, validity, consistency, integrity, uniqueness)
3. Description of what you're checking
4. Rationale: Why this matters for THIS business/domain
5. SQL query that returns COUNT of violations (rows that fail the check)
6. Severity based on business impact (critical/warning/info)
7. Expected pass rate (what % should pass normally)

SQL Query Requirements:
- Must return a single row with a single column (count of violations)
- Use proper SQL syntax (SQLite compatible)
- Quote identifiers with double quotes if needed
- Return 0 if no violations

Examples of good checks:
- Range validation based on domain context
- Cross-column consistency (date1 < date2)
- Referential integrity
- Business rule validation
- Format validation for specific roles

Generate checks that make sense for THIS specific database, not generic rules."""


class QualityGenerationAgent:
    """Agent that generates context-aware quality checks."""

    def __init__(self):
        """Initialize quality generation agent."""
        self.model = get_model()
        self.agent = Agent(
            self.model,
            output_type=QualityCheckPlan,
            instructions=QUALITY_GENERATION_PROMPT,
            retries=3,
        )

    async def generate_checks(
        self,
        table_name: str,
        db_context: DatabaseContext,
        table_purpose: str,
        table_roles: TableRoles,
        column_profiles: list,
        sample_data: list[dict],
    ) -> QualityCheckPlan:
        """Generate quality checks for a table.

        Args:
            table_name: Name of the table
            db_context: Database context
            table_purpose: Purpose of this specific table
            table_roles: Classified roles for columns
            column_profiles: Statistical profiles
            sample_data: Sample rows

        Returns:
            QualityCheckPlan with generated checks
        """
        # Format inputs
        roles_text = self._format_roles(table_roles)
        profiles_text = self._format_profiles(column_profiles)
        samples_text = self._format_samples(sample_data)

        # Format the prompt with actual data
        prompt = QUALITY_GENERATION_PROMPT.format(
            domain=db_context.domain,
            purpose=db_context.purpose,
            priorities=", ".join(db_context.business_priorities),
            characteristics=db_context.data_characteristics,
            table_name=table_name,
            table_purpose=table_purpose,
            column_roles=roles_text,
            column_profiles=profiles_text,
            sample_data=samples_text,
        )

        # Run agent
        result = await self.agent.run(prompt)

        return result.output

    def _format_roles(self, table_roles: TableRoles) -> str:
        """Format column roles for prompt.

        Args:
            table_roles: TableRoles object

        Returns:
            Formatted string
        """
        formatted = []
        for role in table_roles.column_roles:
            formatted.append(
                f"- {role.column_name}: {role.semantic_role} "
                f"(confidence: {role.confidence:.2f}) - {role.reasoning}"
            )
        return "\n".join(formatted)

    def _format_profiles(self, column_profiles: list) -> str:
        """Format column profiles for prompt.

        Args:
            column_profiles: List of ColumnProfile objects

        Returns:
            Formatted string
        """
        formatted = []
        for col in column_profiles:
            stats = [
                f"{col.column_name} ({col.data_type})",
                f"null: {col.null_percentage:.1f}%",
                f"distinct: {col.distinct_count}",
            ]

            if col.mean is not None:
                stats.append(f"range: [{col.min_value}, {col.max_value}]")

            # Add top values for categorical columns (low cardinality)
            if col.top_values and col.distinct_count <= 20:
                top_vals = [str(val) for val, _ in col.top_values[:10]]
                stats.append(f"values: [{', '.join(top_vals)}]")

            formatted.append("  " + ", ".join(stats))

        return "\n".join(formatted)

    def _format_samples(self, sample_data: list[dict]) -> str:
        """Format sample data for prompt.

        Args:
            sample_data: List of sample rows

        Returns:
            Formatted string
        """
        if not sample_data:
            return "No sample data available"

        formatted = []
        for i, row in enumerate(sample_data[:3], 1):
            # Show first 8 columns
            sample_cols = list(row.items())[:8]
            row_str = ", ".join(f"{k}={v}" for k, v in sample_cols)
            formatted.append(f"Row {i}: {row_str}")

        return "\n".join(formatted)