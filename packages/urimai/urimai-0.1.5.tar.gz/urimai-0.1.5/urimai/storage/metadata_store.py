"""Metadata storage using SQLite."""

import json
import aiosqlite
from pathlib import Path
from typing import Any
from datetime import datetime

from urimai.storage.models import (
    DatabaseInfo,
    SchemaInfo,
    SettingInfo,
    TableProfile,
    QualityReport,
    InsightsReport,
)
from urimai.config import Config


# SQL Schema
CREATE_DATABASES_TABLE = """
CREATE TABLE IF NOT EXISTS databases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    path TEXT NOT NULL,
    database_context TEXT,
    created_at TEXT NOT NULL,
    last_synced_at TEXT NOT NULL
);
"""

MIGRATE_DATABASES_ADD_CONTEXT = """
ALTER TABLE databases ADD COLUMN database_context TEXT;
"""

CREATE_SCHEMAS_TABLE = """
CREATE TABLE IF NOT EXISTS schemas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    original_metadata TEXT NOT NULL,
    enriched_metadata TEXT,
    sample_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(database_id) REFERENCES databases(id) ON DELETE CASCADE,
    UNIQUE(database_id, table_name)
);
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

CREATE_TABLE_PROFILES_TABLE = """
CREATE TABLE IF NOT EXISTS table_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    column_count INTEGER NOT NULL,
    profile_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(database_id) REFERENCES databases(id) ON DELETE CASCADE,
    UNIQUE(database_id, table_name)
);
"""

CREATE_QUALITY_REPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS quality_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    overall_score REAL NOT NULL,
    completeness_score REAL NOT NULL,
    uniqueness_score REAL NOT NULL,
    validity_score REAL NOT NULL,
    consistency_score REAL NOT NULL,
    report_data TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(database_id) REFERENCES databases(id) ON DELETE CASCADE,
    UNIQUE(database_id, table_name)
);
"""

