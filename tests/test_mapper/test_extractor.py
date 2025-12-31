# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for XPath extraction helpers."""

from datetime import datetime

import pytest
from lxml import etree

from ccda2omop.ccda.models import CodedValue, EffectiveTime, Quantity
from ccda2omop.mapper.extractor import (
    extract_code,
    extract_effective_time,
    extract_float,
    extract_int,
    extract_quantity,
    extract_string,
    extract_time,
    should_include_entry,
    xpath_with_fallback,
)


class TestExtractString:
    """Tests for extract_string function."""

    def test_extract_string_from_text(self):
        """Test extracting text content from an element."""
        xml = etree.fromstring("<root><name>Test Value</name></root>")
        result = extract_string(xml, "name/text()")
        assert result == "Test Value"

    def test_extract_string_from_attribute(self):
        """Test extracting an attribute value."""
        xml = etree.fromstring('<root><code value="12345"/></root>')
        result = extract_string(xml, "code/@value")
        assert result == "12345"

    def test_extract_string_empty_result(self):
        """Test extracting when xpath finds nothing."""
        xml = etree.fromstring("<root><name>Test</name></root>")
        result = extract_string(xml, "missing/text()")
        assert result == ""

    def test_extract_string_none_node(self):
        """Test extracting from None node."""
        result = extract_string(None, "name/text()")
        assert result == ""

    def test_extract_string_element_with_text(self):
        """Test extracting text from element result."""
        xml = etree.fromstring("<root><name>Test Value</name></root>")
        result = extract_string(xml, "name")
        assert result == "Test Value"


class TestExtractFloat:
    """Tests for extract_float function."""

    def test_extract_float_from_value_attr(self):
        """Test extracting float from value attribute."""
        xml = etree.fromstring('<root><value value="123.45"/></root>')
        result = extract_float(xml, "value")
        assert result == 123.45

    def test_extract_float_from_text(self):
        """Test extracting float from text content."""
        xml = etree.fromstring("<root><value>98.6</value></root>")
        result = extract_float(xml, "value")
        assert result == 98.6

    def test_extract_float_invalid_value(self):
        """Test extracting invalid float returns None."""
        xml = etree.fromstring("<root><value>not a number</value></root>")
        result = extract_float(xml, "value")
        assert result is None

    def test_extract_float_empty_result(self):
        """Test extracting when xpath finds nothing."""
        xml = etree.fromstring("<root></root>")
        result = extract_float(xml, "value/@value")
        assert result is None

    def test_extract_float_none_node(self):
        """Test extracting from None node."""
        result = extract_float(None, "value/@value")
        assert result is None


class TestExtractInt:
    """Tests for extract_int function."""

    def test_extract_int_from_value_attr(self):
        """Test extracting int from value attribute."""
        xml = etree.fromstring('<root><value value="42"/></root>')
        result = extract_int(xml, "value")
        assert result == 42

    def test_extract_int_from_text(self):
        """Test extracting int from text content."""
        xml = etree.fromstring("<root><value>100</value></root>")
        result = extract_int(xml, "value")
        assert result == 100

    def test_extract_int_invalid_value(self):
        """Test extracting invalid int returns None."""
        xml = etree.fromstring("<root><value>3.14</value></root>")
        result = extract_int(xml, "value")
        assert result is None

    def test_extract_int_none_node(self):
        """Test extracting from None node."""
        result = extract_int(None, "value/@value")
        assert result is None


class TestExtractTime:
    """Tests for extract_time function."""

    def test_extract_time_full_datetime(self):
        """Test extracting full HL7 datetime."""
        xml = etree.fromstring('<root><time value="20231215120000"/></root>')
        result = extract_time(xml, "time")
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 15
        assert result.hour == 12

    def test_extract_time_date_only(self):
        """Test extracting date-only HL7 time."""
        xml = etree.fromstring('<root><time value="20231215"/></root>')
        result = extract_time(xml, "time")
        assert result is not None
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 15

    def test_extract_time_empty_result(self):
        """Test extracting when xpath finds nothing."""
        xml = etree.fromstring("<root></root>")
        result = extract_time(xml, "time")
        assert result is None

    def test_extract_time_none_node(self):
        """Test extracting from None node."""
        result = extract_time(None, "time")
        assert result is None


class TestExtractCode:
    """Tests for extract_code function."""

    def test_extract_code_full(self):
        """Test extracting a coded value with all attributes."""
        xml = etree.fromstring(
            '<root><code code="44054006" codeSystem="2.16.840.1.113883.6.96" '
            'codeSystemName="SNOMED CT" displayName="Type 2 diabetes mellitus"/></root>'
        )
        result = extract_code(xml, "code")
        assert isinstance(result, CodedValue)
        assert result.code == "44054006"
        assert result.code_system == "2.16.840.1.113883.6.96"
        assert result.code_system_name == "SNOMED CT"
        assert result.display_name == "Type 2 diabetes mellitus"

    def test_extract_code_with_original_text(self):
        """Test extracting a coded value with original text."""
        xml = etree.fromstring(
            '<root><code code="12345"><originalText>Custom text</originalText></code></root>'
        )
        result = extract_code(xml, "code")
        assert result.code == "12345"
        assert result.original_text == "Custom text"

    def test_extract_code_empty_result(self):
        """Test extracting when xpath finds nothing."""
        xml = etree.fromstring("<root></root>")
        result = extract_code(xml, "code")
        assert isinstance(result, CodedValue)
        assert result.code == ""

    def test_extract_code_none_node(self):
        """Test extracting from None node."""
        result = extract_code(None, "code")
        assert isinstance(result, CodedValue)
        assert result.code == ""


