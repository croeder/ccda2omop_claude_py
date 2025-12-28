# Copyright 2025 Christophe Roeder. All rights reserved.

"""Vocabulary mapping for C-CDA code systems to OMOP concepts."""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .vocab_loader import VocabLoader

# Code system OIDs
OID_SNOMED_CT = "2.16.840.1.113883.6.96"
OID_RXNORM = "2.16.840.1.113883.6.88"
OID_LOINC = "2.16.840.1.113883.6.1"
OID_ICD10CM = "2.16.840.1.113883.6.90"
OID_ICD9CM = "2.16.840.1.113883.6.103"
OID_CPT = "2.16.840.1.113883.6.12"
OID_HCPCS = "2.16.840.1.113883.6.14"
OID_NCI = "2.16.840.1.113883.3.26.1.1"
OID_ACT_CODE = "2.16.840.1.113883.5.4"
OID_ROUTE_OF_ADMIN = "2.16.840.1.113883.5.112"
OID_CVX = "2.16.840.1.113883.12.292"
OID_ADMIN_GENDER = "2.16.840.1.113883.5.1"
OID_RACE_ETHNICITY = "2.16.840.1.113883.6.238"

# OMOP Standard concept IDs (placeholders - real values from vocabulary)
CONCEPT_MALE = 8507
CONCEPT_FEMALE = 8532
CONCEPT_UNKNOWN = 0

# Race concepts
CONCEPT_WHITE = 8527
CONCEPT_BLACK_OR_AFRICAN_AMERICAN = 8516
CONCEPT_ASIAN = 8515
CONCEPT_AMERICAN_INDIAN_OR_ALASKA = 8657
CONCEPT_NATIVE_HAWAIIAN_OR_PACIFIC = 8557
CONCEPT_OTHER_RACE = 8522
CONCEPT_UNKNOWN_RACE = 0

# Ethnicity concepts
CONCEPT_HISPANIC = 38003563
CONCEPT_NOT_HISPANIC = 38003564

# Visit type concepts
CONCEPT_INPATIENT = 9201
CONCEPT_OUTPATIENT = 9202
CONCEPT_EMERGENCY = 9203
CONCEPT_OFFICE = 581477

# Type concepts (how data was recorded)
CONCEPT_EHR_ENCOUNTER = 32817
CONCEPT_EHR_PROBLEM_LIST = 32817
CONCEPT_EHR_PRESCRIPTION = 32817
CONCEPT_EHR_PROCEDURE = 32817
CONCEPT_EHR_OBSERVATION = 32817

# Placeholder for unmapped concepts
CONCEPT_NO_MAPPING = 0


def oid_to_vocabulary_id(oid: str) -> str:
    """
    Map C-CDA code system OIDs to OMOP vocabulary IDs.

    Also accepts direct vocabulary names (e.g., "CPT4", "SNOMED") and returns them as-is.

    Args:
        oid: Code system OID or vocabulary name

    Returns:
        OMOP vocabulary ID, or empty string if unknown
    """
    mapping = {
        # Standard OIDs
        "2.16.840.1.113883.6.96": "SNOMED",
        "2.16.840.1.113883.6.88": "RxNorm",
        "2.16.840.1.113883.6.1": "LOINC",
        "2.16.840.1.113883.6.90": "ICD10CM",
        "2.16.840.1.113883.6.103": "ICD9CM",
        "2.16.840.1.113883.6.12": "CPT4",
        "2.16.840.1.113883.6.14": "HCPCS",
        "2.16.840.1.113883.6.13": "HCPCS",  # CDT OID sometimes used for HCPCS
        "2.16.840.1.113883.12.292": "CVX",
        "2.16.840.1.113883.6.59": "CVX",  # Alternate CVX OID
        "2.16.840.1.113883.6.69": "NDC",
        "2.16.840.1.113883.4.9": "UNII",
        "2.16.840.1.113883.3.26.1.5": "NDFRT",
        "2.16.840.1.113883.3.26.1.1": "NCI",
        "2.16.840.1.113883.5.4": "ActCode",
        "2.16.840.1.113883.5.112": "RouteOfAdministration",
        # Direct vocabulary names
        "SNOMED": "SNOMED",
        "SNOMED CT": "SNOMED",
        "SNOMEDCT": "SNOMED",
        "RxNorm": "RxNorm",
        "LOINC": "LOINC",
        "ICD10CM": "ICD10CM",
        "ICD-10-CM": "ICD10CM",
        "ICD10": "ICD10CM",
        "ICD9CM": "ICD9CM",
        "ICD-9-CM": "ICD9CM",
        "ICD9": "ICD9CM",
        "CPT4": "CPT4",
        "CPT": "CPT4",
        "CPT-4": "CPT4",
        "HCPCS": "HCPCS",
        "CVX": "CVX",
        "NDC": "NDC",
        "UNII": "UNII",
        "NDFRT": "NDFRT",
        "NDF-RT": "NDFRT",
        "NCI": "NCI",
        "NCIt": "NCI",
        "ActCode": "ActCode",
        "ASSERTION": "ActCode",
        "RouteOfAdministration": "RouteOfAdministration",
    }
    return mapping.get(oid, "")


