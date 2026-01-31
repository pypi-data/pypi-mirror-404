"""
Utility functions for rotalabs-comply.

This module provides helper functions for common operations like date
formatting, statistics calculation, and data serialization.

Functions:
    format_period: Format a date range as a readable period string.
    parse_period: Parse a period string back to date range.
    calculate_statistics: Calculate basic statistics from audit entries.
    group_by_date: Group entries by date with configurable granularity.
    severity_weight: Convert severity level to numeric weight.
    json_serializer: Custom JSON serializer for compliance types.

Example:
    >>> from rotalabs_comply.utils import format_period, parse_period
    >>> from datetime import datetime
    >>>
    >>> start = datetime(2026, 1, 1)
    >>> end = datetime(2026, 3, 31)
    >>> period = format_period(start, end)
    >>> print(period)
    '2026-Q1'
    >>>
    >>> parsed_start, parsed_end = parse_period("2026-Q1")
"""

from rotalabs_comply.utils.helpers import (
    calculate_statistics,
    dump_json,
    format_period,
    group_by_date,
    json_serializer,
    load_json,
    parse_period,
    severity_weight,
)

__all__ = [
    "format_period",
    "parse_period",
    "calculate_statistics",
    "group_by_date",
    "severity_weight",
    "json_serializer",
    "dump_json",
    "load_json",
]
