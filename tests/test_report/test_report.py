# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for conversion report."""

import io
import json
from datetime import datetime

import pytest

from ccda2omop.omop.models import (
    ConditionOccurrence,
    DrugExposure,
    Measurement,
    Observation,
    OMOPData,
    Person,
    VisitOccurrence,
)
from ccda2omop.report.report import ConversionReport


class TestConversionReport:
    """Tests for ConversionReport class."""

    def test_new_conversion_report(self):
        """Test creating a new ConversionReport."""
        r = ConversionReport()
        assert r is not None
        assert r.entries_by_section is not None
        assert r.records_by_table is not None
        assert r.field_population is not None
        assert r.concept_mappings is not None
        assert r.skipped_entries is not None

    def test_add_document(self):
        """Test adding documents to report."""
        r = ConversionReport()

        r.add_document(has_error=False)
        assert r.documents_processed == 1
        assert r.documents_with_errors == 0

        r.add_document(has_error=True)
        assert r.documents_processed == 2
        assert r.documents_with_errors == 1

        r.add_document(has_error=False)
        r.add_document(has_error=True)
        assert r.documents_processed == 4
        assert r.documents_with_errors == 2

    def test_add_section_entry(self):
        """Test adding section entries."""
        r = ConversionReport()

        r.add_section_entry("problems")
        r.add_section_entry("problems")
        r.add_section_entry("medications")

        assert r.entries_by_section["problems"].entries_found == 2
        assert r.entries_by_section["medications"].entries_found == 1

    def test_add_section_record(self):
        """Test adding section records."""
        r = ConversionReport()

        r.add_section_record("problems", "condition_occurrence")
        r.add_section_record("problems", "condition_occurrence")
        r.add_section_record("problems", "observation")
        r.add_section_record("medications", "drug_exposure")

        assert r.entries_by_section["problems"].records_created == 3
        assert r.entries_by_section["problems"].target_tables["condition_occurrence"] == 2
        assert r.entries_by_section["problems"].target_tables["observation"] == 1
        assert r.entries_by_section["medications"].target_tables["drug_exposure"] == 1

    def test_add_skipped(self):
        """Test adding skipped entries."""
        r = ConversionReport()

        r.add_skipped("problems", "moodCode != EVN")
        r.add_skipped("problems", "moodCode != EVN")
        r.add_skipped("medications", "missing code")

        assert r.entries_by_section["problems"].skipped == 2
        assert r.skipped_entries["moodCode != EVN"] == 2
        assert r.skipped_entries["missing code"] == 1

    def test_add_concept_mapping(self):
        """Test adding concept mappings."""
        r = ConversionReport()

        r.add_concept_mapping("SNOMED", mapped_to_standard=True)
        r.add_concept_mapping("SNOMED", mapped_to_standard=True)
        r.add_concept_mapping("SNOMED", mapped_to_standard=False)
        r.add_concept_mapping("RxNorm", mapped_to_standard=True)
        r.add_concept_mapping("RxNorm", mapped_to_standard=False)

        snomed = r.concept_mappings["SNOMED"]
        assert snomed.codes_seen == 3
        assert snomed.mapped_standard == 2
        assert snomed.source_only == 1

        rxnorm = r.concept_mappings["RxNorm"]
        assert rxnorm.codes_seen == 2

    def test_add_domain_route(self):
        """Test adding domain routes."""
        r = ConversionReport()

        r.add_domain_route("problems", "condition_occurrence", "observation", "Domain=Observation")
        r.add_domain_route("problems", "condition_occurrence", "observation", "Domain=Observation")
        r.add_domain_route("labs", "measurement", "observation", "Domain=Observation")

        assert len(r.domain_routing) == 2

        problems_route = next(
            (route for route in r.domain_routing if route.source_section == "problems"), None
        )
        assert problems_route is not None
        assert problems_route.count == 2

    def test_calculate_from_omop_data(self):
        """Test calculating report from OMOP data."""
        r = ConversionReport()

        now = datetime.now()
        data = OMOPData(
            persons=[Person(person_id=1, gender_concept_id=8507, year_of_birth=1980)],
            visit_occurrences=[
                VisitOccurrence(
                    visit_occurrence_id=1,
                    person_id=1,
                    visit_concept_id=9201,
                    visit_start_date=now,
                    visit_end_date=now,
                    visit_type_concept_id=44818518,
                )
            ],
            condition_occurrences=[
                ConditionOccurrence(
                    condition_occurrence_id=1,
                    person_id=1,
                    condition_concept_id=12345,
                    condition_start_date=now,
                    condition_type_concept_id=32817,
                    condition_source_value="Test",
                    mapping_rule="RuleMapper:problems_to_conditions",
                ),
                ConditionOccurrence(
                    condition_occurrence_id=2,
                    person_id=1,
                    condition_concept_id=0,
                    condition_start_date=now,
                    condition_type_concept_id=32817,
                    condition_source_value="Test2",
                    mapping_rule="RuleMapper:problems_to_conditions",
                ),
            ],
            drug_exposures=[
                DrugExposure(
                    drug_exposure_id=1,
                    person_id=1,
                    drug_concept_id=100,
                    drug_exposure_start_date=now,
                    drug_exposure_end_date=now,
                    drug_type_concept_id=32817,
                    drug_source_value="Drug1",
                    mapping_rule="RuleMapper:medications_to_drugs",
                )
            ],
            measurements=[
                Measurement(
                    measurement_id=1,
                    person_id=1,
                    measurement_concept_id=200,
                    measurement_date=now,
                    measurement_type_concept_id=32817,
                    value_as_number=120.0,
                    measurement_source_value="BP",
                    mapping_rule="RuleMapper:vitals_to_measurements",
                ),
                Measurement(
                    measurement_id=2,
                    person_id=1,
                    measurement_concept_id=201,
                    measurement_date=now,
                    measurement_type_concept_id=32817,
                    value_as_number=80.0,
                    unit_concept_id=100,
                    measurement_source_value="BP2",
                    mapping_rule="RuleMapper:vitals_to_measurements",
                ),
            ],
            observations=[
                Observation(
                    observation_id=1,
                    person_id=1,
                    observation_concept_id=300,
                    observation_date=now,
                    observation_type_concept_id=32817,
                    value_as_string="Former smoker",
                    observation_source_value="Smoking",
                    mapping_rule="RuleMapper:social_to_observations",
                )
            ],
        )

        r.calculate_from_omop_data(data)

        # Check record counts
        assert r.records_by_table["person"] == 1
        assert r.records_by_table["condition_occurrence"] == 2
        assert r.records_by_table["drug_exposure"] == 1
        assert r.records_by_table["measurement"] == 2
        assert r.records_by_table["observation"] == 1

    def test_write_text(self):
        """Test writing text report."""
        r = ConversionReport()
        r.documents_processed = 10
        r.documents_with_errors = 1
        r.records_by_table["person"] = 10
        r.records_by_table["condition_occurrence"] = 25
        r.records_by_table["measurement"] = 100

        r.add_section_record("problems", "condition_occurrence")
        r.add_concept_mapping("SNOMED", mapped_to_standard=True)
        r.add_concept_mapping("SNOMED", mapped_to_standard=False)

        output = io.StringIO()
        r.write_text(output)
        result = output.getvalue()

        # Check for expected content
        expected_strings = [
            "# CCDA-to-OMOP Conversion Report",
            "## Document Summary",
            "Documents Processed | 10",
            "Documents with Errors | 1",
            "Success Rate | 90.0%",
            "## Records Created by OMOP Table",
            "condition_occurrence | 25",
            "measurement | 100",
        ]

        for expected in expected_strings:
            assert expected in result, f"WriteText output missing {expected!r}"

    def test_write_json(self):
        """Test writing JSON report."""
        r = ConversionReport()
        r.documents_processed = 5
        r.documents_with_errors = 0
        r.records_by_table["person"] = 5
        r.records_by_table["condition_occurrence"] = 15

        r.add_section_record("problems", "condition_occurrence")
        r.add_concept_mapping("LOINC", mapped_to_standard=True)

        output = io.StringIO()
        r.write_json(output)
        result = output.getvalue()

        # Verify it's valid JSON
        parsed = json.loads(result)

        assert parsed["documents_processed"] == 5
        assert parsed["records_by_table"]["person"] == 5
        assert parsed["records_by_table"]["condition_occurrence"] == 15

    def test_empty_data_calculation(self):
        """Test calculation with empty data."""
        r = ConversionReport()
        data = OMOPData()

        # Should not raise exception
        r.calculate_from_omop_data(data)

        assert r.records_by_table["person"] == 0
        assert len(r.field_population) == 0
