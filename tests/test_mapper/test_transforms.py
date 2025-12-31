# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for transform functions."""

from datetime import datetime

import pytest

from ccda2omop.mapper.transforms import (
    TRANSFORMS,
    format_source_value,
    get_transform,
    transform_date,
    transform_float,
    transform_int,
    transform_none,
    transform_string,
    transform_time_ptr,
)


class TestTransformNone:
    """Tests for transform_none function."""

    def test_transform_none_passthrough(self):
        """Test that transform_none returns value unchanged."""
        assert transform_none("test") == "test"
        assert transform_none(123) == 123
        assert transform_none(None) is None
        assert transform_none([1, 2, 3]) == [1, 2, 3]


class TestTransformString:
    """Tests for transform_string function."""

    def test_transform_string_from_string(self):
        """Test converting string to string."""
        assert transform_string("hello") == "hello"

    def test_transform_string_from_int(self):
        """Test converting int to string."""
        assert transform_string(123) == "123"

    def test_transform_string_from_float(self):
        """Test converting float to string."""
        assert transform_string(3.14) == "3.14"

    def test_transform_string_from_none(self):
        """Test converting None to empty string."""
        assert transform_string(None) == ""


class TestTransformInt:
    """Tests for transform_int function."""

    def test_transform_int_from_string(self):
        """Test converting string to int."""
        assert transform_int("123") == 123

    def test_transform_int_from_float(self):
        """Test converting float to int."""
        assert transform_int(3.14) == 3

    def test_transform_int_from_int(self):
        """Test int remains int."""
        assert transform_int(42) == 42

    def test_transform_int_from_none(self):
        """Test converting None returns None."""
        assert transform_int(None) is None

    def test_transform_int_invalid_string(self):
        """Test converting invalid string returns None."""
        assert transform_int("not a number") is None

    def test_transform_int_from_list(self):
        """Test converting list returns None."""
        assert transform_int([1, 2, 3]) is None


class TestTransformFloat:
    """Tests for transform_float function."""

    def test_transform_float_from_string(self):
        """Test converting string to float."""
        assert transform_float("3.14") == 3.14

    def test_transform_float_from_int(self):
        """Test converting int to float."""
        assert transform_float(42) == 42.0

    def test_transform_float_from_float(self):
        """Test float remains float."""
        assert transform_float(3.14) == 3.14

    def test_transform_float_from_none(self):
        """Test converting None returns None."""
        assert transform_float(None) is None

    def test_transform_float_invalid_string(self):
        """Test converting invalid string returns None."""
        assert transform_float("not a number") is None


class TestTransformDate:
    """Tests for transform_date function."""

    def test_transform_date_from_datetime(self):
        """Test converting datetime to date (midnight)."""
        dt = datetime(2023, 12, 15, 14, 30, 45)
        result = transform_date(dt)
        assert result is not None
        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 15

    def test_transform_date_from_none(self):
        """Test converting None returns None."""
        assert transform_date(None) is None

    def test_transform_date_from_string(self):
        """Test converting string returns None."""
        assert transform_date("2023-12-15") is None


class TestTransformTimePtr:
    """Tests for transform_time_ptr function."""

    def test_transform_time_ptr_from_datetime(self):
        """Test returning datetime as-is."""
        dt = datetime(2023, 12, 15, 14, 30, 45)
        result = transform_time_ptr(dt)
        assert result == dt

    def test_transform_time_ptr_from_none(self):
        """Test None returns None."""
        assert transform_time_ptr(None) is None

    def test_transform_time_ptr_from_string(self):
        """Test string returns None."""
        assert transform_time_ptr("2023-12-15") is None


class TestFormatSourceValue:
    """Tests for format_source_value function."""

    def test_format_with_code_and_display(self):
        """Test formatting with both code and display name."""
        result = format_source_value("12345", "Test Condition")
        assert result == "12345: Test Condition"

    def test_format_with_code_only(self):
        """Test formatting with code only."""
        result = format_source_value("12345", "")
        assert result == "12345"

    def test_format_with_display_only(self):
        """Test formatting with display name only."""
        result = format_source_value("", "Test Condition")
        assert result == "Test Condition"

    def test_format_with_both_empty(self):
        """Test formatting with both empty."""
        result = format_source_value("", "")
        assert result == ""


class TestGetTransform:
    """Tests for get_transform function."""

    def test_get_transform_none(self):
        """Test getting none transform."""
        assert get_transform("none") == transform_none

    def test_get_transform_string(self):
        """Test getting string transform."""
        assert get_transform("string") == transform_string

    def test_get_transform_int(self):
        """Test getting int transform."""
        assert get_transform("int") == transform_int

    def test_get_transform_float(self):
        """Test getting float transform."""
        assert get_transform("float") == transform_float

    def test_get_transform_date(self):
        """Test getting date transform."""
        assert get_transform("date") == transform_date

    def test_get_transform_time_ptr(self):
        """Test getting time_ptr transform."""
        assert get_transform("time_ptr") == transform_time_ptr

    def test_get_transform_unknown(self):
        """Test getting unknown transform returns transform_none."""
        assert get_transform("unknown_transform") == transform_none


class TestTransformsRegistry:
    """Tests for TRANSFORMS registry."""

    def test_transforms_contains_expected_keys(self):
        """Test that TRANSFORMS contains expected keys."""
        expected_keys = [
            "none",
            "string",
            "int",
            "float",
            "date",
            "time_ptr",
            "vocab",
            "unit",
            "route",
            "value_vocab",
            "format_source",
        ]
        for key in expected_keys:
            assert key in TRANSFORMS, f"TRANSFORMS missing key: {key}"

    def test_all_transforms_are_callable(self):
        """Test that all registered transforms are callable."""
        for name, transform in TRANSFORMS.items():
            assert callable(transform), f"Transform '{name}' is not callable"
