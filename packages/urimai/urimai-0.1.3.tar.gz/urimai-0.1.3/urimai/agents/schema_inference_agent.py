"""Schema Inference Agent - Intelligently infers SQLite schema from CSV sample data."""

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import List, Dict, Any
from urimai.utils.llm import get_model


class ColumnSchema(BaseModel):
    """Inferred schema for a single column."""

    column_name: str = Field(description="Original column name")
    sqlite_type: str = Field(
        description="SQLite data type: TEXT, INTEGER, REAL, or BLOB"
    )
    reasoning: str = Field(
        description="Brief explanation of why this type was chosen"
    )
    should_be_nullable: bool = Field(
        description="Whether column should allow NULL values based on sample data"
    )
    detected_pattern: str = Field(
        description="Pattern detected (e.g., 'date_iso', 'currency', 'percentage', 'boolean', 'email', 'phone', etc.)"
    )


class InferredSchema(BaseModel):
    """Complete inferred schema for CSV table."""

    columns: List[ColumnSchema] = Field(
        description="Schema for each column"
    )
    suggested_table_name: str = Field(
        description="Suggested table name based on column analysis"
    )
    confidence: str = Field(
        description="Overall confidence level: high, medium, or low"
    )


class SchemaInferenceAgent:
    """Agent that infers optimal SQLite schema from CSV sample data."""

    def __init__(self):
        """Initialize the schema inference agent."""
        self.model = get_model()

        # System prompt for schema inference
        system_prompt = """You are an expert database schema designer specializing in type inference.

Your task is to analyze sample data from CSV files and infer the optimal SQLite schema.

**SQLite Type Guidelines:**

1. **INTEGER**: Use for:
   - Whole numbers (counts, IDs, years, ages, quantities)
   - Booleans (0/1, true/false, yes/no)
   - Zip codes (if no leading zeros)

2. **REAL**: Use for:
   - Decimal numbers (prices, percentages, measurements, ratings)
   - Scientific notation
   - Currency amounts

3. **TEXT**: Use for:
   - Dates/timestamps (store in ISO 8601 format: YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)
   - Strings (names, descriptions, addresses, categories)
   - IDs with letters (UUID, SKU codes)
   - Zip codes with leading zeros
   - Phone numbers, emails, URLs
   - Any mixed alphanumeric content

4. **BLOB**: Rarely used - only for binary data

**Pattern Detection:**
Identify common patterns to help with future data quality checks:
- date_iso: Dates in ISO format (YYYY-MM-DD)
- date_us: US dates (MM/DD/YYYY)
- date_eu: European dates (DD/MM/YYYY)
- datetime: Timestamps
- currency: Money amounts
- percentage: Percentages (0-100 or 0.0-1.0)
- email: Email addresses
- phone: Phone numbers
- url: Web URLs
- boolean: True/false values
- category: Limited distinct values
- id: Unique identifiers

**Analysis Approach:**
1. **Use profiling statistics** (null %, distinct count, top values) to guide type decisions
2. Examine sample values for each column
3. Look for patterns (date formats, number patterns, categories)
4. **Nullable decision**: Set should_be_nullable=true if null_percentage > 0
5. Choose the most specific type that fits ALL sample values
6. When in doubt, prefer TEXT over numeric types (safer for edge cases)
7. Suggest a meaningful table name based on column semantics

**Important:**
- **Prioritize profiling data**: Null percentage and distinct counts are more reliable than sample inspection alone
- Be conservative with numeric types - if ANY value has letters, use TEXT
- Dates should ALWAYS be TEXT in SQLite (we'll store as ISO 8601)
- High distinct percentage (>95%) often indicates IDs
- Low distinct count (<10) often indicates categories
- IDs can be INTEGER or TEXT depending on format
"""

        self.agent = Agent(
            self.model,
            output_type=InferredSchema,
            instructions=system_prompt,
            retries=3,
        )

    async def infer_schema(
        self,
        column_samples: Dict[str, List[Any]],
        column_profiles: Dict[str, Dict[str, Any]],
        filename: str = "data"
    ) -> InferredSchema:
        """Infer schema from sample column data with statistical profiling.

        Args:
            column_samples: Dictionary mapping column names to list of sample values
            column_profiles: Dictionary mapping column names to profiling statistics
            filename: Original CSV filename (used for table name suggestion)

        Returns:
            InferredSchema with type recommendations for each column
        """
        # Format the data for the LLM
        prompt_parts = [
            f"Analyze the following CSV data and infer the optimal SQLite schema.",
            f"\n**Original filename:** {filename}",
            f"\n**Number of columns:** {len(column_samples)}",
            f"\n**Sample data (first {len(next(iter(column_samples.values())))} rows):**\n"
        ]

        # Add sample data in readable format with profiling statistics
        for col_name, values in column_samples.items():
            prompt_parts.append(f"\n**Column: '{col_name}'**")

            # Add profiling statistics first (gives LLM context)
            profile = column_profiles.get(col_name, {})
            prompt_parts.append("Statistics:")
            prompt_parts.append(f"  • Total values: {len(values)}")
            prompt_parts.append(f"  • Null count: {profile.get('null_count', 0)} ({profile.get('null_percentage', 0):.1f}%)")
            prompt_parts.append(f"  • Distinct values: {profile.get('distinct_count', 0)} ({profile.get('distinct_percentage', 0):.1f}%)")

            # Show top values if available
            top_values = profile.get('top_values', [])
            if top_values:
                prompt_parts.append(f"  • Top values: {', '.join([f'{v[0]} ({v[1]}×)' for v in top_values[:3]])}")

            # Then show sample values
            prompt_parts.append("Sample values:")
            for i, val in enumerate(values[:15], 1):  # Show up to 15 samples
                # Handle None/NULL
                display_val = val if val is not None else "<NULL>"
                prompt_parts.append(f"  {i}. {display_val}")

        prompt_parts.append("\n\nProvide the inferred schema for all columns.")

        prompt = "\n".join(prompt_parts)

        # Run agent
        result = await self.agent.run(prompt)

        return result.output
