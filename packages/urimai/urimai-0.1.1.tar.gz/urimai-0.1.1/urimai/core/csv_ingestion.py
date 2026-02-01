"""CSV to SQLite ingestion module with LLM-powered schema inference."""

import re
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd


class CSVIngestionError(Exception):
    """Custom exception for CSV ingestion errors."""
    pass


def is_csv_file(path: Path) -> bool:
    """Check if file is a CSV file based on extension.

    Args:
        path: Path to file

    Returns:
        True if file has .csv or .tsv extension
    """
    return path.suffix.lower() in ['.csv', '.tsv']


def sanitize_identifier(name: str) -> str:
    """Sanitize table/column name for SQLite.

    Args:
        name: Original name

    Returns:
        Sanitized name (lowercase, alphanumeric + underscore only)
    """
    # Remove extension if present
    if '.' in name:
        name = Path(name).stem

    # Replace non-alphanumeric chars with underscore
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)

    # Remove leading/trailing underscores
    name = name.strip('_')

    # Ensure starts with letter (SQLite requirement)
    if name and not name[0].isalpha():
        name = 'table_' + name

    # Lowercase
    name = name.lower()

    return name or 'data'


async def read_csv_sample(
    csv_path: Path,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    has_header: bool = True,
    sample_size: int = 50,
) -> tuple[List[str], Dict[str, List[Any]], Dict[str, Dict[str, Any]]]:
    """Read sample data from CSV for schema inference with profiling.

    Args:
        csv_path: Path to CSV file
        delimiter: Column delimiter
        encoding: File encoding
        has_header: Whether CSV has header row
        sample_size: Number of rows to sample

    Returns:
        Tuple of (column_names, column_samples_dict, column_profiles_dict)

    Raises:
        CSVIngestionError: If CSV cannot be read
    """
    try:
        # Read CSV sample
        df = pd.read_csv(
            csv_path,
            delimiter=delimiter,
            encoding=encoding,
            header=0 if has_header else None,
            nrows=sample_size,
            low_memory=False,
            dtype=str,  # Read everything as string initially
        )

        # If no header, generate column names
        if not has_header:
            df.columns = [f'column_{i}' for i in range(len(df.columns))]

        # Sanitize column names
        original_columns = df.columns.tolist()
        df.columns = [sanitize_identifier(str(col)) for col in df.columns]

        # Check if empty
        if df.empty or len(df.columns) == 0:
            raise CSVIngestionError("CSV file is empty or has no columns")

        # Convert to dict of column samples and profile each column
        from urimai.core.profiling.column_profiler import ColumnProfiler

        column_samples = {}
        column_profiles = {}

        for col in df.columns:
            # Convert to list, preserve None for empty cells
            values = df[col].tolist()
            # Convert empty strings to None
            values = [v if (v and str(v).strip()) else None for v in values]
            column_samples[col] = values

            # Profile the column (use TEXT as temp type since we're inferring)
            profile = ColumnProfiler.profile_column(
                column_name=col,
                data_type='TEXT',  # Temporary, will be inferred
                values=values
            )

            # Convert to dict for easier use in prompt
            column_profiles[col] = {
                'null_count': profile.null_count,
                'null_percentage': profile.null_percentage,
                'distinct_count': profile.distinct_count,
                'distinct_percentage': profile.distinct_percentage,
                'top_values': profile.top_values[:5] if profile.top_values else [],  # Top 5 most common
            }

        return df.columns.tolist(), column_samples, column_profiles

    except pd.errors.EmptyDataError:
        raise CSVIngestionError("CSV file is empty")
    except pd.errors.ParserError as e:
        raise CSVIngestionError(f"Failed to parse CSV: {str(e)}")
    except Exception as e:
        raise CSVIngestionError(f"Failed to read CSV: {str(e)}")


def convert_value_to_type(value: Any, sqlite_type: str) -> Any:
    """Convert a value to the appropriate type for SQLite insertion.

    Args:
        value: Raw value from CSV
        sqlite_type: Target SQLite type (TEXT, INTEGER, REAL)

    Returns:
        Converted value or None
    """
    # Handle None/empty
    if value is None or (isinstance(value, str) and not value.strip()):
        return None

    try:
        if sqlite_type == 'INTEGER':
            # Handle boolean strings
            if isinstance(value, str):
                value_lower = value.lower().strip()
                if value_lower in ('true', 'yes', 'y', '1'):
                    return 1
                elif value_lower in ('false', 'no', 'n', '0'):
                    return 0
            return int(float(value))  # float() first to handle "123.0"

        elif sqlite_type == 'REAL':
            # Remove currency symbols, commas, etc.
            if isinstance(value, str):
                value = value.replace('$', '').replace(',', '').replace('%', '').strip()
            return float(value)

        elif sqlite_type == 'TEXT':
            return str(value).strip()

        else:
            # Default to TEXT
            return str(value)

    except (ValueError, TypeError):
        # If conversion fails, return as text or None
        return str(value) if value else None


