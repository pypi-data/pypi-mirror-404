# Utilities Module

Helper functions for date formatting, statistics calculation, and JSON serialization.

---

## Period Formatting

### format_period

```python
def format_period(start: datetime, end: datetime) -> str
```

Format a date range as a human-readable period string.

Automatically detects the most appropriate format based on the date range.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start` | `datetime` | Start of period |
| `end` | `datetime` | End of period |

**Returns:** Formatted period string

**Examples:**

```python
from datetime import datetime
from rotalabs_comply.utils import format_period

# Quarter
format_period(datetime(2026, 1, 1), datetime(2026, 3, 31))
# Returns: '2026-Q1'

# Month
format_period(datetime(2026, 1, 1), datetime(2026, 1, 31))
# Returns: 'Jan 2026'

# Year
format_period(datetime(2026, 1, 1), datetime(2026, 12, 31))
# Returns: '2026'

# Date range
format_period(datetime(2026, 1, 15), datetime(2026, 2, 20))
# Returns: '2026-01-15 to 2026-02-20'
```

---

### parse_period

```python
def parse_period(period: str) -> Tuple[datetime, datetime]
```

Parse a period string back to start and end datetimes.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | `str` | Period string to parse |

**Returns:** Tuple of (start_datetime, end_datetime)

**Raises:** `ValueError` if the period string cannot be parsed

**Supported formats:**
- `YYYY-Q#` (quarter)
- `YYYY` (year)
- `Mon YYYY` or `Month YYYY` (month)
- `YYYY-MM-DD to YYYY-MM-DD` (date range)
- ISO date format

**Examples:**

```python
from rotalabs_comply.utils import parse_period

# Quarter
start, end = parse_period("2026-Q1")
# start: datetime(2026, 1, 1, 0, 0)
# end: datetime(2026, 3, 31, 23, 59, 59)

# Month
start, end = parse_period("Jan 2026")
# start: datetime(2026, 1, 1, 0, 0)
# end: datetime(2026, 1, 31, 23, 59, 59)

# Year
start, end = parse_period("2026")
# start: datetime(2026, 1, 1, 0, 0)
# end: datetime(2026, 12, 31, 23, 59, 59)

# Date range
start, end = parse_period("2026-01-15 to 2026-02-20")
# start: datetime(2026, 1, 15, 0, 0)
# end: datetime(2026, 2, 20, 23, 59, 59)
```

---

## Statistics

### calculate_statistics

```python
def calculate_statistics(entries: Sequence[Any]) -> Dict[str, Any]
```

Calculate basic statistics from audit entries.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `entries` | `Sequence[Any]` | List of audit entries (dict or object) |

**Expected entry attributes:**
- `timestamp`
- `safety_passed`
- `latency_ms`
- `provider`
- `model`
- `detectors_triggered`

**Returns:**

| Key | Type | Description |
|-----|------|-------------|
| `total_entries` | `int` | Total count |
| `safety_passed` | `int` | Entries passing safety |
| `safety_failed` | `int` | Entries failing safety |
| `safety_rate` | `float` | Pass percentage (0-100) |
| `avg_latency_ms` | `float` | Average latency |
| `min_latency_ms` | `float` | Minimum latency |
| `max_latency_ms` | `float` | Maximum latency |
| `providers` | `Dict[str, int]` | Provider counts |
| `models` | `Dict[str, int]` | Model counts |
| `detectors` | `Dict[str, int]` | Detector trigger counts |

**Example:**

```python
from rotalabs_comply.utils import calculate_statistics

entries = [
    {"safety_passed": True, "latency_ms": 100.0, "provider": "openai"},
    {"safety_passed": True, "latency_ms": 150.0, "provider": "openai"},
    {"safety_passed": False, "latency_ms": 200.0, "provider": "anthropic"},
]

stats = calculate_statistics(entries)
print(stats["total_entries"])  # 3
print(stats["safety_rate"])    # 66.67
print(stats["providers"])      # {"openai": 2, "anthropic": 1}
```

---

### group_by_date

```python
def group_by_date(
    entries: Sequence[Any],
    granularity: Literal["day", "week", "month", "quarter", "year"] = "day",
) -> Dict[str, List[Any]]
```

Group audit entries by date with configurable granularity.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entries` | `Sequence[Any]` | Required | Entries with timestamp |
| `granularity` | `str` | `"day"` | Time granularity |

**Granularity options:**

| Value | Key Format | Example |
|-------|------------|---------|
| `"day"` | `YYYY-MM-DD` | `2026-01-15` |
| `"week"` | `YYYY-WNN` | `2026-W03` |
| `"month"` | `YYYY-MM` | `2026-01` |
| `"quarter"` | `YYYY-Q#` | `2026-Q1` |
| `"year"` | `YYYY` | `2026` |

**Returns:** Dictionary mapping period keys to lists of entries (sorted by key)

