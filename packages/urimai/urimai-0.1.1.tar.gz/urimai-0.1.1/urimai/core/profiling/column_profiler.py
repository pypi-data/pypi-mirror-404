"""Column-level profiling with statistics computation."""

import numpy as np
from scipy import stats
from typing import Any
from collections import Counter

from urimai.storage.models import ColumnProfile


class ColumnProfiler:
    """Computes statistical profiles for database columns."""

    @staticmethod
    def profile_column(
        column_name: str,
        data_type: str,
        values: list[Any],
    ) -> ColumnProfile:
        """Generate a complete statistical profile for a column.

        Args:
            column_name: Name of the column
            data_type: SQL data type
            values: List of all values in the column

        Returns:
            ColumnProfile with computed statistics
        """
        row_count = len(values)

        # Count nulls
        null_values = [v for v in values if v is None]
        null_count = len(null_values)
        null_percentage = (null_count / row_count * 100) if row_count > 0 else 0.0

        # Non-null values for further analysis
        non_null_values = [v for v in values if v is not None]

        # Distinct counts
        distinct_count = len(set(non_null_values))
        distinct_percentage = (
            (distinct_count / len(non_null_values) * 100)
            if len(non_null_values) > 0
            else 0.0
        )

        # Top values (most common)
        top_values = []
        if non_null_values:
            counter = Counter(non_null_values)
            top_values = counter.most_common(10)

        # Initialize profile with basic stats
        profile = ColumnProfile(
            column_name=column_name,
            data_type=data_type,
            row_count=row_count,
            null_count=null_count,
            null_percentage=round(null_percentage, 2),
            distinct_count=distinct_count,
            distinct_percentage=round(distinct_percentage, 2),
            top_values=top_values,
        )

        # Type-specific statistics
        if ColumnProfiler._is_numeric_type(data_type):
            ColumnProfiler._add_numeric_stats(profile, non_null_values)
        elif ColumnProfiler._is_string_type(data_type):
            ColumnProfiler._add_string_stats(profile, non_null_values)

        return profile

    @staticmethod
    def _is_numeric_type(data_type: str) -> bool:
        """Check if data type is numeric."""
        numeric_types = [
            "integer",
            "int",
            "bigint",
            "smallint",
            "tinyint",
            "real",
            "float",
            "double",
            "decimal",
            "numeric",
            "number",
        ]
        return any(nt in data_type.lower() for nt in numeric_types)

    @staticmethod
    def _is_string_type(data_type: str) -> bool:
        """Check if data type is string/text."""
        string_types = ["varchar", "char", "text", "string", "nvarchar", "nchar"]
        return any(st in data_type.lower() for st in string_types)

    @staticmethod
    def _add_numeric_stats(profile: ColumnProfile, values: list[Any]) -> None:
        """Add numeric statistics to profile.

        Args:
            profile: ColumnProfile to update (in-place)
            values: Non-null numeric values
        """
        if not values:
            return

        try:
            # Convert to numpy array for calculations
            numeric_values = np.array([float(v) for v in values if v is not None])

            if len(numeric_values) == 0:
                return

            # Basic stats
            profile.min_value = float(np.min(numeric_values))
            profile.max_value = float(np.max(numeric_values))
            profile.mean = float(np.mean(numeric_values))
            profile.median = float(np.median(numeric_values))
            profile.std_dev = float(np.std(numeric_values))

            # Quartiles
            profile.q1 = float(np.percentile(numeric_values, 25))
            profile.q3 = float(np.percentile(numeric_values, 75))

            # Skewness and kurtosis (require at least 3 values)
            if len(numeric_values) >= 3:
                profile.skewness = float(stats.skew(numeric_values))
                profile.kurtosis = float(stats.kurtosis(numeric_values))

            # Round all values
            profile.min_value = round(profile.min_value, 4)
            profile.max_value = round(profile.max_value, 4)
            profile.mean = round(profile.mean, 4)
            profile.median = round(profile.median, 4)
            profile.std_dev = round(profile.std_dev, 4)
            profile.q1 = round(profile.q1, 4)
            profile.q3 = round(profile.q3, 4)
            if profile.skewness is not None:
                profile.skewness = round(profile.skewness, 4)
            if profile.kurtosis is not None:
                profile.kurtosis = round(profile.kurtosis, 4)

        except (ValueError, TypeError) as e:
            # If conversion fails, skip numeric stats
            pass

    @staticmethod
    def _add_string_stats(profile: ColumnProfile, values: list[Any]) -> None:
        """Add string statistics to profile.

        Args:
            profile: ColumnProfile to update (in-place)
            values: Non-null string values
        """
        if not values:
            return

        try:
            # Convert all to strings
            string_values = [str(v) for v in values if v is not None]

            if not string_values:
                return

            lengths = [len(s) for s in string_values]

            profile.min_length = min(lengths)
            profile.max_length = max(lengths)
            profile.avg_length = round(sum(lengths) / len(lengths), 2)

        except (ValueError, TypeError):
            # If any operation fails, skip string stats
            pass


async def profile_table(
    db_path: str,
    table_name: str,
    database_id: int,
    schema_info: "SchemaInfo",
) -> "TableProfile":
    """Profile an entire table.

    Args:
        db_path: Path to the database
        table_name: Name of the table to profile
        database_id: Database ID for storage
        schema_info: SchemaInfo object with table metadata

    Returns:
        TableProfile with all column profiles
    """
    from urimai.core.db_manager import DatabaseManager
    from urimai.storage.models import TableProfile, SchemaInfo

    db_manager = DatabaseManager(db_path)

    # Use the schema_info passed in - no redundant metadata fetch!
    columns = schema_info.original_metadata.get("columns", [])

    # Get all rows for analysis
    query = f"SELECT * FROM {table_name}"
    rows = db_manager.execute_query(query)

    row_count = len(rows)
    column_count = len(columns)

    # Profile each column
    column_profiles = []

    for col in columns:
        col_name = col["column_name"]
        col_type = col.get("data_type", "unknown")

        # Extract column values
        col_values = [row.get(col_name) for row in rows]

        # Profile the column
        profile = ColumnProfiler.profile_column(col_name, col_type, col_values)
        column_profiles.append(profile)

    # Create table profile
    table_profile = TableProfile(
        database_id=database_id,
        table_name=table_name,
        row_count=row_count,
        column_count=column_count,
        columns=column_profiles,
    )

    return table_profile
