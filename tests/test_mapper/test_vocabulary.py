# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for vocabulary mapping."""

import pytest

from ccda2omop.mapper.vocabulary import oid_to_vocabulary_id


class TestOIDToVocabularyID:
    """Tests for oid_to_vocabulary_id function."""

    @pytest.mark.parametrize(
        "oid,expected",
        [
            # Standard medical vocabularies
            ("2.16.840.1.113883.6.96", "SNOMED"),
            ("2.16.840.1.113883.6.88", "RxNorm"),
            ("2.16.840.1.113883.6.1", "LOINC"),
            ("2.16.840.1.113883.6.90", "ICD10CM"),
            ("2.16.840.1.113883.6.103", "ICD9CM"),
            ("2.16.840.1.113883.6.12", "CPT4"),
            ("2.16.840.1.113883.6.14", "HCPCS"),
            ("2.16.840.1.113883.6.13", "HCPCS"),  # CDT OID
            ("2.16.840.1.113883.12.292", "CVX"),
            ("2.16.840.1.113883.6.59", "CVX"),  # alternate
            ("2.16.840.1.113883.6.69", "NDC"),
            ("2.16.840.1.113883.4.9", "UNII"),
            ("2.16.840.1.113883.3.26.1.5", "NDFRT"),
            # Newly added OIDs
            ("2.16.840.1.113883.3.26.1.1", "NCI"),
            ("2.16.840.1.113883.5.4", "ActCode"),
            ("2.16.840.1.113883.5.112", "RouteOfAdministration"),
            # Direct vocabulary names
            ("SNOMED", "SNOMED"),
            ("SNOMED CT", "SNOMED"),
            ("SNOMEDCT", "SNOMED"),
            ("RxNorm", "RxNorm"),
            ("LOINC", "LOINC"),
            ("ICD10CM", "ICD10CM"),
            ("ICD-10-CM", "ICD10CM"),
            ("ICD10", "ICD10CM"),
            ("ICD9CM", "ICD9CM"),
            ("ICD-9-CM", "ICD9CM"),
            ("ICD9", "ICD9CM"),
            ("CPT4", "CPT4"),
            ("CPT", "CPT4"),
            ("CPT-4", "CPT4"),
            ("HCPCS", "HCPCS"),
            ("CVX", "CVX"),
            ("NDC", "NDC"),
            ("UNII", "UNII"),
            ("NDFRT", "NDFRT"),
            ("NDF-RT", "NDFRT"),
            ("NCI", "NCI"),
            ("NCIt", "NCI"),
            ("ActCode", "ActCode"),
            ("ASSERTION", "ActCode"),
            ("RouteOfAdministration", "RouteOfAdministration"),
            # Unknown OIDs return empty string
            ("1.2.3.4.5", ""),
            ("", ""),
            ("foobar", ""),
        ],
    )
    def test_oid_to_vocabulary_id(self, oid: str, expected: str):
        """Test OID to vocabulary ID conversion."""
        result = oid_to_vocabulary_id(oid)
        assert result == expected
