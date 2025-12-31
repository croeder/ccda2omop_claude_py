# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for OMOP ID generation."""

import pytest

from ccda2omop.omop.ids import (
    generate_condition_id,
    generate_device_exposure_id,
    generate_drug_exposure_id,
    generate_id,
    generate_measurement_id,
    generate_observation_id,
    generate_person_id,
    generate_procedure_id,
    generate_visit_id,
)


class TestGenerateId:
    """Tests for generate_id function."""

    def test_generate_id_single_value(self):
        """Test ID generation with a single value."""
        id1 = generate_id("test")
        assert isinstance(id1, int)
        assert id1 > 0

    def test_generate_id_multiple_values(self):
        """Test ID generation with multiple values."""
        id1 = generate_id("test", "value1", "value2")
        assert isinstance(id1, int)
        assert id1 > 0

    def test_generate_id_deterministic(self):
        """Test that same inputs produce same ID."""
        id1 = generate_id("person", "12345", "system1")
        id2 = generate_id("person", "12345", "system1")
        assert id1 == id2

    def test_generate_id_different_inputs(self):
        """Test that different inputs produce different IDs."""
        id1 = generate_id("person", "12345")
        id2 = generate_id("person", "67890")
        assert id1 != id2

    def test_generate_id_order_matters(self):
        """Test that order of values affects the ID."""
        id1 = generate_id("a", "b", "c")
        id2 = generate_id("c", "b", "a")
        assert id1 != id2

    def test_generate_id_empty_string(self):
        """Test ID generation with empty string."""
        id1 = generate_id("")
        assert isinstance(id1, int)
        assert id1 > 0


class TestGeneratePersonId:
    """Tests for generate_person_id function."""

    def test_generate_person_id(self):
        """Test person ID generation."""
        pid = generate_person_id("patient123", "hospital_system")
        assert isinstance(pid, int)
        assert pid > 0

    def test_generate_person_id_deterministic(self):
        """Test that same patient produces same ID."""
        pid1 = generate_person_id("patient123", "system")
        pid2 = generate_person_id("patient123", "system")
        assert pid1 == pid2

    def test_generate_person_id_different_patients(self):
        """Test that different patients produce different IDs."""
        pid1 = generate_person_id("patient123", "system")
        pid2 = generate_person_id("patient456", "system")
        assert pid1 != pid2


class TestGenerateVisitId:
    """Tests for generate_visit_id function."""

    def test_generate_visit_id(self):
        """Test visit ID generation."""
        vid = generate_visit_id(12345, "encounter_001")
        assert isinstance(vid, int)
        assert vid > 0

    def test_generate_visit_id_deterministic(self):
        """Test that same encounter produces same ID."""
        vid1 = generate_visit_id(12345, "encounter_001")
        vid2 = generate_visit_id(12345, "encounter_001")
        assert vid1 == vid2


class TestGenerateConditionId:
    """Tests for generate_condition_id function."""

    def test_generate_condition_id(self):
        """Test condition ID generation."""
        cid = generate_condition_id(12345, "SNOMED:44054006", "2023-01-15")
        assert isinstance(cid, int)
        assert cid > 0

    def test_generate_condition_id_deterministic(self):
        """Test that same condition produces same ID."""
        cid1 = generate_condition_id(12345, "SNOMED:44054006", "2023-01-15")
        cid2 = generate_condition_id(12345, "SNOMED:44054006", "2023-01-15")
        assert cid1 == cid2


class TestGenerateDrugExposureId:
    """Tests for generate_drug_exposure_id function."""

    def test_generate_drug_exposure_id(self):
        """Test drug exposure ID generation."""
        did = generate_drug_exposure_id(12345, "RxNorm:1049221", "2023-01-15")
        assert isinstance(did, int)
        assert did > 0


class TestGenerateProcedureId:
    """Tests for generate_procedure_id function."""

    def test_generate_procedure_id(self):
        """Test procedure ID generation."""
        pid = generate_procedure_id(12345, "CPT:99213", "2023-01-15")
        assert isinstance(pid, int)
        assert pid > 0


class TestGenerateMeasurementId:
    """Tests for generate_measurement_id function."""

    def test_generate_measurement_id(self):
        """Test measurement ID generation."""
        mid = generate_measurement_id(12345, "LOINC:8480-6", "2023-01-15", "120")
        assert isinstance(mid, int)
        assert mid > 0


class TestGenerateObservationId:
    """Tests for generate_observation_id function."""

    def test_generate_observation_id(self):
        """Test observation ID generation."""
        oid = generate_observation_id(12345, "LOINC:72166-2", "2023-01-15")
        assert isinstance(oid, int)
        assert oid > 0


class TestGenerateDeviceExposureId:
    """Tests for generate_device_exposure_id function."""

    def test_generate_device_exposure_id(self):
        """Test device exposure ID generation."""
        did = generate_device_exposure_id(12345, "SNOMED:714628002", "2023-01-15")
        assert isinstance(did, int)
        assert did > 0