async def create_sqlite_from_csv(
    csv_path: Path,
    output_dir: Path,
    table_name: Optional[str] = None,
    delimiter: str = ',',
    encoding: str = 'utf-8',
    has_header: bool = True,
    chunksize: int = 10000,
) -> tuple[Path, Dict[str, Any]]:
    """Create SQLite database from CSV file with LLM-inferred schema.

    Loads full CSV, profiles ALL data, and uses accurate statistics for schema inference.

    Args:
        csv_path: Path to CSV file
        output_dir: Directory to store SQLite database
        table_name: Custom table name (default: LLM-suggested or sanitized filename)
        delimiter: Column delimiter
        encoding: File encoding
        has_header: Whether CSV has header row
        chunksize: Unused (kept for backward compatibility)

    Returns:
        Tuple of (path_to_sqlite_db, ingestion_info)

    Raises:
        CSVIngestionError: If ingestion fails
    """
    try:
        # Validate CSV file exists
        if not csv_path.exists():
            raise CSVIngestionError(f"CSV file not found: {csv_path}")

        # Create output directory if needed
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Load FULL CSV into DataFrame (single read)
        df = pd.read_csv(
            csv_path,
            delimiter=delimiter,
            encoding=encoding,
            header=0 if has_header else None,
            low_memory=False,
            dtype=str,  # Read everything as string initially
        )

        # If no header, generate column names
        if not has_header:
            df.columns = [f'column_{i}' for i in range(len(df.columns))]

        # Sanitize column names
        df.columns = [sanitize_identifier(str(col)) for col in df.columns]

        # Check if empty
        if df.empty or len(df.columns) == 0:
            raise CSVIngestionError("CSV file is empty or has no columns")

        # Step 2: Profile ALL data (100% accurate)
        from urimai.core.profiling.column_profiler import ColumnProfiler

        column_samples = {}
        column_profiles = {}

        for col in df.columns:
            # Get all values from full DataFrame
            all_values = df[col].tolist()
            # Convert empty strings to None
            all_values = [v if (v and str(v).strip()) else None for v in all_values]

            # Only send first 50 samples to LLM (prompt size limit)
            column_samples[col] = all_values[:50]

            # Profile the ENTIRE column (accurate statistics)
            profile = ColumnProfiler.profile_column(
                column_name=col,
                data_type='TEXT',  # Temporary, will be inferred
                values=all_values
            )

            # Store profiling results
            column_profiles[col] = {
                'null_count': profile.null_count,
                'null_percentage': profile.null_percentage,
                'distinct_count': profile.distinct_count,
                'distinct_percentage': profile.distinct_percentage,
                'top_values': profile.top_values[:5] if profile.top_values else [],
            }

        # Step 3: Use LLM to infer schema with ACCURATE profiling data
        from urimai.agents.schema_inference_agent import SchemaInferenceAgent
        inference_agent = SchemaInferenceAgent()

        inferred_schema = await inference_agent.infer_schema(
            column_samples=column_samples,  # 50 samples for LLM context
            column_profiles=column_profiles,  # Stats from ALL rows
            filename=csv_path.name
        )

        # Use provided table name or LLM suggestion
        if table_name is None:
            table_name = sanitize_identifier(inferred_schema.suggested_table_name)
        else:
            table_name = sanitize_identifier(table_name)

        # Create SQLite database path
        db_path = output_dir / f"{csv_path.stem}.db"

        # Remove existing database if present
        if db_path.exists():
            db_path.unlink()

        # Create schema mapping
        column_type_map = {
            col.column_name: col.sqlite_type
            for col in inferred_schema.columns
        }

        # Step 4: Build CREATE TABLE with ACCURATE NOT NULL constraints
        column_defs = []
        for col_schema in inferred_schema.columns:
            col_def = f"{col_schema.column_name} {col_schema.sqlite_type}"

            # Use FULL data profiling (100% accurate, not sample)
            profile = column_profiles.get(col_schema.column_name, {})
            null_percentage = profile.get('null_percentage', 0)

            # Only add NOT NULL if column has zero nulls in ENTIRE dataset
            if null_percentage == 0:
                col_def += " NOT NULL"

            column_defs.append(col_def)

        create_table_sql = f"CREATE TABLE {table_name} (\n  " + ",\n  ".join(column_defs) + "\n)"

        # Step 5: Convert DataFrame values to proper types
        for col in df.columns:
            sqlite_type = column_type_map.get(col, 'TEXT')
            df[col] = df[col].apply(lambda v: convert_value_to_type(v, sqlite_type))

        # Step 6: Create SQLite database and write DataFrame
        conn = sqlite3.connect(db_path)

        try:
            # Create table
            conn.execute(create_table_sql)
            conn.commit()

            # Insert all data from DataFrame
            df.to_sql(
                table_name,
                conn,
                if_exists='append',
                index=False,
            )

            conn.commit()

            # Verify data was inserted
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]

            if row_count == 0:
                raise CSVIngestionError("No data was inserted into database")

            total_rows = row_count

        finally:
            conn.close()

        # Return ingestion info
        ingestion_info = {
            'table_name': table_name,
            'total_rows': total_rows,
            'num_columns': len(inferred_schema.columns),
            'inferred_schema': inferred_schema,
            'create_table_sql': create_table_sql,
        }

        return db_path, ingestion_info

    except CSVIngestionError:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        raise CSVIngestionError(
            f"Failed to create SQLite database: {str(e)}\n\n"
            f"Detailed traceback:\n{error_details}"
        )


def get_csv_info(csv_path: Path, delimiter: str = ',', encoding: str = 'utf-8') -> Dict[str, Any]:
    """Get basic information about a CSV file.

    Args:
        csv_path: Path to CSV file
        delimiter: Column delimiter
        encoding: File encoding

    Returns:
        Dictionary with CSV info (num_rows, num_columns, columns, size_mb)
    """
    try:
        # Count rows efficiently
        with open(csv_path, 'r', encoding=encoding) as f:
            num_rows = sum(1 for _ in f) - 1  # Subtract header

        # Read just header for column info
        df_sample = pd.read_csv(csv_path, delimiter=delimiter, encoding=encoding, nrows=0)

        # Get file size
        size_mb = csv_path.stat().st_size / (1024 * 1024)

        return {
            'num_rows': num_rows,
            'num_columns': len(df_sample.columns),
            'columns': list(df_sample.columns),
            'size_mb': round(size_mb, 2),
        }
    except Exception as e:
        raise CSVIngestionError(f"Failed to get CSV info: {str(e)}")