class TestExtractEffectiveTime:
    """Tests for extract_effective_time function."""

    def test_extract_effective_time_value(self):
        """Test extracting effective time with value attribute."""
        xml = etree.fromstring('<root><effectiveTime value="20231215"/></root>')
        result = extract_effective_time(xml, "effectiveTime")
        assert isinstance(result, EffectiveTime)
        assert result.value is not None
        assert result.value.year == 2023

    def test_extract_effective_time_range(self):
        """Test extracting effective time with low and high."""
        xml = etree.fromstring(
            '<root><effectiveTime><low value="20230101"/><high value="20231231"/></effectiveTime></root>'
        )
        result = extract_effective_time(xml, "effectiveTime")
        assert isinstance(result, EffectiveTime)
        assert result.low is not None
        assert result.low.year == 2023
        assert result.low.month == 1
        assert result.high is not None
        assert result.high.year == 2023
        assert result.high.month == 12

    def test_extract_effective_time_empty(self):
        """Test extracting when xpath finds nothing."""
        xml = etree.fromstring("<root></root>")
        result = extract_effective_time(xml, "effectiveTime")
        assert isinstance(result, EffectiveTime)
        assert result.value is None

    def test_extract_effective_time_none_node(self):
        """Test extracting from None node."""
        result = extract_effective_time(None, "effectiveTime")
        assert isinstance(result, EffectiveTime)


class TestExtractQuantity:
    """Tests for extract_quantity function."""

    def test_extract_quantity_with_unit(self):
        """Test extracting quantity with value and unit."""
        xml = etree.fromstring('<root><doseQuantity value="500" unit="mg"/></root>')
        result = extract_quantity(xml, "doseQuantity")
        assert isinstance(result, Quantity)
        assert result.value == 500.0
        assert result.unit == "mg"

    def test_extract_quantity_no_unit(self):
        """Test extracting quantity without unit."""
        xml = etree.fromstring('<root><doseQuantity value="2"/></root>')
        result = extract_quantity(xml, "doseQuantity")
        assert result.value == 2.0
        assert result.unit == ""

    def test_extract_quantity_invalid_value(self):
        """Test extracting quantity with invalid value."""
        xml = etree.fromstring('<root><doseQuantity value="invalid"/></root>')
        result = extract_quantity(xml, "doseQuantity")
        assert result.value == 0.0

    def test_extract_quantity_none_node(self):
        """Test extracting from None node."""
        result = extract_quantity(None, "doseQuantity")
        assert isinstance(result, Quantity)


class TestShouldIncludeEntry:
    """Tests for should_include_entry function."""

    def test_include_entry_evn_mood(self):
        """Test including entry with moodCode EVN."""
        xml = etree.fromstring('<act moodCode="EVN"><statusCode code="completed"/></act>')
        assert should_include_entry(xml) is True

    def test_include_entry_no_mood(self):
        """Test including entry without moodCode (defaults to EVN)."""
        xml = etree.fromstring('<act><statusCode code="completed"/></act>')
        assert should_include_entry(xml) is True

    def test_exclude_entry_int_mood(self):
        """Test excluding entry with moodCode INT (intent)."""
        xml = etree.fromstring('<act moodCode="INT"><statusCode code="completed"/></act>')
        assert should_include_entry(xml) is False

    def test_include_entry_active_status(self):
        """Test including entry with active status."""
        xml = etree.fromstring('<act moodCode="EVN"><statusCode code="active"/></act>')
        assert should_include_entry(xml) is True

    def test_exclude_entry_cancelled_status(self):
        """Test excluding entry with cancelled status."""
        xml = etree.fromstring('<act moodCode="EVN"><statusCode code="cancelled"/></act>')
        assert should_include_entry(xml) is False

    def test_include_entry_no_status(self):
        """Test including entry without statusCode."""
        xml = etree.fromstring('<act moodCode="EVN"></act>')
        assert should_include_entry(xml) is True

    def test_exclude_none_node(self):
        """Test excluding None node."""
        assert should_include_entry(None) is False


class TestXpathWithFallback:
    """Tests for xpath_with_fallback function."""

    def test_primary_xpath_succeeds(self):
        """Test using primary xpath when it finds results."""
        xml = etree.fromstring('<root><primary value="1"/><fallback value="2"/></root>')
        result = xpath_with_fallback(xml, "primary/@value", "fallback/@value")
        assert result == ["1"]

    def test_fallback_xpath_used(self):
        """Test using fallback xpath when primary fails."""
        xml = etree.fromstring('<root><fallback value="2"/></root>')
        result = xpath_with_fallback(xml, "primary/@value", "fallback/@value")
        assert result == ["2"]

    def test_no_primary_uses_fallback(self):
        """Test using fallback when no primary xpath provided."""
        xml = etree.fromstring('<root><fallback value="2"/></root>')
        result = xpath_with_fallback(xml, "", "fallback/@value")
        assert result == ["2"]

    def test_both_empty_returns_empty(self):
        """Test returning empty list when both xpaths are empty."""
        xml = etree.fromstring("<root></root>")
        result = xpath_with_fallback(xml, "", "")
        assert result == []

    def test_neither_matches_returns_empty(self):
        """Test returning empty list when neither xpath matches."""
        xml = etree.fromstring("<root></root>")
        result = xpath_with_fallback(xml, "missing1", "missing2")
        assert result == []
