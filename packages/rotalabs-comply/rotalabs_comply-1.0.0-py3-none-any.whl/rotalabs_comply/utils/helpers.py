"""
Utility helper functions for rotalabs-comply.

This module provides common utility functions used throughout the compliance
package, including date formatting, statistics calculation, and serialization.

Example:
    >>> from rotalabs_comply.utils.helpers import format_period, severity_weight
    >>> from datetime import datetime
    >>>
    >>> period = format_period(datetime(2026, 1, 1), datetime(2026, 3, 31))
    >>> print(period)
    '2026-Q1'
    >>>
    >>> weight = severity_weight("critical")
    >>> print(weight)
    10
"""

from __future__ import annotations

import calendar
import json
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Literal, Sequence, Tuple, Union

from rotalabs_comply.frameworks.base import RiskLevel


def format_period(start: datetime, end: datetime) -> str:
    """
    Format a date range as a human-readable period string.

    Automatically detects the most appropriate format based on the
    date range (quarter, month, year, or date range).

    Args:
        start: Start of the period.
        end: End of the period.

    Returns:
        Formatted period string (e.g., "2026-Q1", "Jan 2026", "2026",
        or "2026-01-01 to 2026-03-15").

    Examples:
        >>> from datetime import datetime
        >>> format_period(datetime(2026, 1, 1), datetime(2026, 3, 31))
        '2026-Q1'

        >>> format_period(datetime(2026, 1, 1), datetime(2026, 1, 31))
        'Jan 2026'

        >>> format_period(datetime(2026, 1, 1), datetime(2026, 12, 31))
        '2026'

        >>> format_period(datetime(2026, 1, 15), datetime(2026, 2, 20))
        '2026-01-15 to 2026-02-20'
    """
    # Check if same year
    if start.year != end.year:
        return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"

    year = start.year

    # Check if full year
    if start.month == 1 and start.day == 1 and end.month == 12 and end.day == 31:
        return str(year)

    # Check if full quarter
    quarter_starts = {1: 1, 4: 2, 7: 3, 10: 4}
    quarter_ends = {3: 1, 6: 2, 9: 3, 12: 4}

    if (
        start.day == 1
        and start.month in quarter_starts
        and end.month in quarter_ends
        and quarter_starts[start.month] == quarter_ends[end.month]
    ):
        # Verify end day is last day of month
        _, last_day = calendar.monthrange(end.year, end.month)
        if end.day == last_day:
            return f"{year}-Q{quarter_starts[start.month]}"

    # Check if full month
    if start.day == 1 and start.month == end.month:
        _, last_day = calendar.monthrange(end.year, end.month)
        if end.day == last_day:
            return start.strftime("%b %Y")

    # Default to date range
    return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"


