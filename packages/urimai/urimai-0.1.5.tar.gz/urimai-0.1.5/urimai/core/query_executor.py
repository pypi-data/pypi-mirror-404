"""Query execution with error handling and retry logic."""

import asyncio
from typing import Any
from urimai.core.db_manager import DatabaseManager
from urimai.config import Config


class QueryExecutionResult:
    """Result of query execution."""

    def __init__(
        self,
        success: bool,
        data: list[dict[str, Any]] | None = None,
        error: str | None = None,
        row_count: int = 0,
    ):
        """Initialize query execution result.

        Args:
            success: Whether query executed successfully
            data: Query results (list of row dictionaries)
            error: Error message if execution failed
            row_count: Number of rows returned
        """
        self.success = success
        self.data = data or []
        self.error = error
        self.row_count = row_count


class QueryExecutor:
    """Executes SQL queries with error handling."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize query executor.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    async def execute(self, sql_query: str) -> QueryExecutionResult:
        """Execute a SQL query with timeout protection.

        Args:
            sql_query: SQL query string to execute

        Returns:
            QueryExecutionResult with execution status and data/error
        """
        try:
            results = await asyncio.wait_for(
                asyncio.to_thread(self.db_manager.execute_query, sql_query),
                timeout=Config.QUERY_TIMEOUT,
            )

            return QueryExecutionResult(
                success=True,
                data=results,
                row_count=len(results),
            )

        except asyncio.TimeoutError:
            return QueryExecutionResult(
                success=False,
                error=(
                    f"Query timed out after {Config.QUERY_TIMEOUT} seconds. "
                    "The query is too slow — likely a cartesian join, missing index, or full table scan on a large table. "
                    "Simplify: add LIMIT, reduce joins, use indexed columns, or break into smaller queries."
                ),
            )

        except Exception as e:
            # Capture error details
            error_msg = str(e)

            # Common SQLite errors
            if "no such table" in error_msg.lower():
                error_msg = f"Table does not exist: {error_msg}"
            elif "no such column" in error_msg.lower():
                error_msg = f"Column does not exist: {error_msg}"
            elif "syntax error" in error_msg.lower():
                error_msg = f"SQL syntax error: {error_msg}"

            return QueryExecutionResult(
                success=False,
                error=error_msg,
            )

    def validate_query(self, sql_query: str) -> tuple[bool, str | None]:
        """Validate SQL query basic structure.

        Generic validation that works across SQL databases (SQLite, PostgreSQL, MySQL, etc.)

        Args:
            sql_query: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        if not sql_query or not sql_query.strip():
            return False, "Query is empty"

        # Normalize: strip comments and whitespace (works for all SQL dialects)
        normalized = self._normalize_query(sql_query)

        # Detect multiple statements (SQL injection risk - universal)
        if self._has_multiple_statements(normalized):
            return False, "Multiple statements not allowed (SQL injection risk)"

        # Check for dangerous operations (universal SQL keywords)
        dangerous_keywords = ["insert", "update", "delete", "drop", "truncate", "alter", "create", "replace"]
        normalized_lower = normalized.lower()
        for keyword in dangerous_keywords:
            if normalized_lower.startswith(keyword):
                return False, f"Dangerous operation not allowed: {keyword.upper()}"

        # Allow SELECT, WITH (CTEs), and EXPLAIN (all standard SQL)
        allowed_starts = ["select", "with", "explain"]
        if not any(normalized_lower.startswith(keyword) for keyword in allowed_starts):
            return False, "Only SELECT, WITH (CTEs), and EXPLAIN queries are allowed"

        # If WITH clause, ensure it's for SELECT (not INSERT/UPDATE/DELETE)
        if normalized_lower.startswith("with"):
            if not self._validate_cte_is_select_only(normalized):
                return False, "WITH clause must be used with SELECT (not INSERT/UPDATE/DELETE)"

        # TODO: Add database-specific validators (PostgreSQL, MySQL, etc.)
        # TODO: Add PRAGMA support for SQLite specifically
        # TODO: Add read-only mode per database type:
        #       - SQLite: URI mode with ?mode=ro
        #       - PostgreSQL: BEGIN TRANSACTION READ ONLY
        #       - MySQL: SET SESSION TRANSACTION READ ONLY
        # TODO: Add database-specific function validation
        # TODO: Consider using sqlparse library for robust parsing across dialects

        return True, None

    def _normalize_query(self, sql: str) -> str:
        """Remove comments and normalize whitespace (works for all SQL dialects).

        Args:
            sql: Raw SQL query

        Returns:
            Normalized SQL query
        """
        import re

        # Remove single-line comments (-- style)
        sql = re.sub(r'--[^\n]*', '', sql)

        # Remove multi-line comments (/* */ style)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)

        # Normalize whitespace
        return ' '.join(sql.split()).strip()

    def _has_multiple_statements(self, sql: str) -> bool:
        """Detect multiple statements (universal SQL injection vector).

        Checks for semicolons outside of string literals.

        Args:
            sql: Normalized SQL query

        Returns:
            True if multiple statements detected
        """
        in_string = False
        string_char = None

        for i, char in enumerate(sql):
            # Track string boundaries
            if char in ("'", '"'):
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char:
                    # Check for escaped quote (doubled quote)
                    if i + 1 < len(sql) and sql[i + 1] == char:
                        continue  # Skip escaped quote
                    in_string = False
                    string_char = None

            # Check for semicolon outside string
            elif char == ';' and not in_string:
                # Found semicolon outside string, check if there's content after
                remaining = sql[i + 1:].strip()
                if remaining:
                    return True

        return False

    def _validate_cte_is_select_only(self, sql: str) -> bool:
        """Ensure WITH clause ends with SELECT (generic SQL check).

        Args:
            sql: Normalized SQL query starting with WITH

        Returns:
            True if CTE is used with SELECT only
        """
        sql_upper = sql.upper()

        # Simple check: does it contain dangerous keywords after WITH?
        # These would indicate WITH...INSERT/UPDATE/DELETE which we don't allow
        dangerous = ['INSERT', 'UPDATE', 'DELETE', 'REPLACE']
        for keyword in dangerous:
            if keyword in sql_upper:
                return False

        # Must contain SELECT (all valid CTEs eventually have a SELECT)
        if 'SELECT' not in sql_upper:
            return False

        return True

        # TODO: More robust parsing for complex CTEs with nested subqueries
