"""Schema extraction and preparation for LLM enrichment."""

from typing import Any
from urimai.core.db_manager import DatabaseManager
from urimai.storage.models import SchemaInfo


class SchemaExtractor:
    """Extracts and prepares schema metadata from databases."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize schema extractor.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def extract_all_schemas(
        self, database_id: int, sample_rows: int = 5
    ) -> list[SchemaInfo]:
        """Extract schema information for all tables.

        Args:
            database_id: ID of the database in metadata store
            sample_rows: Number of sample rows to extract per table

        Returns:
            List of SchemaInfo objects
        """
        schemas = []

        # Get complete metadata from dq_db_manager
        complete_metadata = self.db_manager.get_complete_metadata()

        # Process each table
        for table_info in complete_metadata.get("tables", []):
            table_name = table_info["table_name"]

            # Get sample data
            sample_data = self.db_manager.get_sample_data(table_name, limit=sample_rows)

            # Create schema info
            schema = SchemaInfo(
                database_id=database_id,
                table_name=table_name,
                original_metadata=table_info,  # Full table metadata
                enriched_metadata=None,  # Will be populated by enrichment agent
                sample_data=sample_data,
            )
            schemas.append(schema)

        return schemas

    def build_database_context(self, all_schemas: list[SchemaInfo]) -> str:
        """Build a compact summary of all tables and their columns.

        Args:
            all_schemas: All schemas in the database

        Returns:
            Compact string listing all tables with their columns
        """
        lines = []
        for s in all_schemas:
            cols = [c["column_name"] for c in s.original_metadata.get("columns", [])]
            lines.append(f"- {s.table_name}({', '.join(cols)})")
        return "\n".join(lines)

    def prepare_for_enrichment(
        self, schema_info: SchemaInfo, database_context: str | None = None
    ) -> dict[str, Any]:
        """Prepare schema information for LLM enrichment.

        Args:
            schema_info: Schema information to prepare
            database_context: Compact summary of all tables in the database

        Returns:
            Dictionary formatted for LLM consumption
        """
        table_metadata = schema_info.original_metadata

        # Extract column information
        columns = []
        for col in table_metadata.get("columns", []):
            column_desc = {
                "name": col["column_name"],
                "type": col["data_type"],
                "nullable": col["is_nullable"],
            }
            if col.get("column_default"):
                column_desc["default"] = col["column_default"]
            columns.append(column_desc)

        # Extract constraints
        constraints = []
        for constraint in table_metadata.get("constraints", []):
            entry = {
                "name": constraint["constraint_name"],
                "type": constraint["constraint_type"],
            }
            if constraint.get("source_column"):
                entry["source_column"] = constraint["source_column"]
                entry["referenced_table"] = constraint["referenced_table"]
                entry["referenced_column"] = constraint["referenced_column"]
            constraints.append(entry)

        # Extract indexes
        indexes = []
        for index in table_metadata.get("indexes", []):
            indexes.append(
                {
                    "name": index["index_name"],
                    "definition": index.get("index_definition", ""),
                }
            )

        # Prepare sample data (convert to simplified format)
        sample_data_preview = []
        for row in schema_info.sample_data[:3]:  # Only include first 3 rows for LLM
            sample_data_preview.append(row)

        result = {
            "table_name": schema_info.table_name,
            "columns": columns,
            "constraints": constraints,
            "indexes": indexes,
            "sample_data": sample_data_preview,
            "row_count_in_sample": len(schema_info.sample_data),
        }
        if database_context:
            result["database_context"] = database_context
        return result

    def format_schema_for_query_agent(
        self, schemas: list[SchemaInfo]
    ) -> dict[str, Any]:
        """Format schemas for query generation agent.

        Args:
            schemas: List of schema information

        Returns:
            Dictionary formatted for query agent consumption
        """
        formatted_schemas = {}

        for schema in schemas:
            table_name = schema.table_name

            # Use enriched metadata if available, otherwise fall back to original
            if schema.enriched_metadata:
                enriched = schema.enriched_metadata
                formatted_schemas[table_name] = {
                    "purpose": enriched.get("table_purpose", ""),
                    "columns": enriched.get("column_descriptions", {}),
                    "relationships": enriched.get("relationships", []),
                    "business_context": enriched.get("business_context", ""),
                }
            else:
                # Fallback to basic column info
                columns = {}
                for col in schema.original_metadata.get("columns", []):
                    col_name = col["column_name"]
                    columns[col_name] = f"{col['data_type']} column"

                formatted_schemas[table_name] = {
                    "purpose": "Table in the database",
                    "columns": columns,
                    "relationships": [],
                    "business_context": "",
                }

        return formatted_schemas