def parse_period(period: str) -> Tuple[datetime, datetime]:
    """
    Parse a period string back to start and end datetimes.

    Supports various period formats including quarters, months, years,
    and explicit date ranges.

    Args:
        period: Period string to parse (e.g., "2026-Q1", "Jan 2026",
            "2026", or "2026-01-01 to 2026-03-31").

    Returns:
        Tuple of (start_datetime, end_datetime).

    Raises:
        ValueError: If the period string cannot be parsed.

    Examples:
        >>> parse_period("2026-Q1")
        (datetime(2026, 1, 1, 0, 0), datetime(2026, 3, 31, 23, 59, 59))

        >>> parse_period("Jan 2026")
        (datetime(2026, 1, 1, 0, 0), datetime(2026, 1, 31, 23, 59, 59))

        >>> parse_period("2026")
        (datetime(2026, 1, 1, 0, 0), datetime(2026, 12, 31, 23, 59, 59))

        >>> parse_period("2026-01-15 to 2026-02-20")
        (datetime(2026, 1, 15, 0, 0), datetime(2026, 2, 20, 23, 59, 59))
    """
    period = period.strip()

    # Try quarter format: YYYY-Q#
    quarter_match = re.match(r"^(\d{4})-Q([1-4])$", period)
    if quarter_match:
        year = int(quarter_match.group(1))
        quarter = int(quarter_match.group(2))
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        _, last_day = calendar.monthrange(year, end_month)
        return (
            datetime(year, start_month, 1, 0, 0, 0),
            datetime(year, end_month, last_day, 23, 59, 59),
        )

    # Try year format: YYYY
    if re.match(r"^\d{4}$", period):
        year = int(period)
        return (
            datetime(year, 1, 1, 0, 0, 0),
            datetime(year, 12, 31, 23, 59, 59),
        )

    # Try month format: Mon YYYY or Month YYYY
    month_match = re.match(r"^(\w+)\s+(\d{4})$", period)
    if month_match:
        month_str = month_match.group(1)
        year = int(month_match.group(2))

        # Parse month name
        month_names = {
            "jan": 1, "january": 1,
            "feb": 2, "february": 2,
            "mar": 3, "march": 3,
            "apr": 4, "april": 4,
            "may": 5,
            "jun": 6, "june": 6,
            "jul": 7, "july": 7,
            "aug": 8, "august": 8,
            "sep": 9, "september": 9,
            "oct": 10, "october": 10,
            "nov": 11, "november": 11,
            "dec": 12, "december": 12,
        }

        month = month_names.get(month_str.lower())
        if month:
            _, last_day = calendar.monthrange(year, month)
            return (
                datetime(year, month, 1, 0, 0, 0),
                datetime(year, month, last_day, 23, 59, 59),
            )

    # Try date range format: YYYY-MM-DD to YYYY-MM-DD
    range_match = re.match(
        r"^(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})$",
        period,
    )
    if range_match:
        start = datetime.strptime(range_match.group(1), "%Y-%m-%d")
        end = datetime.strptime(range_match.group(2), "%Y-%m-%d")
        return (
            start.replace(hour=0, minute=0, second=0),
            end.replace(hour=23, minute=59, second=59),
        )

    # Try ISO date format
    try:
        dt = datetime.fromisoformat(period)
        return (
            dt.replace(hour=0, minute=0, second=0),
            dt.replace(hour=23, minute=59, second=59),
        )
    except ValueError:
        pass

    raise ValueError(
        f"Cannot parse period: {period}. "
        "Expected formats: 'YYYY-Q#', 'Mon YYYY', 'YYYY', "
        "'YYYY-MM-DD to YYYY-MM-DD'"
    )


