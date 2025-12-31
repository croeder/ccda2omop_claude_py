# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for OMOP CSV writer."""

import csv
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from ccda2omop.omop.models import (
    ConditionOccurrence,
    DeviceExposure,
    DrugExposure,
    Measurement,
    Observation,
    OMOPData,
    Person,
    ProcedureOccurrence,
    VisitOccurrence,
)
from ccda2omop.omop.writer import CSVWriter


class TestCSVWriter:
    """Tests for CSVWriter class."""

    def test_init_creates_output_dir(self):
        """Test that CSVWriter creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_subdir"
            assert not output_dir.exists()

            writer = CSVWriter(output_dir)

            assert output_dir.exists()
            assert output_dir.is_dir()

    def test_write_all_creates_files(self):
        """Test that write_all creates all expected CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()

            writer.write_all(data)

            expected_files = [
                "person.csv",
                "visit_occurrence.csv",
                "condition_occurrence.csv",
                "drug_exposure.csv",
                "procedure_occurrence.csv",
                "measurement.csv",
                "observation.csv",
                "device_exposure.csv",
            ]

            for filename in expected_files:
                filepath = Path(tmpdir) / filename
                assert filepath.exists(), f"Expected {filename} to exist"

    def test_write_person_data(self):
        """Test writing person data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            data.persons.append(
                Person(
                    person_id=12345,
                    gender_concept_id=8507,
                    year_of_birth=1990,
                    month_of_birth=6,
                    day_of_birth=15,
                    race_concept_id=8527,
                    ethnicity_concept_id=38003564,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "person.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2  # header + 1 data row
            assert rows[0][0] == "person_id"
            assert rows[1][0] == "12345"

    def test_write_visit_occurrence_data(self):
        """Test writing visit occurrence data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            visit_start = datetime(2023, 1, 15, 10, 0, 0)
            visit_end = datetime(2023, 1, 15, 11, 0, 0)
            data.visit_occurrences.append(
                VisitOccurrence(
                    visit_occurrence_id=1001,
                    person_id=12345,
                    visit_concept_id=9201,
                    visit_start_date=visit_start,
                    visit_start_datetime=visit_start,
                    visit_end_date=visit_end,
                    visit_end_datetime=visit_end,
                    visit_type_concept_id=32817,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "visit_occurrence.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "visit_occurrence_id" in rows[0]

    def test_write_condition_occurrence_data(self):
        """Test writing condition occurrence data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            condition_start = datetime(2023, 1, 15)
            data.condition_occurrences.append(
                ConditionOccurrence(
                    condition_occurrence_id=2001,
                    person_id=12345,
                    condition_concept_id=44054006,
                    condition_start_date=condition_start,
                    condition_start_datetime=condition_start,
                    condition_type_concept_id=32817,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "condition_occurrence.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "condition_occurrence_id" in rows[0]

    def test_write_drug_exposure_data(self):
        """Test writing drug exposure data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            drug_start = datetime(2023, 1, 15)
            data.drug_exposures.append(
                DrugExposure(
                    drug_exposure_id=3001,
                    person_id=12345,
                    drug_concept_id=1049221,
                    drug_exposure_start_date=drug_start,
                    drug_exposure_start_datetime=drug_start,
                    drug_type_concept_id=32817,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "drug_exposure.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "drug_exposure_id" in rows[0]

    def test_write_procedure_occurrence_data(self):
        """Test writing procedure occurrence data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            proc_date = datetime(2023, 1, 15)
            data.procedure_occurrences.append(
                ProcedureOccurrence(
                    procedure_occurrence_id=4001,
                    person_id=12345,
                    procedure_concept_id=2213,
                    procedure_date=proc_date,
                    procedure_datetime=proc_date,
                    procedure_type_concept_id=32817,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "procedure_occurrence.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "procedure_occurrence_id" in rows[0]

    def test_write_measurement_data(self):
        """Test writing measurement data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            meas_date = datetime(2023, 1, 15)
            data.measurements.append(
                Measurement(
                    measurement_id=5001,
                    person_id=12345,
                    measurement_concept_id=3004249,
                    measurement_date=meas_date,
                    measurement_datetime=meas_date,
                    measurement_type_concept_id=32817,
                    value_as_number=120.0,
                    unit_concept_id=8876,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "measurement.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "measurement_id" in rows[0]

    def test_write_observation_data(self):
        """Test writing observation data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            obs_date = datetime(2023, 1, 15)
            data.observations.append(
                Observation(
                    observation_id=6001,
                    person_id=12345,
                    observation_concept_id=4219336,
                    observation_date=obs_date,
                    observation_datetime=obs_date,
                    observation_type_concept_id=32817,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "observation.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "observation_id" in rows[0]

    def test_write_device_exposure_data(self):
        """Test writing device exposure data to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()
            device_start = datetime(2023, 1, 15)
            data.device_exposures.append(
                DeviceExposure(
                    device_exposure_id=7001,
                    person_id=12345,
                    device_concept_id=714628002,
                    device_exposure_start_date=device_start,
                    device_exposure_start_datetime=device_start,
                    device_type_concept_id=32817,
                )
            )

            writer.write_all(data)

            filepath = Path(tmpdir) / "device_exposure.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 2
            assert "device_exposure_id" in rows[0]

    def test_write_empty_data(self):
        """Test writing empty OMOP data creates files with headers only."""
        with tempfile.TemporaryDirectory() as tmpdir:
            writer = CSVWriter(tmpdir)
            data = OMOPData()

            writer.write_all(data)

            filepath = Path(tmpdir) / "person.csv"
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)

            assert len(rows) == 1  # header only
            assert "person_id" in rows[0]
