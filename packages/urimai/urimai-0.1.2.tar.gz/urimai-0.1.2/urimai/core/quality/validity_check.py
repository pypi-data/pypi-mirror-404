"""Validity check - validate data types, ranges, and formats."""

from urimai.core.db_manager import DatabaseManager
from urimai.storage.models import TableProfile, QualityIssue


class ValidityChecker:
    """Checks data validity by validating types, ranges, and formats."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize validity checker.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db_manager = db_manager

    def check(
        self, table_name: str, table_profile: TableProfile
    ) -> tuple[float, list[QualityIssue]]:
        """Check validity of a table.

        Args:
            table_name: Name of the table
            table_profile: TableProfile with column statistics

        Returns:
            Tuple of (validity_score, list of issues)
        """
        issues = []

        for col in table_profile.columns:
            # Check range validity for numeric columns
            if col.mean is not None:
                range_issues = self._check_numeric_range(col)
                issues.extend(range_issues)

            # Check format validity based on inferred role
            if col.inferred_role:
                format_issues = self._check_format_validity(
                    table_name, col, table_profile.row_count
                )
                issues.extend(format_issues)

        # Calculate validity score
        # Start with 100, subtract points for issues
        total_rows = table_profile.row_count
        if total_rows == 0:
            return 100.0, issues

        total_invalid_rows = sum(i.affected_rows or 0 for i in issues)
        invalid_percentage = (total_invalid_rows / total_rows) * 100

        validity_score = max(0.0, 100.0 - invalid_percentage)

        return round(validity_score, 2), issues

    def _check_numeric_range(self, col) -> list[QualityIssue]:
        """Check if numeric values are in expected ranges.

        Args:
            col: ColumnProfile

        Returns:
            List of issues found
        """
        issues = []

        # Check age-like columns
        if col.inferred_role == "age":
            if col.min_value is not None and col.min_value < 0:
                issues.append(
                    QualityIssue(
                        severity="critical",
                        category="validity",
                        column_name=col.column_name,
                        issue=f"Age column has negative values (min: {col.min_value})",
                        affected_rows=None,
                        recommendation="Age values should be non-negative",
                    )
                )

            if col.max_value is not None and col.max_value > 150:
                issues.append(
                    QualityIssue(
                        severity="warning",
                        category="validity",
                        column_name=col.column_name,
                        issue=f"Age column has suspiciously high values (max: {col.max_value})",
                        affected_rows=None,
                        recommendation="Verify if maximum age value is realistic",
                    )
                )

        # Check currency/price columns
        if col.inferred_role == "currency":
            if col.min_value is not None and col.min_value < 0:
                issues.append(
                    QualityIssue(
                        severity="warning",
                        category="validity",
                        column_name=col.column_name,
                        issue=f"Currency column has negative values (min: {col.min_value})",
                        affected_rows=None,
                        recommendation="Verify if negative values are expected (refunds, discounts, etc.)",
                    )
                )

        # Check percentage columns
        if col.inferred_role == "percentage":
            if col.min_value is not None and (
                col.min_value < 0 or col.max_value > 100
            ):
                issues.append(
                    QualityIssue(
                        severity="warning",
                        category="validity",
                        column_name=col.column_name,
                        issue=f"Percentage column has values outside 0-100 range (min: {col.min_value}, max: {col.max_value})",
                        affected_rows=None,
                        recommendation="Verify if percentage values are in correct range",
                    )
                )

        # Check year columns
        if col.inferred_role == "year":
            if col.min_value is not None and (
                col.min_value < 1900 or col.max_value > 2100
            ):
                issues.append(
                    QualityIssue(
                        severity="info",
                        category="validity",
                        column_name=col.column_name,
                        issue=f"Year column has unusual values (min: {col.min_value}, max: {col.max_value})",
                        affected_rows=None,
                        recommendation="Verify if year values are in expected range (1900-2100)",
                    )
                )

        return issues

    def _check_format_validity(
        self, table_name: str, col, total_rows: int
    ) -> list[QualityIssue]:
        """Check if values match expected format for their role.

        Args:
            table_name: Name of the table
            col: ColumnProfile
            total_rows: Total number of rows in table

        Returns:
            List of issues found
        """
        issues = []

        # Only check if we have some data
        if col.null_count == total_rows:
            return issues

        try:
            # Check email format
            if col.inferred_role == "email":
                query = f"""
                    SELECT COUNT(*) as invalid_count
                    FROM {table_name}
                    WHERE {col.column_name} IS NOT NULL
                      AND {col.column_name} NOT LIKE '%@%'
                """
                result = self.db_manager.execute_query(query)
                if result:
                    invalid_count = result[0].get("invalid_count", 0)
                    if invalid_count > 0:
                        invalid_pct = (invalid_count / total_rows) * 100
                        issues.append(
                            QualityIssue(
                                severity="warning",
                                category="validity",
                                column_name=col.column_name,
                                issue=f"{invalid_count:,} email values ({invalid_pct:.1f}%) don't contain '@'",
                                affected_rows=invalid_count,
                                recommendation="Verify email format validity",
                            )
                        )

            # Check URL format
            if col.inferred_role == "url":
                query = f"""
                    SELECT COUNT(*) as invalid_count
                    FROM {table_name}
                    WHERE {col.column_name} IS NOT NULL
                      AND {col.column_name} NOT LIKE 'http%'
                """
                result = self.db_manager.execute_query(query)
                if result:
                    invalid_count = result[0].get("invalid_count", 0)
                    if invalid_count > 0:
                        invalid_pct = (invalid_count / total_rows) * 100
                        issues.append(
                            QualityIssue(
                                severity="info",
                                category="validity",
                                column_name=col.column_name,
                                issue=f"{invalid_count:,} URL values ({invalid_pct:.1f}%) don't start with 'http'",
                                affected_rows=invalid_count,
                                recommendation="Verify URL format (should start with http:// or https://)",
                            )
                        )

        except Exception:
            # If queries fail, skip format checks
            pass

        return issues
