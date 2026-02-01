"""Database manager wrapper for dq_db_manager."""

from pathlib import Path
from typing import Any
from dq_db_manager.database_factory import DatabaseFactory
from dq_db_manager.handlers.sqlite.db_handler import SQLiteDBHandler


class DatabaseManager:
    """Wrapper around dq_db_manager for SQLite operations."""

    def __init__(self, db_path: str | Path):
        """Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).resolve()
        self.connection_details = {"database": str(self.db_path)}
        self.handler: SQLiteDBHandler = DatabaseFactory.get_database_handler(
            "sqlite", self.connection_details
        )

    def test_connection(self) -> bool:
        """Test if database is accessible.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            return self.handler.connection_handler.test_connection()
        except Exception:
            return False

    def get_complete_metadata(self) -> dict[str, Any]:
        """Extract complete database metadata.

        Returns:
            Dictionary containing all metadata (tables, columns, constraints, etc.)
        """
        return self.handler.metadata_extractor.get_complete_metadata()

    def get_table_names(self) -> list[str]:
        """Get list of all table names.

        Returns:
            List of table names
        """
        tables = self.handler.metadata_extractor.extract_table_details(
            return_as_dict=True
        )
        return [table["table_name"] for table in tables]

    def get_table_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Get column details for a specific table.

        Args:
            table_name: Name of the table

        Returns:
            List of column details (name, type, nullable, default)
        """
        return self.handler.metadata_extractor.extract_column_details(
            table_name=table_name, return_as_dict=True
        )

    def get_sample_data(self, table_name: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get sample rows from a table.

        Args:
            table_name: Name of the table
            limit: Number of rows to retrieve (default: 5)

        Returns:
            List of row dictionaries
        """
        query = f"SELECT * FROM {table_name} LIMIT ?"
        return self.handler.connection_handler.execute_query(query, [limit])

    def execute_query(
        self, query: str, params: list[Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a SQL query.

        Args:
            query: SQL query string
            params: Optional query parameters (for parameterized queries)

        Returns:
            List of result rows as dictionaries
        """
        return self.handler.connection_handler.execute_query(query, params)

    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows in the table
        """
        result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
        return result[0]["count"] if result else 0
