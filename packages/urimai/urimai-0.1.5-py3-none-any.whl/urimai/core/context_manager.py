"""Context Manager - Unified source of truth for database context.

This module provides a centralized way to access database context including:
- Schemas with enriched metadata
- Database domain understanding
- Column profiles
- Sample data

All agents (query generation, analysis, quality checks) should get context
from this manager to ensure consistency.
"""

from typing import Optional
from urimai.storage.metadata_store import MetadataStore
from urimai.storage.models import SchemaInfo, TableProfile
from urimai.agents.schema_context_agent import SchemaContextAgent, DatabaseContext
from urimai.agents.schema_selection_agent import SchemaSelectionAgent

TABLE_SELECTION_THRESHOLD = 6


class ContextManager:
    """Manages and caches database context for consistent access across agents."""

    def __init__(self, db_name: str):
        """Initialize context manager for a database.

        Args:
            db_name: Name of the registered database
        """
        self.db_name = db_name
        self.store: Optional[MetadataStore] = None
        self.db_id: Optional[int] = None

        # Cached context
        self._schemas: Optional[list[SchemaInfo]] = None
        self._db_context: Optional[DatabaseContext] = None
        self._profiles_cache: dict[str, TableProfile] = {}

        # Expose selection agent for usage tracking
        self._selection_agent: Optional[SchemaSelectionAgent] = None

    async def initialize(self) -> None:
        """Initialize the context manager by loading database info."""
        self.store = MetadataStore()
        await self.store.initialize()

        # Get database info
        db_info = await self.store.get_database(self.db_name)
        if not db_info:
            raise ValueError(f"Database '{self.db_name}' not found")

        self.db_id = db_info.id

        # Load schemas
        await self._load_schemas()

    async def _load_schemas(self) -> None:
        """Load all schemas from metadata store."""
        if not self.store or not self.db_id:
            raise RuntimeError("ContextManager not initialized")

        self._schemas = await self.store.get_schemas(self.db_id)

    async def get_schemas(self) -> list[SchemaInfo]:
        """Get all schemas with enriched metadata.

        Returns:
            List of SchemaInfo objects
        """
        if self._schemas is None:
            await self._load_schemas()

        return self._schemas or []

    async def get_database_context(self, force_refresh: bool = False) -> DatabaseContext:
        """Get or generate holistic database context.

        This provides domain understanding, business priorities, etc.
        Loads from persisted context first, falls back to LLM generation.
        Result is cached for performance.

        Args:
            force_refresh: If True, regenerate context even if cached/persisted

        Returns:
            DatabaseContext with domain understanding
        """
        # Return cached if available
        if self._db_context and not force_refresh:
            return self._db_context

        # Try loading from persisted context
        if not force_refresh and self.store and self.db_id:
            db_info = await self.store.get_database(self.db_name)
            if db_info and db_info.database_context:
                self._db_context = DatabaseContext(**db_info.database_context)
                return self._db_context

        # Generate new context via LLM
        schemas = await self.get_schemas()

        # Prepare enriched metadata and sample data
        enriched_metadata = {}
        sample_data = {}

        for schema in schemas:
            if schema.enriched_metadata:
                enriched_metadata[schema.table_name] = schema.enriched_metadata

            if schema.sample_data:
                sample_data[schema.table_name] = schema.sample_data

        # Use SchemaContextAgent to analyze
        context_agent = SchemaContextAgent()
        self._db_context = await context_agent.analyze_database(
            schemas=schemas,
            enriched_metadata=enriched_metadata,
            sample_data=sample_data,
        )

        # Persist for future use
        if self.store and self.db_id:
            await self.store.update_database_context(
                self.db_id, self._db_context.model_dump()
            )

        return self._db_context

    async def get_table_profile(self, table_name: str) -> Optional[TableProfile]:
        """Get statistical profile for a table.

        Profiles are cached for performance.

        Args:
            table_name: Name of the table

        Returns:
            TableProfile if exists, None otherwise
        """
        # Check cache first
        if table_name in self._profiles_cache:
            return self._profiles_cache[table_name]

        # Load from store
        if not self.store or not self.db_id:
            raise RuntimeError("ContextManager not initialized")

        profile = await self.store.get_table_profile(self.db_id, table_name)

        # Cache if found
        if profile:
            self._profiles_cache[table_name] = profile

        return profile

    async def get_enriched_schema_for_table(self, table_name: str) -> Optional[dict]:
        """Get enriched metadata for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            Enriched metadata dict or None if not available
        """
        schemas = await self.get_schemas()

        for schema in schemas:
            if schema.table_name == table_name:
                return schema.enriched_metadata

        return None

    async def format_context_for_query_agent(self, query: str | None = None) -> dict:
        """Format database context for query generation agent.

        When a query is provided and the database has more than TABLE_SELECTION_THRESHOLD
        tables, an intelligent selection agent filters to only relevant tables.
        For small databases (<= threshold), all tables are used.

        Args:
            query: Optional user question for intelligent table selection

        Returns:
            Dictionary with formatted context including selection metadata
        """
        schemas = await self.get_schemas()
        db_context = await self.get_database_context()

        # Determine whether to filter tables
        table_selection_skipped = True
        selected_tables = [s.table_name for s in schemas]
        selection_reasoning = None
        expansion_details: list[str] = []

        if query and len(schemas) > TABLE_SELECTION_THRESHOLD:
            table_selection_skipped = False

            # Build condensed summary and run selection agent
            schema_summary = self._build_schema_summary(schemas)
            if self._selection_agent is None:
                self._selection_agent = SchemaSelectionAgent()
            selection = await self._selection_agent.select_tables(query, schema_summary)

            selected_tables = selection.tables
            selection_reasoning = selection.reasoning

            # Expand with relationship neighbors
            selected_tables, expansion_details = self._expand_with_relationships(
                selected_tables, schemas, db_context
            )

            # Filter schemas to selected set
            schemas = [s for s in schemas if s.table_name in selected_tables]

        # Build rich schema descriptions
        tables_context = {}

        for schema in schemas:
            table_name = schema.table_name

            # Get enriched metadata
            enriched = schema.enriched_metadata or {}
            table_purpose = enriched.get("table_purpose", "Table in the database")

            # Get column descriptions
            column_descriptions = enriched.get("column_descriptions", {})

            # Get column profiles (if available) for value constraints
            profile = await self.get_table_profile(table_name)
            column_constraints = {}

            if profile:
                for col_profile in profile.columns:
                    constraints = {}

                    # Add value constraints for categorical columns
                    if col_profile.top_values and col_profile.distinct_count <= 20:
                        values = [str(val) for val, _ in col_profile.top_values]
                        constraints["valid_values"] = values

                    # Add range constraints for numeric columns
                    if col_profile.min_value is not None:
                        constraints["range"] = f"{col_profile.min_value} to {col_profile.max_value}"

                    if constraints:
                        column_constraints[col_profile.column_name] = constraints

            # Build table context with sample data
            tables_context[table_name] = {
                "purpose": table_purpose,
                "columns": column_descriptions if column_descriptions else self._basic_column_descriptions(schema),
                "column_constraints": column_constraints,
                "relationships": enriched.get("relationships", []),
                "sample_rows": schema.sample_data[:3] if schema.sample_data else [],
            }

        return {
            "domain": db_context.domain,
            "domain_confidence": db_context.domain_confidence,
            "database_purpose": db_context.purpose,
            "key_entities": db_context.key_entities,
            "data_characteristics": db_context.data_characteristics,
            "business_priorities": db_context.business_priorities,
            "tables": tables_context,
            "selected_tables": selected_tables,
            "selection_reasoning": selection_reasoning,
            "expansion_details": expansion_details,
            "table_selection_skipped": table_selection_skipped,
        }

    def _build_schema_summary(self, schemas: list[SchemaInfo]) -> str:
        """Build a condensed schema summary for the selection agent.

        Args:
            schemas: List of SchemaInfo objects

        Returns:
            Condensed string with table names, purposes, and column names
        """
        lines = []
        for schema in schemas:
            enriched = schema.enriched_metadata or {}
            purpose = enriched.get("table_purpose", "")
            columns = schema.original_metadata.get("columns", [])
            col_names = [c.get("column_name", c.get("name", "")) for c in columns]

            lines.append(f"Table: {schema.table_name}")
            if purpose:
                lines.append(f"  Purpose: {purpose}")
            lines.append(f"  Columns: {', '.join(col_names)}")
            lines.append("")

        return "\n".join(lines)

    def _expand_with_relationships(
        self,
        selected_tables: list[str],
        schemas: list[SchemaInfo],
        db_context: DatabaseContext,
    ) -> tuple[list[str], list[str]]:
        """Expand selected tables with directly-linked neighbors via foreign keys.

        Args:
            selected_tables: Tables chosen by the selection agent
            schemas: All schemas in the database
            db_context: Database context with refined relationships

        Returns:
            Tuple of (final_table_list, expansion_details)
        """
        all_table_names = {s.table_name for s in schemas}
        selected_set = set(selected_tables)
        expansion_details: list[str] = []

        # Check original_metadata for explicit FK constraints
        for schema in schemas:
            if schema.table_name not in selected_set:
                continue

            constraints = schema.original_metadata.get("constraints", [])
            for constraint in constraints:
                if constraint.get("constraint_type") == "FOREIGN KEY":
                    ref_table = constraint.get("referenced_table", "")
                    src_col = constraint.get("source_column", "")
                    if ref_table and ref_table in all_table_names and ref_table not in selected_set:
                        selected_set.add(ref_table)
                        expansion_details.append(
                            f"+ {ref_table} (linked via {src_col} from {schema.table_name})"
                        )

        # Also check if any non-selected table has an FK pointing to a selected table
        for schema in schemas:
            if schema.table_name in selected_set:
                continue

            constraints = schema.original_metadata.get("constraints", [])
            for constraint in constraints:
                if constraint.get("constraint_type") == "FOREIGN KEY":
                    ref_table = constraint.get("referenced_table", "")
                    src_col = constraint.get("source_column", "")
                    if ref_table in selected_set and schema.table_name not in selected_set:
                        # Only add if the refined_relationships also suggest a link
                        rels = db_context.refined_relationships.get(schema.table_name, [])
                        for rel in rels:
                            if ref_table in rel:
                                selected_set.add(schema.table_name)
                                expansion_details.append(
                                    f"+ {schema.table_name} (linked via {src_col} to {ref_table})"
                                )
                                break

        return list(selected_set), expansion_details

    def _basic_column_descriptions(self, schema: SchemaInfo) -> dict:
        """Generate basic column descriptions from original metadata.

        Fallback when enriched descriptions not available.

        Args:
            schema: SchemaInfo object

        Returns:
            Dict of column_name -> description
        """
        columns = schema.original_metadata.get("columns", [])
        descriptions = {}

        for col in columns:
            col_name = col.get("column_name", col.get("name", ""))
            col_type = col.get("data_type", col.get("type", ""))
            nullable = col.get("is_nullable", True)

            desc = f"{col_type} column"
            if not nullable:
                desc += " (required)"

            descriptions[col_name] = desc

        return descriptions

    async def refresh(self) -> None:
        """Refresh all cached context.

        Useful after schema changes or re-sync.
        """
        self._schemas = None
        self._db_context = None
        self._profiles_cache.clear()

        await self._load_schemas()
