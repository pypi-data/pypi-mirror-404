"""Semantic role classification for database columns."""

import re
from typing import Any
from urimai.storage.models import ColumnProfile


class RoleClassifier:
    """Classifies columns into semantic roles based on patterns."""

    # Role patterns (role_name, pattern, confidence)
    PATTERNS = [
        # IDs and Keys
        ("id", r"^(id|.*_id|pk|.*_pk)$", 0.9),
        ("foreign_key", r"^(fk_.*|.*_fk|.*_id)$", 0.8),

        # Personal Information
        ("email", r"^(email|e_mail|mail|email_address)$", 0.95),
        ("phone", r"^(phone|telephone|mobile|cell|phone_number)$", 0.9),
        ("name", r"^(name|full_name|first_name|last_name|fname|lname)$", 0.85),
        ("address", r"^(address|street|city|state|country|zip|postal)$", 0.8),
        ("age", r"^(age|years)$", 0.9),

        # Financial
        ("currency", r"^(price|cost|amount|salary|revenue|total|sum|balance)$", 0.85),

        # Temporal
        ("date", r"^(date|.*_date|.*_at|created|updated|modified|timestamp)$", 0.85),
        ("year", r"^(year|yr)$", 0.9),
        ("month", r"^(month|mon)$", 0.9),
        ("day", r"^(day)$", 0.85),

        # Status and Categories
        ("status", r"^(status|state|condition)$", 0.9),
        ("category", r"^(category|type|kind|class|group)$", 0.85),
        ("flag", r"^(is_.*|has_.*|.*_flag|active|enabled|verified)$", 0.8),

        # Content
        ("description", r"^(description|desc|details|notes|comments|content)$", 0.85),
        ("url", r"^(url|link|website|webpage)$", 0.9),

        # Geospatial
        ("coordinate", r"^(lat|latitude|lon|longitude|coordinates|location)$", 0.9),

        # Measurement
        ("quantity", r"^(quantity|qty|count|number|total)$", 0.8),
        ("percentage", r"^(.*_percent|.*_pct|.*_rate|percentage)$", 0.85),
    ]

    @staticmethod
    def classify_column(profile: ColumnProfile, sample_values: list[Any] = None) -> tuple[str, float]:
        """Classify a column's semantic role.

        Args:
            profile: ColumnProfile with statistics
            sample_values: Optional sample of actual values for content-based classification

        Returns:
            Tuple of (role, confidence)
        """
        column_name = profile.column_name.lower()

        # Pattern-based classification
        for role, pattern, confidence in RoleClassifier.PATTERNS:
            if re.match(pattern, column_name, re.IGNORECASE):
                return role, confidence

        # Content-based classification (if sample values provided)
        if sample_values:
            content_role = RoleClassifier._classify_by_content(profile, sample_values)
            if content_role:
                return content_role

        # Heuristic-based classification using statistics
        heuristic_role = RoleClassifier._classify_by_heuristics(profile)
        if heuristic_role:
            return heuristic_role

        # Default: unknown
        return "text", 0.3

    @staticmethod
    def _classify_by_content(profile: ColumnProfile, sample_values: list[Any]) -> tuple[str, float] | None:
        """Classify based on actual value content.

        Args:
            profile: ColumnProfile
            sample_values: Sample values to analyze

        Returns:
            Tuple of (role, confidence) or None
        """
        if not sample_values or profile.null_count == profile.row_count:
            return None

        # Remove nulls
        non_null_samples = [v for v in sample_values if v is not None][:100]
        if not non_null_samples:
            return None

        # Convert to strings for pattern matching
        string_samples = [str(v) for v in non_null_samples]

        # Email pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email_matches = sum(1 for s in string_samples if re.match(email_pattern, s))
        if email_matches / len(string_samples) > 0.8:
            return "email", 0.95

        # URL pattern
        url_pattern = r'^https?://.*'
        url_matches = sum(1 for s in string_samples if re.match(url_pattern, s))
        if url_matches / len(string_samples) > 0.8:
            return "url", 0.95

        # Phone pattern (basic international)
        phone_pattern = r'^[\+\d][\d\s\-\(\)]+$'
        phone_matches = sum(1 for s in string_samples if re.match(phone_pattern, s) and len(s) >= 7)
        if phone_matches / len(string_samples) > 0.7:
            return "phone", 0.85

        # Date-like patterns (ISO format, common formats)
        date_pattern = r'^\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'
        date_matches = sum(1 for s in string_samples if re.match(date_pattern, s))
        if date_matches / len(string_samples) > 0.8:
            return "date", 0.9

        return None

    @staticmethod
    def _classify_by_heuristics(profile: ColumnProfile) -> tuple[str, float] | None:
        """Classify using statistical heuristics.

        Args:
            profile: ColumnProfile with statistics

        Returns:
            Tuple of (role, confidence) or None
        """
        # High cardinality suggests ID
        if profile.distinct_percentage > 95 and profile.row_count > 100:
            return "id", 0.7

        # Low cardinality suggests category
        if profile.distinct_count < 20 and profile.row_count > 100:
            return "category", 0.6

        # Binary values suggest flag
        if profile.distinct_count == 2:
            return "flag", 0.7

        # Numeric with specific ranges
        if profile.mean is not None:
            # Year-like range
            if 1900 <= profile.mean <= 2100 and profile.min_value >= 1900:
                return "year", 0.75

            # Age-like range
            if 0 <= profile.mean <= 120 and profile.min_value >= 0 and profile.max_value <= 120:
                return "age", 0.7

            # Percentage-like (0-100 or 0-1)
            if 0 <= profile.min_value and profile.max_value <= 1:
                return "percentage", 0.65
            if 0 <= profile.min_value and profile.max_value <= 100:
                return "percentage", 0.6

        return None


def enrich_profile_with_roles(
    profile: ColumnProfile,
    sample_values: list[Any] = None
) -> ColumnProfile:
    """Enrich a column profile with role classification.

    Args:
        profile: ColumnProfile to enrich
        sample_values: Optional sample values for content-based classification

    Returns:
        ColumnProfile with inferred_role and role_confidence set
    """
    role, confidence = RoleClassifier.classify_column(profile, sample_values)
    profile.inferred_role = role
    profile.role_confidence = confidence
    return profile