CREATE_INSIGHTS_REPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS insights_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    database_id INTEGER NOT NULL,
    table_name TEXT NOT NULL,
    insights_data TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(database_id) REFERENCES databases(id) ON DELETE CASCADE,
    UNIQUE(database_id, table_name)
);
"""


class MetadataStore:
    """Manages metadata storage in SQLite database."""

    def __init__(self, db_path: str | Path | None = None):
        """Initialize metadata store.

        Args:
            db_path: Path to metadata database. If None, uses Config.METADATA_DB_PATH
        """
        self.db_path = Path(db_path) if db_path else Config.get_metadata_db_path()

    async def initialize(self) -> None:
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_DATABASES_TABLE)
            await db.execute(CREATE_SCHEMAS_TABLE)
            await db.execute(CREATE_SETTINGS_TABLE)
            await db.execute(CREATE_TABLE_PROFILES_TABLE)
            await db.execute(CREATE_QUALITY_REPORTS_TABLE)
            await db.execute(CREATE_INSIGHTS_REPORTS_TABLE)

            # Migrations for existing databases
            try:
                await db.execute(MIGRATE_DATABASES_ADD_CONTEXT)
            except Exception:
                pass  # Column already exists

            await db.commit()

    # ========================================================================
    # Database Operations
    # ========================================================================

    async def add_database(self, db_info: DatabaseInfo) -> int:
        """Add a new database to the store.

        Args:
            db_info: Database information

        Returns:
            ID of the inserted database

        Raises:
            sqlite3.IntegrityError: If database name already exists
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO databases (name, path, database_context, created_at, last_synced_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    db_info.name,
                    db_info.path,
                    json.dumps(db_info.database_context) if db_info.database_context else None,
                    db_info.created_at,
                    db_info.last_synced_at,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_database(self, name: str) -> DatabaseInfo | None:
        """Get database by name.

        Args:
            name: Database name

        Returns:
            DatabaseInfo if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM databases WHERE name = ?", (name,)
            )
            row = await cursor.fetchone()

            if row:
                row_dict = dict(row)
                if row_dict.get("database_context"):
                    row_dict["database_context"] = json.loads(row_dict["database_context"])
                return DatabaseInfo(**row_dict)
            return None

    async def list_databases(self) -> list[DatabaseInfo]:
        """List all registered databases.

        Returns:
            List of DatabaseInfo objects
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM databases ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                row_dict = dict(row)
                if row_dict.get("database_context"):
                    row_dict["database_context"] = json.loads(row_dict["database_context"])
                results.append(DatabaseInfo(**row_dict))
            return results

    async def update_last_synced(self, database_id: int) -> None:
        """Update last_synced_at timestamp for a database.

        Args:
            database_id: Database ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE databases SET last_synced_at = ? WHERE id = ?",
                (datetime.now().isoformat(), database_id),
            )
            await db.commit()

    async def update_database_context(
        self, database_id: int, context: dict[str, Any]
    ) -> None:
        """Update the persisted database context.

        Args:
            database_id: Database ID
            context: DatabaseContext dict to persist
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE databases SET database_context = ? WHERE id = ?",
                (json.dumps(context), database_id),
            )
            await db.commit()

    async def delete_database(self, name: str) -> bool:
        """Delete a database and all its schemas.

        Args:
            name: Database name

        Returns:
            True if deleted, False if not found
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM databases WHERE name = ?", (name,))
            await db.commit()
            return cursor.rowcount > 0

    # ========================================================================
    # Schema Operations
    # ========================================================================

    async def add_schema(self, schema_info: SchemaInfo) -> int:
        """Add schema metadata for a table.

        Args:
            schema_info: Schema information

        Returns:
            ID of the inserted schema
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO schemas (database_id, table_name, original_metadata,
                                    enriched_metadata, sample_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(database_id, table_name) DO UPDATE SET
                    original_metadata = excluded.original_metadata,
                    enriched_metadata = excluded.enriched_metadata,
                    sample_data = excluded.sample_data,
                    created_at = excluded.created_at
                """,
                (
                    schema_info.database_id,
                    schema_info.table_name,
                    json.dumps(schema_info.original_metadata),
                    (
                        json.dumps(schema_info.enriched_metadata)
                        if schema_info.enriched_metadata
                        else None
                    ),
                    json.dumps(schema_info.sample_data),
                    schema_info.created_at,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_schemas(self, database_id: int) -> list[SchemaInfo]:
        """Get all schemas for a database.

        Args:
            database_id: Database ID

        Returns:
            List of SchemaInfo objects
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM schemas WHERE database_id = ? ORDER BY table_name",
                (database_id,),
            )
            rows = await cursor.fetchall()

            schemas = []
            for row in rows:
                row_dict = dict(row)
                row_dict["original_metadata"] = json.loads(row_dict["original_metadata"])
                row_dict["enriched_metadata"] = (
                    json.loads(row_dict["enriched_metadata"])
                    if row_dict["enriched_metadata"]
                    else None
                )
                row_dict["sample_data"] = json.loads(row_dict["sample_data"])
                schemas.append(SchemaInfo(**row_dict))

            return schemas

    async def update_enriched_metadata(
        self, database_id: int, table_name: str, enriched_metadata: dict[str, Any]
    ) -> None:
        """Update enriched metadata for a table.

        Args:
            database_id: Database ID
            table_name: Table name
            enriched_metadata: Enriched metadata dictionary
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE schemas
                SET enriched_metadata = ?
                WHERE database_id = ? AND table_name = ?
                """,
                (json.dumps(enriched_metadata), database_id, table_name),
            )
            await db.commit()

    async def delete_schemas(self, database_id: int) -> None:
        """Delete all schemas for a database.

        Args:
            database_id: Database ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM schemas WHERE database_id = ?", (database_id,))
            await db.commit()

    # ========================================================================
    # Settings Operations
    # ========================================================================

    async def get_setting(self, key: str, default: str | None = None) -> str | None:
        """Get a setting value.

        Args:
            key: Setting key
            default: Default value if not found

        Returns:
            Setting value or default
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else default

    async def set_setting(self, key: str, value: str) -> None:
        """Set a setting value.

        Args:
            key: Setting key
            value: Setting value
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )
            await db.commit()

    async def list_settings(self) -> list[SettingInfo]:
        """List all settings.

        Returns:
            List of SettingInfo objects
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM settings ORDER BY key")
            rows = await cursor.fetchall()
            return [SettingInfo(**dict(row)) for row in rows]

    # ========================================================================
    # Table Profile Operations
    # ========================================================================

    async def save_table_profile(self, profile: TableProfile) -> int:
        """Save or update a table profile.

        Args:
            profile: TableProfile object

        Returns:
            ID of the inserted/updated profile
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO table_profiles (database_id, table_name, row_count,
                                           column_count, profile_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(database_id, table_name) DO UPDATE SET
                    row_count = excluded.row_count,
                    column_count = excluded.column_count,
                    profile_data = excluded.profile_data,
                    created_at = excluded.created_at
                """,
                (
                    profile.database_id,
                    profile.table_name,
                    profile.row_count,
                    profile.column_count,
                    json.dumps([col.model_dump() for col in profile.columns]),
                    profile.created_at,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_table_profile(
        self, database_id: int, table_name: str
    ) -> TableProfile | None:
        """Get table profile by database ID and table name.

        Args:
            database_id: Database ID
            table_name: Table name

        Returns:
            TableProfile if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM table_profiles
                WHERE database_id = ? AND table_name = ?
                """,
                (database_id, table_name),
            )
            row = await cursor.fetchone()

            if row:
                row_dict = dict(row)
                row_dict["columns"] = json.loads(row_dict.pop("profile_data"))
                return TableProfile(**row_dict)
            return None

    async def list_table_profiles(self, database_id: int) -> list[TableProfile]:
        """List all table profiles for a database.

        Args:
            database_id: Database ID

        Returns:
            List of TableProfile objects
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM table_profiles WHERE database_id = ? ORDER BY table_name",
                (database_id,),
            )
            rows = await cursor.fetchall()

            profiles = []
            for row in rows:
                row_dict = dict(row)
                row_dict["columns"] = json.loads(row_dict.pop("profile_data"))
                profiles.append(TableProfile(**row_dict))

            return profiles

    # ========================================================================
    # Quality Report Operations
    # ========================================================================

    async def save_quality_report(self, report: QualityReport) -> int:
        """Save or update a quality report.

        Args:
            report: QualityReport object

        Returns:
            ID of the inserted/updated report
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO quality_reports (database_id, table_name, overall_score,
                                            completeness_score, uniqueness_score,
                                            validity_score, consistency_score,
                                            report_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(database_id, table_name) DO UPDATE SET
                    overall_score = excluded.overall_score,
                    completeness_score = excluded.completeness_score,
                    uniqueness_score = excluded.uniqueness_score,
                    validity_score = excluded.validity_score,
                    consistency_score = excluded.consistency_score,
                    report_data = excluded.report_data,
                    created_at = excluded.created_at
                """,
                (
                    report.database_id,
                    report.table_name,
                    report.overall_score,
                    report.completeness_score,
                    report.uniqueness_score,
                    report.validity_score,
                    report.consistency_score,
                    json.dumps([issue.model_dump() for issue in report.issues]),
                    report.created_at,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_quality_report(
        self, database_id: int, table_name: str
    ) -> QualityReport | None:
        """Get quality report by database ID and table name.

        Args:
            database_id: Database ID
            table_name: Table name

        Returns:
            QualityReport if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM quality_reports
                WHERE database_id = ? AND table_name = ?
                """,
                (database_id, table_name),
            )
            row = await cursor.fetchone()

            if row:
                row_dict = dict(row)
                row_dict["issues"] = json.loads(row_dict.pop("report_data"))
                return QualityReport(**row_dict)
            return None

    # ========================================================================
    # Insights Report Operations
    # ========================================================================

    async def save_insights_report(self, report: InsightsReport) -> int:
        """Save or update an insights report.

        Args:
            report: InsightsReport object

        Returns:
            ID of the inserted/updated report
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                INSERT INTO insights_reports (database_id, table_name,
                                             insights_data, summary, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(database_id, table_name) DO UPDATE SET
                    insights_data = excluded.insights_data,
                    summary = excluded.summary,
                    created_at = excluded.created_at
                """,
                (
                    report.database_id,
                    report.table_name,
                    json.dumps([insight.model_dump() for insight in report.insights]),
                    report.summary,
                    report.created_at,
                ),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_insights_report(
        self, database_id: int, table_name: str
    ) -> InsightsReport | None:
        """Get insights report by database ID and table name.

        Args:
            database_id: Database ID
            table_name: Table name

        Returns:
            InsightsReport if found, None otherwise
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM insights_reports
                WHERE database_id = ? AND table_name = ?
                """,
                (database_id, table_name),
            )
            row = await cursor.fetchone()

            if row:
                row_dict = dict(row)
                row_dict["insights"] = json.loads(row_dict.pop("insights_data"))
                return InsightsReport(**row_dict)
            return None