**Example:**

```python
from rotalabs_comply.utils import group_by_date

entries = [
    {"timestamp": "2026-01-15T10:00:00"},
    {"timestamp": "2026-01-15T14:00:00"},
    {"timestamp": "2026-01-16T09:00:00"},
]

# By day
grouped = group_by_date(entries, granularity="day")
# {'2026-01-15': [entry1, entry2], '2026-01-16': [entry3]}

# By month
grouped = group_by_date(entries, granularity="month")
# {'2026-01': [entry1, entry2, entry3]}
```

---

### severity_weight

```python
def severity_weight(severity: Union[str, RiskLevel]) -> int
```

Convert a severity level to a numeric weight for scoring.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `severity` | `Union[str, RiskLevel]` | Severity level |

**Returns:** Numeric weight (1-10)

**Weight mapping:**

| Severity | Weight |
|----------|--------|
| `critical` | 10 |
| `high` | 5 |
| `medium` | 2 |
| `low` | 1 |
| `info` | 1 |

**Example:**

```python
from rotalabs_comply.utils import severity_weight
from rotalabs_comply.frameworks.base import RiskLevel

severity_weight("critical")        # 10
severity_weight("high")            # 5
severity_weight(RiskLevel.MEDIUM)  # 2
```

---

## JSON Serialization

### json_serializer

```python
def json_serializer(obj: Any) -> Any
```

Custom JSON serializer for compliance-specific types.

Handles:
- `datetime` -> ISO format string
- `Enum` -> `.value`
- Dataclasses -> dict via `asdict()`
- Pydantic models -> `.model_dump()` or `.dict()`
- Objects with `to_dict()` method
- Objects with `__dict__`
- `bytes` -> UTF-8 decoded string
- `set` -> list
- `timedelta` -> total seconds

**Raises:** `TypeError` if object cannot be serialized

**Example:**

```python
import json
from datetime import datetime
from rotalabs_comply.utils import json_serializer
from rotalabs_comply.frameworks.base import RiskLevel

data = {
    "timestamp": datetime(2026, 1, 15, 10, 30),
    "status": RiskLevel.HIGH,
}

json.dumps(data, default=json_serializer)
# '{"timestamp": "2026-01-15T10:30:00", "status": "high"}'
```

---

### dump_json

```python
def dump_json(obj: Any, **kwargs) -> str
```

Serialize object to JSON string with compliance type support.

Convenience wrapper around `json.dumps` with `json_serializer`.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `obj` | `Any` | Object to serialize |
| `**kwargs` | | Arguments passed to `json.dumps` |

**Example:**

```python
from datetime import datetime
from rotalabs_comply.utils import dump_json

data = {"created": datetime(2026, 1, 15)}
print(dump_json(data))
# {"created": "2026-01-15T00:00:00"}

print(dump_json(data, indent=2))
# {
#   "created": "2026-01-15T00:00:00"
# }
```

---

### load_json

```python
def load_json(data: str) -> Any
```

Parse JSON string with datetime restoration.

Automatically converts ISO format strings back to datetime objects.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `str` | JSON string to parse |

**Returns:** Parsed Python object with datetimes restored

**Example:**

```python
from rotalabs_comply.utils import load_json

data = '{"timestamp": "2026-01-15T10:30:00"}'
obj = load_json(data)
print(type(obj["timestamp"]))
# <class 'datetime.datetime'>
```

---

## Usage Examples

### Complete Statistics Pipeline

```python
from datetime import datetime, timedelta
from rotalabs_comply.utils import (
    format_period,
    calculate_statistics,
    group_by_date,
    dump_json,
)

# Sample entries
entries = [...]

# Calculate overall statistics
stats = calculate_statistics(entries)
print(f"Total: {stats['total_entries']}")
print(f"Safety Rate: {stats['safety_rate']}%")

# Group by time
daily = group_by_date(entries, granularity="day")
weekly = group_by_date(entries, granularity="week")

# Analyze trends
for period, period_entries in daily.items():
    period_stats = calculate_statistics(period_entries)
    print(f"{period}: {period_stats['total_entries']} entries")

# Export to JSON
report = {
    "period": format_period(
        datetime(2026, 1, 1),
        datetime(2026, 3, 31)
    ),
    "statistics": stats,
    "daily_breakdown": {
        period: calculate_statistics(entries)
        for period, entries in daily.items()
    },
}

json_output = dump_json(report, indent=2)
```

### Period-Based Reporting

```python
from rotalabs_comply.utils import format_period, parse_period

# Format for display
period_str = format_period(start, end)
print(f"Reporting Period: {period_str}")

# Parse from user input
user_input = "2026-Q1"
start, end = parse_period(user_input)

# Generate report for parsed period
report = await generator.generate(
    period_start=start,
    period_end=end,
    profile=profile,
)
```
