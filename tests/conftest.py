# Copyright 2025 Christophe Roeder. All rights reserved.

"""Pytest fixtures for ccda2omop tests."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_ccda_file(fixtures_dir: Path) -> Path:
    """Return path to sample C-CDA XML file."""
    return fixtures_dir / "sample_ccda.xml"


@pytest.fixture
def sample_concept_file(fixtures_dir: Path) -> Path:
    """Return path to sample CONCEPT.csv file."""
    return fixtures_dir / "CONCEPT_sample.csv"
