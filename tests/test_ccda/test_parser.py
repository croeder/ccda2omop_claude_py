# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for C-CDA parser."""

from datetime import datetime
from pathlib import Path

import pytest

from ccda2omop.ccda.parser import CCDAParser


@pytest.fixture
def sample_xml_path():
    """Return path to sample.xml test file."""
    return Path(__file__).parent.parent / "fixtures" / "sample.xml"


@pytest.fixture
def parser():
    """Return a CCDAParser instance."""
    return CCDAParser()


class TestCCDAParser:
    """Tests for CCDAParser class."""

    def test_parse_sample_document(self, parser, sample_xml_path):
        """Test parsing the sample C-CDA document."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        # Test patient parsing
        assert doc.patient.id == "123-45-6789"
        assert doc.patient.name.given == "John Q"
        assert doc.patient.name.family == "Public"
        assert doc.patient.gender.code == "M"
        assert doc.patient.birth_time == datetime(1980, 5, 15, 0, 0, 0)
        assert doc.patient.race.code == "2106-3"
        assert doc.patient.ethnicity.code == "2186-5"

    def test_parse_encounters(self, parser, sample_xml_path):
        """Test parsing encounters section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.encounters) == 1
        enc = doc.encounters[0]
        assert enc.id == "ENC-001"
        assert enc.code.code == "AMB"
        assert enc.performer == "Jane Doctor"

    def test_parse_problems(self, parser, sample_xml_path):
        """Test parsing problems section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.problems) == 2
        prob = doc.problems[0]
        assert prob.code.code == "44054006"
        assert prob.code.display_name == "Type 2 Diabetes Mellitus"

    def test_parse_medications(self, parser, sample_xml_path):
        """Test parsing medications section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.medications) == 2
        med = doc.medications[0]
        assert med.code.code == "860975"
        assert med.dose_quantity.value == 500
        assert med.dose_quantity.unit == "mg"
        assert med.route_code.code == "PO"

    def test_parse_vital_signs(self, parser, sample_xml_path):
        """Test parsing vital signs section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.vital_signs) == 4

        # Find systolic BP
        systolic = next((v for v in doc.vital_signs if v.code.code == "8480-6"), None)
        assert systolic is not None
        assert systolic.value == 128
        assert systolic.unit == "mm[Hg]"

    def test_parse_lab_results(self, parser, sample_xml_path):
        """Test parsing lab results section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.lab_results) == 2

        # Find HbA1c
        hba1c = next((l for l in doc.lab_results if l.code.code == "4548-4"), None)
        assert hba1c is not None
        assert hba1c.value == 7.2
        assert hba1c.unit == "%"

    def test_parse_allergies(self, parser, sample_xml_path):
        """Test parsing allergies section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.allergies) == 1
        allergy = doc.allergies[0]
        assert allergy.substance.code == "7980"
        assert allergy.substance.display_name == "Penicillin"

    def test_parse_immunizations(self, parser, sample_xml_path):
        """Test parsing immunizations section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.immunizations) == 1
        imm = doc.immunizations[0]
        assert imm.code.code == "141"
        assert imm.lot_number == "LOT-2023-FLU-456"
        assert imm.dose_quantity.value == 0.5

    def test_parse_procedures(self, parser, sample_xml_path):
        """Test parsing procedures section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.procedures) == 1
        proc = doc.procedures[0]
        assert proc.code.code == "73761001"
        assert proc.code.display_name == "Colonoscopy"

    def test_parse_devices(self, parser, sample_xml_path):
        """Test parsing devices section."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.devices) == 1
        dev = doc.devices[0]
        assert dev.code.code == "706689003"
        assert dev.udi == "(01)00884838049032"

    def test_parse_observations(self, parser, sample_xml_path):
        """Test parsing social history observations."""
        if not sample_xml_path.exists():
            pytest.skip("Sample XML file not found")

        doc = parser.parse_file(str(sample_xml_path))

        assert len(doc.observations) == 1
        obs = doc.observations[0]
        assert obs.code.code == "72166-2"
        assert obs.value.display_name == "Former smoker"

    def test_parse_file_not_found(self, parser):
        """Test parsing non-existent file raises exception."""
        with pytest.raises(Exception):
            parser.parse_file("nonexistent.xml")

    def test_parse_invalid_xml(self, parser):
        """Test parsing invalid XML raises exception."""
        invalid_xml = "<?xml version='1.0'?><ClinicalDocument><invalid>"
        with pytest.raises(Exception):
            parser.parse_string(invalid_xml)

    def test_parse_empty_document(self, parser):
        """Test parsing empty C-CDA document."""
        empty_doc = '<?xml version="1.0"?><ClinicalDocument xmlns="urn:hl7-org:v3"></ClinicalDocument>'
        doc = parser.parse_string(empty_doc)

        assert len(doc.encounters) == 0
        assert len(doc.problems) == 0
        assert len(doc.medications) == 0
