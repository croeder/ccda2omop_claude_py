# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for HL7 time parsing."""

from datetime import datetime

import pytest

from ccda2omop.ccda.hl7_time import parse_hl7_time


class TestParseHL7Time:
    """Tests for parse_hl7_time function."""

    @pytest.mark.parametrize(
        "input_str,expected",
        [
            ("20231215120000", datetime(2023, 12, 15, 12, 0, 0)),
            ("202312151230", datetime(2023, 12, 15, 12, 30, 0)),
            ("20231215", datetime(2023, 12, 15, 0, 0, 0)),
            ("202312", datetime(2023, 12, 1, 0, 0, 0)),
            ("2023", datetime(2023, 1, 1, 0, 0, 0)),
            ("20231215120000Z", datetime(2023, 12, 15, 12, 0, 0)),
            ("20231215120000-0500", datetime(2023, 12, 15, 12, 0, 0)),
            ("", None),
        ],
    )
    def test_parse_hl7_time(self, input_str: str, expected):
        """Test various HL7 time formats."""
        result = parse_hl7_time(input_str)
        assert result == expected