def get_code_system_name(oid: str) -> str:
    """Get a human-readable name for a code system OID."""
    names = {
        OID_SNOMED_CT: "SNOMED-CT",
        OID_RXNORM: "RxNorm",
        OID_LOINC: "LOINC",
        OID_ICD10CM: "ICD-10-CM",
        OID_ICD9CM: "ICD-9-CM",
        OID_CPT: "CPT",
        OID_CVX: "CVX",
    }
    return names.get(oid, oid)


class VocabularyMapper:
    """Provides concept mappings for OMOP using loaded vocabulary tables."""

    def __init__(self, vocab_loader: Optional["VocabLoader"] = None):
        """
        Create a vocabulary mapper.

        Args:
            vocab_loader: Optional VocabLoader for OMOP concept lookups
        """
        self.vocab_loader = vocab_loader

        # Fallback concept mappings
        self._gender_concepts = {
            "M": CONCEPT_MALE,
            "F": CONCEPT_FEMALE,
            "UN": CONCEPT_UNKNOWN,
        }

        self._race_concepts = {
            "2106-3": CONCEPT_WHITE,
            "2054-5": CONCEPT_BLACK_OR_AFRICAN_AMERICAN,
            "2028-9": CONCEPT_ASIAN,
            "1002-5": CONCEPT_AMERICAN_INDIAN_OR_ALASKA,
            "2076-8": CONCEPT_NATIVE_HAWAIIAN_OR_PACIFIC,
            "2131-1": CONCEPT_OTHER_RACE,
        }

        self._ethnicity_concepts = {
            "2135-2": CONCEPT_HISPANIC,
            "2186-5": CONCEPT_NOT_HISPANIC,
        }

        self._visit_type_concepts = {
            "IMP": CONCEPT_INPATIENT,
            "AMB": CONCEPT_OUTPATIENT,
            "EMER": CONCEPT_EMERGENCY,
            "VR": CONCEPT_OFFICE,
        }

    def map_gender(self, code: str) -> int:
        """Map a gender code to an OMOP concept ID."""
        return self._gender_concepts.get(code, CONCEPT_UNKNOWN)

    def map_race(self, code: str) -> int:
        """Map a race code to an OMOP concept ID."""
        return self._race_concepts.get(code, CONCEPT_UNKNOWN_RACE)

    def map_ethnicity(self, code: str) -> int:
        """Map an ethnicity code to an OMOP concept ID."""
        return self._ethnicity_concepts.get(code, CONCEPT_NO_MAPPING)

    def map_visit_type(self, class_code: str) -> int:
        """Map an encounter class code to an OMOP visit concept ID."""
        return self._visit_type_concepts.get(class_code, CONCEPT_OUTPATIENT)

    def map_condition_code(self, code: str, code_system: str) -> int:
        """Map a condition code to an OMOP concept ID (first match)."""
        ids = self.map_condition_codes(code, code_system)
        return ids[0] if ids else CONCEPT_NO_MAPPING

    def map_condition_codes(self, code: str, code_system: str) -> list[int]:
        """Map a condition code to all matching OMOP concept IDs."""
        if self.vocab_loader is None or not code:
            return []

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            return []

        return self.vocab_loader.get_standard_concept_ids(vocab_id, code)

    def map_drug_code(self, code: str, code_system: str) -> int:
        """Map a drug code to an OMOP concept ID (first match)."""
        ids = self.map_drug_codes(code, code_system)
        return ids[0] if ids else CONCEPT_NO_MAPPING

    def map_drug_codes(self, code: str, code_system: str) -> list[int]:
        """Map a drug code to all matching OMOP concept IDs."""
        if self.vocab_loader is None or not code:
            return []

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            return []

        return self.vocab_loader.get_standard_concept_ids(vocab_id, code)

    def map_procedure_code(self, code: str, code_system: str) -> int:
        """Map a procedure code to an OMOP concept ID (first match)."""
        ids = self.map_procedure_codes(code, code_system)
        return ids[0] if ids else CONCEPT_NO_MAPPING

    def map_procedure_codes(self, code: str, code_system: str) -> list[int]:
        """Map a procedure code to all matching OMOP concept IDs."""
        if self.vocab_loader is None or not code:
            return []

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            return []

        return self.vocab_loader.get_standard_concept_ids(vocab_id, code)

    def map_measurement_code(self, code: str, code_system: str) -> int:
        """Map a measurement code to an OMOP concept ID (first match)."""
        ids = self.map_measurement_codes(code, code_system)
        return ids[0] if ids else CONCEPT_NO_MAPPING

    def map_measurement_codes(self, code: str, code_system: str) -> list[int]:
        """Map a measurement code to all matching OMOP concept IDs."""
        if self.vocab_loader is None or not code:
            return []

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            return []

        return self.vocab_loader.get_standard_concept_ids(vocab_id, code)

    def map_observation_code(self, code: str, code_system: str) -> int:
        """Map an observation code to an OMOP concept ID (first match)."""
        ids = self.map_observation_codes(code, code_system)
        return ids[0] if ids else CONCEPT_NO_MAPPING

    def map_observation_codes(self, code: str, code_system: str) -> list[int]:
        """Map an observation code to all matching OMOP concept IDs."""
        if self.vocab_loader is None or not code:
            return []

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            return []

        return self.vocab_loader.get_standard_concept_ids(vocab_id, code)

    def map_device_code(self, code: str, code_system: str) -> int:
        """Map a device code to an OMOP concept ID (first match)."""
        ids = self.map_device_codes(code, code_system)
        return ids[0] if ids else CONCEPT_NO_MAPPING

    def map_device_codes(self, code: str, code_system: str) -> list[int]:
        """Map a device code to all matching OMOP concept IDs."""
        if self.vocab_loader is None or not code:
            return []

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            return []

        return self.vocab_loader.get_standard_concept_ids(vocab_id, code)

    def map_unit_code(self, unit: str) -> int:
        """Map a unit code (UCUM) to an OMOP concept ID."""
        if self.vocab_loader is None or not unit:
            return CONCEPT_NO_MAPPING

        return self.vocab_loader.get_standard_concept_id("UCUM", unit)

    def map_route_code(self, code: str, code_system: str) -> int:
        """Map a route code to an OMOP concept ID."""
        if self.vocab_loader is None or not code:
            return CONCEPT_NO_MAPPING

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            vocab_id = "SNOMED"  # Default for route codes

        return self.vocab_loader.get_standard_concept_id(vocab_id, code)

    def map_observation_value_code(self, code: str, code_system: str) -> int:
        """Map a coded observation value to an OMOP concept ID."""
        if self.vocab_loader is None or not code:
            return CONCEPT_NO_MAPPING

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            vocab_id = "SNOMED"

        return self.vocab_loader.get_standard_concept_id(vocab_id, code)

    def map_measurement_value_code(self, code: str, code_system: str) -> int:
        """Map a coded measurement value to an OMOP concept ID."""
        if self.vocab_loader is None or not code:
            return CONCEPT_NO_MAPPING

        vocab_id = oid_to_vocabulary_id(code_system)
        if not vocab_id:
            vocab_id = "SNOMED"

        return self.vocab_loader.get_standard_concept_id(vocab_id, code)

    def get_concept_domain(self, concept_id: int) -> str:
        """Get the domain_id for a concept."""
        if self.vocab_loader is None:
            return ""
        return self.vocab_loader.get_concept_domain(concept_id)
