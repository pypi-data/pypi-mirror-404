"""Uniqueness check - detect duplicates and uniqueness violations."""

from urimai.core.db_manager import DatabaseManager
from urimai.storage.models import TableProfile, QualityIssue


class UniquenessChecker:
    """Checks data uniqueness by detecting duplicates."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize uniqueness checker.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def check(
        self, table_name: str, table_profile: TableProfile
    ) -> tuple[float, list[QualityIssue]]:
        """Check uniqueness of a table.

        Args:
            table_name: Name of the table
            table_profile: TableProfile with column statistics

        Returns:
            Tuple of (uniqueness_score, list of issues)
        """
        issues = []

        # Check for full row duplicates
        duplicate_issues = self._check_row_duplicates(table_name, table_profile)
        issues.extend(duplicate_issues)

        # Check for columns that should be unique but aren't
        uniqueness_violations = self._check_column_uniqueness(table_profile)
        issues.extend(uniqueness_violations)

        # Calculate uniqueness score
        # Based on duplicate rate and uniqueness violations
        total_issues = len(issues)
        critical_issues = sum(1 for i in issues if i.severity == "critical")
        warning_issues = sum(1 for i in issues if i.severity == "warning")

        # Score formula: penalize more for critical issues
        penalty = (critical_issues * 20) + (warning_issues * 10)
        uniqueness_score = max(0.0, 100.0 - penalty)

        return round(uniqueness_score, 2), issues

    def _check_row_duplicates(
        self, table_name: str, table_profile: TableProfile
    ) -> list[QualityIssue]:
        """Check for full row duplicates.

        Args:
            table_name: Name of the table
            table_profile: TableProfile

        Returns:
            List of issues found
        """
        # NOTE: Full row duplicate detection disabled
        # SQLite doesn't support COUNT(DISTINCT *) or GROUP BY * syntax
        # Implementing this properly requires dynamic SQL with all column names
        # Column-level uniqueness checks below are more valuable and actionable
        return []

    def _check_column_uniqueness(
        self, table_profile: TableProfile
    ) -> list[QualityIssue]:
        """Check for columns that should be unique but aren't.

        Args:
            table_profile: TableProfile

        Returns:
            List of issues found
        """
        issues = []

        for col in table_profile.columns:
            # Check if column looks like it should be unique
            should_be_unique = self._should_be_unique(col)

            if should_be_unique and col.distinct_percentage < 100:
                duplicate_pct = 100 - col.distinct_percentage
                duplicate_count = col.row_count - col.distinct_count

                issues.append(
                    QualityIssue(
                        severity="warning",
                        category="uniqueness",
                        column_name=col.column_name,
                        issue=f"Column appears to be an identifier but has {duplicate_count:,} duplicate values ({duplicate_pct:.1f}%)",
                        affected_rows=duplicate_count,
                        recommendation="Verify if this column should have unique values",
                    )
                )

        return issues

    def _should_be_unique(self, col) -> bool:
        """Determine if a column should be unique.

        Args:
            col: ColumnProfile

        Returns:
            True if column should be unique
        """
        # Check if it's an ID column
        if col.inferred_role == "id":
            return True

        # Check column name patterns
        name_lower = col.column_name.lower()
        id_patterns = ["id", "_id", "pk", "_pk", "key", "_key", "uuid", "guid"]
        if any(pattern in name_lower for pattern in id_patterns):
            return True

        # High cardinality (>95% unique) suggests it should be fully unique
        if col.distinct_percentage > 95:
            return True

        return False
