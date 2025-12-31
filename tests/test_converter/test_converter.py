# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for C-CDA to OMOP converter."""

import tempfile
from pathlib import Path

import pytest

from ccda2omop.converter.converter import Config, ConversionSummary, Converter
from ccda2omop.omop.models import OMOPData, Person


class TestConfig:
    """Tests for Config dataclass."""

    def test_config_defaults(self):
        """Test Config has expected defaults."""
        cfg = Config()
        assert cfg.input_file == ""
        assert cfg.output_dir == ""
        assert cfg.verbose is False
        assert cfg.concept_file == ""
        assert cfg.relationship_file == ""
        assert cfg.vocab_dir == ""
        assert cfg.rules_file == ""
        assert cfg.generate_report is False

    def test_config_custom_values(self):
        """Test Config with custom values."""
        cfg = Config(
            input_file="input.xml",
            output_dir="/tmp/output",
            verbose=True,
            concept_file="CONCEPT.csv",
            generate_report=True,
        )
        assert cfg.input_file == "input.xml"
        assert cfg.output_dir == "/tmp/output"
        assert cfg.verbose is True
        assert cfg.concept_file == "CONCEPT.csv"
        assert cfg.generate_report is True


class TestConversionSummary:
    """Tests for ConversionSummary dataclass."""

    def test_summary_defaults(self):
        """Test ConversionSummary has zero defaults."""
        summary = ConversionSummary()
        assert summary.persons == 0
        assert summary.visit_occurrences == 0
        assert summary.condition_occurrences == 0
        assert summary.drug_exposures == 0
        assert summary.procedure_occurrences == 0
        assert summary.measurements == 0
        assert summary.observations == 0
        assert summary.device_exposures == 0
        assert summary.report is None

    def test_summary_custom_values(self):
        """Test ConversionSummary with custom values."""
        summary = ConversionSummary(
            persons=1,
            visit_occurrences=5,
            condition_occurrences=10,
            drug_exposures=3,
            procedure_occurrences=2,
            measurements=20,
            observations=1,
            device_exposures=0,
        )
        assert summary.persons == 1
        assert summary.visit_occurrences == 5
        assert summary.condition_occurrences == 10


class TestConverter:
    """Tests for Converter class."""

    def test_converter_init(self):
        """Test creating a Converter instance."""
        converter = Converter()
        assert converter is not None
        assert converter._vocab_loader is None

    def test_load_vocabulary_no_file(self):
        """Test loading vocabulary with no file specified."""
        converter = Converter()
        converter.load_vocabulary("")
        assert converter._vocab_loader is None

    def test_load_vocabulary_with_concept_file(self, fixtures_dir):
        """Test loading vocabulary from CONCEPT.csv file."""
        concept_file = fixtures_dir / "CONCEPT.csv"
        if not concept_file.exists():
            pytest.skip("CONCEPT.csv fixture not available")

        converter = Converter()
        converter.load_vocabulary(str(concept_file))
        assert converter._vocab_loader is not None

    def test_load_vocabulary_caches_result(self, fixtures_dir):
        """Test that vocabulary is only loaded once."""
        concept_file = fixtures_dir / "CONCEPT.csv"
        if not concept_file.exists():
            pytest.skip("CONCEPT.csv fixture not available")

        converter = Converter()
        converter.load_vocabulary(str(concept_file))
        first_loader = converter._vocab_loader

        # Load again - should return cached
        converter.load_vocabulary(str(concept_file))
        assert converter._vocab_loader is first_loader

    def test_load_supplementary_vocabs_invalid_dir(self):
        """Test loading supplementary vocabs from invalid directory."""
        converter = Converter()
        converter._vocab_loader = None  # Needs vocab_loader first

        with pytest.raises(ValueError, match="Vocab directory not found"):
            converter._load_supplementary_vocabs("/nonexistent/path", False)

    def test_set_source_file(self):
        """Test setting source file on OMOP data."""
        converter = Converter()
        data = OMOPData()
        data.persons.append(Person(person_id=1))

        converter._set_source_file(data, "test.xml")

        assert data.persons[0].source_file == "test.xml"


class TestConverterRun:
    """Tests for Converter.run method."""

    def test_run_creates_output_dir(self, sample_ccda_file):
        """Test that run creates the output directory."""
        if not sample_ccda_file.exists():
            pytest.skip("Sample CCDA file not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "new_output"
            cfg = Config(
                input_file=str(sample_ccda_file),
                output_dir=str(output_dir),
            )

            converter = Converter()
            converter.run(cfg)

            assert output_dir.exists()
            assert (output_dir / "person.csv").exists()

    def test_run_generates_csv_files(self, sample_ccda_file):
        """Test that run generates all expected CSV files."""
        if not sample_ccda_file.exists():
            pytest.skip("Sample CCDA file not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config(
                input_file=str(sample_ccda_file),
                output_dir=tmpdir,
            )

            converter = Converter()
            converter.run(cfg)

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


class TestConverterRunBatch:
    """Tests for Converter.run_batch method."""

    def test_run_batch_empty_list(self):
        """Test run_batch with empty file list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config(output_dir=tmpdir)
            converter = Converter()
            summary = converter.run_batch([], cfg)

            assert summary.persons == 0
            assert summary.visit_occurrences == 0

    def test_run_batch_single_file(self, sample_ccda_file):
        """Test run_batch with a single file."""
        if not sample_ccda_file.exists():
            pytest.skip("Sample CCDA file not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config(output_dir=tmpdir)
            converter = Converter()
            summary = converter.run_batch([str(sample_ccda_file)], cfg)

            # Should have at least one person
            assert summary.persons >= 1

    def test_run_batch_with_report(self, sample_ccda_file):
        """Test run_batch with report generation enabled."""
        if not sample_ccda_file.exists():
            pytest.skip("Sample CCDA file not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config(output_dir=tmpdir, generate_report=True)
            converter = Converter()
            summary = converter.run_batch([str(sample_ccda_file)], cfg)

            assert summary.report is not None

    def test_run_batch_creates_aggregated_output(self, sample_ccda_file):
        """Test run_batch creates aggregated CSV files."""
        if not sample_ccda_file.exists():
            pytest.skip("Sample CCDA file not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = Config(output_dir=tmpdir)
            converter = Converter()
            converter.run_batch([str(sample_ccda_file)], cfg)

            # Check that all output files exist
            assert (Path(tmpdir) / "person.csv").exists()
            assert (Path(tmpdir) / "condition_occurrence.csv").exists()
