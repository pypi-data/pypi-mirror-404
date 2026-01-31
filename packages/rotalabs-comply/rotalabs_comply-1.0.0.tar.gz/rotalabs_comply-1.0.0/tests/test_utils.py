"""Tests for utility functions."""

from datetime import datetime

import pytest

from rotalabs_comply.frameworks.base import RiskLevel
from rotalabs_comply.utils.helpers import (
    dump_json,
    format_period,
    json_serializer,
    load_json,
    parse_period,
    severity_weight,
)


class TestFormatPeriod:
    """Tests for format_period function."""

    def test_format_period_quarter(self):
        """Test formatting a full quarter as '2026-Q1'."""
        start = datetime(2026, 1, 1)
        end = datetime(2026, 3, 31)

        result = format_period(start, end)
        assert result == "2026-Q1"

        # Test Q2
        start_q2 = datetime(2026, 4, 1)
        end_q2 = datetime(2026, 6, 30)
        assert format_period(start_q2, end_q2) == "2026-Q2"

        # Test Q3
        start_q3 = datetime(2026, 7, 1)
        end_q3 = datetime(2026, 9, 30)
        assert format_period(start_q3, end_q3) == "2026-Q3"

        # Test Q4
        start_q4 = datetime(2026, 10, 1)
        end_q4 = datetime(2026, 12, 31)
        assert format_period(start_q4, end_q4) == "2026-Q4"

    def test_format_period_month(self):
        """Test formatting a full month as 'Jan 2026'."""
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)

        result = format_period(start, end)
        assert result == "Jan 2026"

        # Test February (non-leap year)
        start_feb = datetime(2026, 2, 1)
        end_feb = datetime(2026, 2, 28)
        assert format_period(start_feb, end_feb) == "Feb 2026"

        # Test December
        start_dec = datetime(2026, 12, 1)
        end_dec = datetime(2026, 12, 31)
        assert format_period(start_dec, end_dec) == "Dec 2026"

    def test_format_period_year(self):
        """Test formatting a full year as '2026'."""
        start = datetime(2026, 1, 1)
        end = datetime(2026, 12, 31)

        result = format_period(start, end)
        assert result == "2026"

    def test_format_period_custom_range(self):
        """Test formatting a custom date range."""
        start = datetime(2026, 1, 15)
        end = datetime(2026, 2, 20)

        result = format_period(start, end)
        assert result == "2026-01-15 to 2026-02-20"

    def test_format_period_cross_year(self):
        """Test formatting a range that crosses years."""
        start = datetime(2025, 11, 1)
        end = datetime(2026, 2, 28)

        result = format_period(start, end)
        assert result == "2025-11-01 to 2026-02-28"


