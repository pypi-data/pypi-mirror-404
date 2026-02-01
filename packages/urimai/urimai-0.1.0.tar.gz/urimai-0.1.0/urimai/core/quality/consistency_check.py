"""Consistency check - validate logical consistency and relationships."""

from urimai.core.db_manager import DatabaseManager
from urimai.storage.models import TableProfile, QualityIssue


class ConsistencyChecker:
    """Checks data consistency by validating logical rules."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize consistency checker.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def check(
        self, table_name: str, table_profile: TableProfile
    ) -> tuple[float, list[QualityIssue]]:
        """Check consistency of a table.

        Args:
            table_name: Name of the table
            table_profile: TableProfile with column statistics

        Returns:
            Tuple of (consistency_score, list of issues)
        """
        issues = []

        # Check for common date consistency issues
        date_issues = self._check_date_consistency(table_name, table_profile)
        issues.extend(date_issues)

        # Check for cross-column consistency
        cross_column_issues = self._check_cross_column_consistency(
            table_name, table_profile
        )
        issues.extend(cross_column_issues)

        # Calculate consistency score
        # Penalize based on number and severity of issues
        critical_issues = sum(1 for i in issues if i.severity == "critical")
        warning_issues = sum(1 for i in issues if i.severity == "warning")

        penalty = (critical_issues * 25) + (warning_issues * 10)
        consistency_score = max(0.0, 100.0 - penalty)

        return round(consistency_score, 2), issues

    def _check_date_consistency(
        self, table_name: str, table_profile: TableProfile
    ) -> list[QualityIssue]:
        """Check for date consistency issues.

        Args:
            table_name: Name of the table
            table_profile: TableProfile

        Returns:
            List of issues found
        """
        issues = []

        # Find date columns
        date_columns = [
            col.column_name
            for col in table_profile.columns
            if col.inferred_role == "date" or "date" in col.column_name.lower()
        ]

        # Check for common date pairs
        date_pairs = [
            ("start_date", "end_date"),
            ("begin_date", "end_date"),
            ("created_at", "updated_at"),
            ("created", "updated"),
            ("from_date", "to_date"),
            ("birth_date", "death_date"),
        ]

        for start_col, end_col in date_pairs:
            # Check if both columns exist
            if start_col in date_columns and end_col in date_columns:
                try:
                    query = f"""
                        SELECT COUNT(*) as violation_count
                        FROM {table_name}
                        WHERE {start_col} IS NOT NULL
                          AND {end_col} IS NOT NULL
                          AND {start_col} > {end_col}
                    """
                    result = self.db_manager.execute_query(query)
                    if result:
                        violation_count = result[0].get("violation_count", 0)
                        if violation_count > 0:
                            issues.append(
                                QualityIssue(
                                    severity="critical",
                                    category="consistency",
                                    column_name=f"{start_col}, {end_col}",
                                    issue=f"{violation_count:,} rows where {start_col} > {end_col}",
                                    affected_rows=violation_count,
                                    recommendation=f"Start date should not be after end date",
                                )
                            )
                except Exception:
                    # Query might fail if columns don't support comparison
                    pass

        return issues

    def _check_cross_column_consistency(
        self, table_name: str, table_profile: TableProfile
    ) -> list[QualityIssue]:
        """Check for cross-column consistency issues.

        Args:
            table_name: Name of the table
            table_profile: TableProfile

        Returns:
            List of issues found
        """
        issues = []

        # Check for source == destination patterns
        column_pairs = [
            ("source", "destination"),
            ("from", "to"),
            ("sender", "receiver"),
            ("origin", "destination"),
            ("source_id", "destination_id"),
            ("from_id", "to_id"),
        ]

        all_columns = [col.column_name.lower() for col in table_profile.columns]

        for col1_name, col2_name in column_pairs:
            # Check if both columns exist (case-insensitive)
            col1_actual = next(
                (
                    col.column_name
                    for col in table_profile.columns
                    if col.column_name.lower() == col1_name
                ),
                None,
            )
            col2_actual = next(
                (
                    col.column_name
                    for col in table_profile.columns
                    if col.column_name.lower() == col2_name
                ),
                None,
            )

            if col1_actual and col2_actual:
                try:
                    query = f"""
                        SELECT COUNT(*) as violation_count
                        FROM {table_name}
                        WHERE {col1_actual} IS NOT NULL
                          AND {col2_actual} IS NOT NULL
                          AND {col1_actual} = {col2_actual}
                    """
                    result = self.db_manager.execute_query(query)
                    if result:
                        violation_count = result[0].get("violation_count", 0)
                        if violation_count > 0:
                            total_rows = table_profile.row_count
                            violation_pct = (
                                (violation_count / total_rows) * 100
                                if total_rows > 0
                                else 0
                            )

                            # Only warn if it's a significant percentage
                            if violation_pct > 5:
                                issues.append(
                                    QualityIssue(
                                        severity="warning",
                                        category="consistency",
                                        column_name=f"{col1_actual}, {col2_actual}",
                                        issue=f"{violation_count:,} rows ({violation_pct:.1f}%) where {col1_actual} = {col2_actual}",
                                        affected_rows=violation_count,
                                        recommendation=f"Verify if {col1_name} should differ from {col2_name}",
                                    )
                                )
                except Exception:
                    # Query might fail for various reasons
                    pass

        # Check for negative values in quantity/count columns
        quantity_patterns = ["quantity", "count", "amount", "qty", "total", "sum"]
        for col in table_profile.columns:
            if col.mean is not None:  # Numeric column
                col_lower = col.column_name.lower()
                if any(pattern in col_lower for pattern in quantity_patterns):
                    if col.min_value is not None and col.min_value < 0:
                        issues.append(
                            QualityIssue(
                                severity="warning",
                                category="consistency",
                                column_name=col.column_name,
                                issue=f"Quantity/count column has negative values (min: {col.min_value})",
                                affected_rows=None,
                                recommendation="Verify if negative quantities are valid",
                            )
                        )

        return issues