def calculate_statistics(entries: Sequence[Any]) -> Dict[str, Any]:
    """
    Calculate basic statistics from audit entries.

    Computes volume, safety, performance, and distribution metrics
    from a collection of audit entries.

    Args:
        entries: List of audit entries (dict or object with standard attributes).
            Expected attributes: timestamp, safety_passed, latency_ms,
            provider, model, detectors_triggered.

    Returns:
        Dictionary containing calculated statistics:
            - total_entries: Total number of entries
            - safety_passed: Number passing safety checks
            - safety_failed: Number failing safety checks
            - safety_rate: Percentage of entries passing (0-100)
            - avg_latency_ms: Average response latency
            - min_latency_ms: Minimum latency
            - max_latency_ms: Maximum latency
            - providers: Dict of provider -> count
            - models: Dict of model -> count
            - detectors: Dict of detector -> trigger count

    Example:
        >>> entries = [
        ...     {"safety_passed": True, "latency_ms": 100.0, "provider": "openai"},
        ...     {"safety_passed": True, "latency_ms": 150.0, "provider": "openai"},
        ...     {"safety_passed": False, "latency_ms": 200.0, "provider": "anthropic"},
        ... ]
        >>> stats = calculate_statistics(entries)
        >>> print(stats["total_entries"])
        3
        >>> print(stats["safety_rate"])
        66.67
    """
    if not entries:
        return {
            "total_entries": 0,
            "safety_passed": 0,
            "safety_failed": 0,
            "safety_rate": 100.0,
            "avg_latency_ms": 0.0,
            "min_latency_ms": 0.0,
            "max_latency_ms": 0.0,
            "providers": {},
            "models": {},
            "detectors": {},
        }

    total = len(entries)
    safety_passed = 0
    latencies: List[float] = []
    providers: Dict[str, int] = {}
    models: Dict[str, int] = {}
    detectors: Dict[str, int] = {}

    for entry in entries:
        # Handle both dict and object access
        if isinstance(entry, dict):
            passed = entry.get("safety_passed", True)
            latency = entry.get("latency_ms", 0.0)
            provider = entry.get("provider", "unknown") or "unknown"
            model = entry.get("model", "unknown") or "unknown"
            triggered = entry.get("detectors_triggered", []) or []
        else:
            passed = getattr(entry, "safety_passed", True)
            latency = getattr(entry, "latency_ms", 0.0)
            provider = getattr(entry, "provider", "unknown") or "unknown"
            model = getattr(entry, "model", "unknown") or "unknown"
            triggered = getattr(entry, "detectors_triggered", []) or []

        if passed:
            safety_passed += 1

        if latency is not None:
            latencies.append(float(latency))

        providers[provider] = providers.get(provider, 0) + 1
        models[model] = models.get(model, 0) + 1

        for detector in triggered:
            detectors[detector] = detectors.get(detector, 0) + 1

    safety_failed = total - safety_passed
    safety_rate = (safety_passed / total * 100) if total > 0 else 100.0

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0

    return {
        "total_entries": total,
        "safety_passed": safety_passed,
        "safety_failed": safety_failed,
        "safety_rate": round(safety_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "min_latency_ms": round(min_latency, 2),
        "max_latency_ms": round(max_latency, 2),
        "providers": providers,
        "models": models,
        "detectors": detectors,
    }


def group_by_date(
    entries: Sequence[Any],
    granularity: Literal["day", "week", "month", "quarter", "year"] = "day",
) -> Dict[str, List[Any]]:
    """
    Group audit entries by date with configurable granularity.

    Organizes entries into buckets based on the specified time granularity,
    useful for trend analysis and time-series reporting.

    Args:
        entries: List of audit entries with timestamp attribute/key.
        granularity: Time granularity for grouping:
            - "day": Group by YYYY-MM-DD
            - "week": Group by YYYY-WNN (ISO week)
            - "month": Group by YYYY-MM
            - "quarter": Group by YYYY-Q#
            - "year": Group by YYYY

    Returns:
        Dictionary mapping period keys to lists of entries.

    Example:
        >>> entries = [
        ...     {"timestamp": "2026-01-15T10:00:00"},
        ...     {"timestamp": "2026-01-15T14:00:00"},
        ...     {"timestamp": "2026-01-16T09:00:00"},
        ... ]
        >>> grouped = group_by_date(entries, granularity="day")
        >>> print(list(grouped.keys()))
        ['2026-01-15', '2026-01-16']

        >>> grouped = group_by_date(entries, granularity="month")
        >>> print(list(grouped.keys()))
        ['2026-01']
    """
    groups: Dict[str, List[Any]] = {}

    for entry in entries:
        # Extract timestamp
        if isinstance(entry, dict):
            ts = entry.get("timestamp")
        else:
            ts = getattr(entry, "timestamp", None)

        if ts is None:
            continue

        # Parse timestamp if string
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
        elif not isinstance(ts, datetime):
            continue

        # Generate key based on granularity
        if granularity == "day":
            key = ts.strftime("%Y-%m-%d")
        elif granularity == "week":
            # ISO week number
            key = ts.strftime("%Y-W%V")
        elif granularity == "month":
            key = ts.strftime("%Y-%m")
        elif granularity == "quarter":
            quarter = (ts.month - 1) // 3 + 1
            key = f"{ts.year}-Q{quarter}"
        elif granularity == "year":
            key = str(ts.year)
        else:
            key = ts.strftime("%Y-%m-%d")

        if key not in groups:
            groups[key] = []
        groups[key].append(entry)

    # Sort by key
    return dict(sorted(groups.items()))


def severity_weight(severity: Union[str, RiskLevel]) -> int:
    """
    Convert a severity level to a numeric weight for scoring.

    Higher weights indicate more severe issues. Useful for calculating
    weighted compliance scores and prioritizing violations.

    Args:
        severity: Severity level as string or RiskLevel enum.
            Valid values: "critical", "high", "medium", "low", "info".

    Returns:
        Numeric weight (1-10).

    Example:
        >>> severity_weight("critical")
        10

        >>> severity_weight("high")
        5

        >>> severity_weight(RiskLevel.MEDIUM)
        2

        >>> severity_weight("info")
        1
    """
    # Convert RiskLevel to string if needed
    if isinstance(severity, RiskLevel):
        severity_str = severity.value
    elif hasattr(severity, "value"):
        severity_str = severity.value
    else:
        severity_str = str(severity)

    weights = {
        "critical": 10,
        "high": 5,
        "medium": 2,
        "low": 1,
        "info": 1,
    }

    return weights.get(severity_str.lower(), 1)


def json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for compliance-specific types.

    Handles serialization of datetime objects, enums, dataclasses,
    and other types not natively supported by the json module.

    Args:
        obj: Object to serialize.

    Returns:
        JSON-serializable representation of the object.

    Raises:
        TypeError: If the object cannot be serialized.

    Example:
        >>> import json
        >>> from datetime import datetime
        >>>
        >>> data = {
        ...     "timestamp": datetime(2026, 1, 15, 10, 30),
        ...     "status": RiskLevel.HIGH,
        ... }
        >>> json.dumps(data, default=json_serializer)
        '{"timestamp": "2026-01-15T10:30:00", "status": "high"}'

        >>> # Use with json.dump
        >>> with open("output.json", "w") as f:
        ...     json.dump(data, f, default=json_serializer)
    """
    # Handle datetime
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle Enum types
    if isinstance(obj, Enum):
        return obj.value

    # Handle objects with value attribute (custom enums)
    if hasattr(obj, "value"):
        return obj.value

    # Handle dataclasses
    if hasattr(obj, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(obj)

    # Handle objects with to_dict method
    if hasattr(obj, "to_dict"):
        return obj.to_dict()

    # Handle Pydantic models
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):  # Pydantic v1
        return obj.dict()

    # Handle objects with __dict__
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    # Handle bytes
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")

    # Handle sets
    if isinstance(obj, set):
        return list(obj)

    # Handle timedelta
    if isinstance(obj, timedelta):
        return obj.total_seconds()

    # Fallback to string representation
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def dump_json(obj: Any, **kwargs) -> str:
    """
    Serialize object to JSON string with compliance type support.

    Convenience wrapper around json.dumps that automatically uses
    the custom serializer for compliance types.

    Args:
        obj: Object to serialize.
        **kwargs: Additional arguments passed to json.dumps.

    Returns:
        JSON formatted string.

    Example:
        >>> from datetime import datetime
        >>> data = {"created": datetime(2026, 1, 15)}
        >>> print(dump_json(data))
        {"created": "2026-01-15T00:00:00"}

        >>> print(dump_json(data, indent=2))
        {
          "created": "2026-01-15T00:00:00"
        }
    """
    return json.dumps(obj, default=json_serializer, **kwargs)


def load_json(data: str) -> Any:
    """
    Parse JSON string with datetime restoration.

    Automatically converts ISO format strings back to datetime objects
    when loading JSON data.

    Args:
        data: JSON string to parse.

    Returns:
        Parsed Python object with datetimes restored.

    Example:
        >>> data = '{"timestamp": "2026-01-15T10:30:00"}'
        >>> obj = load_json(data)
        >>> print(type(obj["timestamp"]))
        <class 'datetime.datetime'>
    """

    def datetime_hook(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Try to convert string values to datetime."""
        for key, value in obj.items():
            if isinstance(value, str):
                # Try ISO format
                try:
                    obj[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
        return obj

    return json.loads(data, object_hook=datetime_hook)