class TestParsePeriod:
    """Tests for parse_period function."""

    def test_parse_period_quarter(self):
        """Parse '2026-Q1' to date range."""
        start, end = parse_period("2026-Q1")

        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end == datetime(2026, 3, 31, 23, 59, 59)

        # Test Q2
        start_q2, end_q2 = parse_period("2026-Q2")
        assert start_q2.month == 4
        assert end_q2.month == 6
        assert end_q2.day == 30

        # Test Q3
        start_q3, end_q3 = parse_period("2026-Q3")
        assert start_q3.month == 7
        assert end_q3.month == 9

        # Test Q4
        start_q4, end_q4 = parse_period("2026-Q4")
        assert start_q4.month == 10
        assert end_q4.month == 12
        assert end_q4.day == 31

    def test_parse_period_month(self):
        """Parse 'Jan 2026' to date range."""
        start, end = parse_period("Jan 2026")

        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end == datetime(2026, 1, 31, 23, 59, 59)

        # Test February
        start_feb, end_feb = parse_period("February 2026")
        assert start_feb.month == 2
        assert end_feb.day == 28

        # Test case insensitivity
        start_dec, end_dec = parse_period("dec 2026")
        assert start_dec.month == 12

    def test_parse_period_year(self):
        """Parse '2026' to full year date range."""
        start, end = parse_period("2026")

        assert start == datetime(2026, 1, 1, 0, 0, 0)
        assert end == datetime(2026, 12, 31, 23, 59, 59)

    def test_parse_period_date_range(self):
        """Parse '2026-01-15 to 2026-02-20' date range."""
        start, end = parse_period("2026-01-15 to 2026-02-20")

        assert start == datetime(2026, 1, 15, 0, 0, 0)
        assert end == datetime(2026, 2, 20, 23, 59, 59)

    def test_parse_period_invalid(self):
        """Test parsing invalid period raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            parse_period("invalid-period")

        assert "Cannot parse period" in str(exc_info.value)


class TestSeverityWeight:
    """Tests for severity_weight function."""

    def test_severity_weight_string(self):
        """Test weight values for string input."""
        assert severity_weight("critical") == 10
        assert severity_weight("high") == 5
        assert severity_weight("medium") == 2
        assert severity_weight("low") == 1
        assert severity_weight("info") == 1

    def test_severity_weight_enum(self):
        """Test weight values for RiskLevel enum input."""
        assert severity_weight(RiskLevel.CRITICAL) == 10
        assert severity_weight(RiskLevel.HIGH) == 5
        assert severity_weight(RiskLevel.MEDIUM) == 2
        assert severity_weight(RiskLevel.LOW) == 1
        assert severity_weight(RiskLevel.INFO) == 1

    def test_severity_weight_case_insensitive(self):
        """Test case insensitivity for string input."""
        assert severity_weight("CRITICAL") == 10
        assert severity_weight("Critical") == 10
        assert severity_weight("HIGH") == 5
        assert severity_weight("High") == 5

    def test_severity_weight_unknown(self):
        """Test unknown severity returns default weight."""
        assert severity_weight("unknown") == 1
        assert severity_weight("custom") == 1


class TestJsonSerializer:
    """Tests for json_serializer function."""

    def test_json_serializer_datetime(self):
        """Test datetime serialization."""
        dt = datetime(2026, 1, 15, 10, 30, 45)
        result = json_serializer(dt)

        assert result == "2026-01-15T10:30:45"

    def test_json_serializer_enum(self):
        """Test enum serialization."""
        result = json_serializer(RiskLevel.HIGH)
        assert result == "high"

    def test_json_serializer_bytes(self):
        """Test bytes serialization."""
        result = json_serializer(b"hello")
        assert result == "hello"

    def test_json_serializer_set(self):
        """Test set serialization."""
        result = json_serializer({1, 2, 3})
        assert isinstance(result, list)
        assert set(result) == {1, 2, 3}

    def test_json_serializer_object_with_dict(self):
        """Test objects with __dict__ are serialized to their dict."""

        class CustomClass:
            def __init__(self):
                self.data = {"key": "value"}
                self.count = 42

        result = json_serializer(CustomClass())
        assert isinstance(result, dict)
        assert result["count"] == 42
        assert result["data"] == {"key": "value"}


class TestDumpLoadJson:
    """Tests for dump_json and load_json functions."""

    def test_dump_json_load_json_roundtrip(self):
        """Test round-trip JSON serialization and deserialization."""
        original = {
            "timestamp": datetime(2026, 1, 15, 10, 30, 0),
            "name": "Test Entry",
            "count": 42,
            "values": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # Dump to JSON
        json_str = dump_json(original)
        assert isinstance(json_str, str)
        assert "2026-01-15T10:30:00" in json_str

        # Load back
        loaded = load_json(json_str)

        # Verify restoration
        assert isinstance(loaded["timestamp"], datetime)
        assert loaded["timestamp"] == original["timestamp"]
        assert loaded["name"] == original["name"]
        assert loaded["count"] == original["count"]
        assert loaded["values"] == original["values"]
        assert loaded["nested"] == original["nested"]

    def test_dump_json_with_indent(self):
        """Test dump_json with indentation."""
        data = {"key": "value", "number": 123}
        result = dump_json(data, indent=2)

        assert "\n" in result
        assert "  " in result

    def test_dump_json_with_risk_level(self):
        """Test dump_json with RiskLevel enum."""
        data = {
            "severity": RiskLevel.HIGH,
            "message": "Test",
        }

        result = dump_json(data)
        assert '"high"' in result

    def test_load_json_simple(self):
        """Test loading simple JSON."""
        json_str = '{"name": "test", "value": 42}'
        loaded = load_json(json_str)

        assert loaded["name"] == "test"
        assert loaded["value"] == 42

    def test_load_json_preserves_non_datetime_strings(self):
        """Test that non-datetime strings are preserved."""
        json_str = '{"name": "John Doe", "email": "john@example.com"}'
        loaded = load_json(json_str)

        assert loaded["name"] == "John Doe"
        assert loaded["email"] == "john@example.com"
        assert isinstance(loaded["name"], str)
