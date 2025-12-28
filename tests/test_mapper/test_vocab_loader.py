# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for vocabulary loader."""

import pytest

from ccda2omop.mapper.vocab_loader import VocabLoader


class TestVocabLoader:
    """Tests for VocabLoader class."""

    def test_new_vocab_loader(self):
        """Test creating a new VocabLoader."""
        vl = VocabLoader()
        assert vl is not None
        assert vl._concept_index is not None
        assert vl._concept_by_id is not None
        assert vl._maps_to is not None
        assert VocabLoader.RELEVANT_VOCABS is not None

    def test_relevant_vocabs(self):
        """Test that expected vocabularies are marked as relevant."""
        expected_vocabs = [
            "SNOMED",
            "RxNorm",
            "LOINC",
            "ICD10CM",
            "ICD9CM",
            "CPT4",
            "HCPCS",
            "CVX",
            "NDC",
            "UNII",
            "NDFRT",
            "NCI",
            "ActCode",
            "RouteOfAdministration",
            "Gender",
            "Race",
            "Ethnicity",
            "UCUM",
            "Visit",
        ]

        for vocab in expected_vocabs:
            assert vocab in VocabLoader.RELEVANT_VOCABS, f"RELEVANT_VOCABS missing {vocab}"

    def test_lookup_concept_empty(self):
        """Test lookup on empty loader returns None."""
        vl = VocabLoader()

        result = vl.lookup_concept("SNOMED", "44054006")
        assert result is None

        result_by_id = vl.lookup_concept_by_id(44054006)
        assert result_by_id is None

    def test_get_standard_concept_id_empty(self):
        """Test get standard concept ID on empty loader returns empty list."""
        vl = VocabLoader()

        result = vl.get_standard_concept_ids("SNOMED", "44054006")
        assert result == []

    def test_get_concept_domain_empty(self):
        """Test get concept domain on empty loader returns empty string."""
        vl = VocabLoader()

        result = vl.get_concept_domain(44054006)
        assert result == ""
