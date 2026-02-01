"""Completeness check - analyze missing values and null patterns."""

from urimai.storage.models import TableProfile, QualityIssue


class CompletenessChecker:
    """Checks data completeness by analyzing null values."""

    @staticmethod
    def check(table_profile: TableProfile) -> tuple[float, list[QualityIssue]]:
        """Check completeness of a table.

        Args:
            table_profile: TableProfile with column statistics

        Returns:
            Tuple of (completeness_score, list of issues)
        """
        issues = []
        null_percentages = []

        for col in table_profile.columns:
            null_pct = col.null_percentage
            null_percentages.append(null_pct)

            # Critical: Column is entirely null
            if null_pct == 100:
                issues.append(
                    QualityIssue(
                        severity="critical",
                        category="completeness",
                        column_name=col.column_name,
                        issue=f"Column is entirely NULL (no data)",
                        affected_rows=col.null_count,
                        recommendation="Consider removing this column or investigating why no data exists",
                    )
                )

            # Warning: High null rate (>50%)
            elif null_pct > 50:
                issues.append(
                    QualityIssue(
                        severity="warning",
                        category="completeness",
                        column_name=col.column_name,
                        issue=f"{null_pct:.1f}% of values are NULL",
                        affected_rows=col.null_count,
                        recommendation="Investigate why more than half the values are missing",
                    )
                )

            # Info: Moderate null rate (20-50%)
            elif null_pct > 20:
                issues.append(
                    QualityIssue(
                        severity="info",
                        category="completeness",
                        column_name=col.column_name,
                        issue=f"{null_pct:.1f}% of values are NULL",
                        affected_rows=col.null_count,
                        recommendation="Consider if this level of missingness is acceptable",
                    )
                )

        # Calculate overall completeness score
        # Score = 100 - average null percentage
        if null_percentages:
            avg_null_pct = sum(null_percentages) / len(null_percentages)
            completeness_score = max(0.0, 100.0 - avg_null_pct)
        else:
            completeness_score = 100.0

        return round(completeness_score, 2), issues
