# Copyright 2025 Christophe Roeder. All rights reserved.

"""Deterministic ID generation for OMOP records using SHA256 hashing."""

import hashlib
import struct


def generate_id(*values: str) -> int:
    """
    Generate a deterministic int64 ID from input values.
    Uses SHA256 hash truncated to int64 for reproducible IDs.

    Args:
        *values: Variable number of string values to hash

    Returns:
        Positive int64 ID
    """
    h = hashlib.sha256()
    for v in values:
        h.update(v.encode("utf-8"))
        h.update(b"\x00")  # separator

    digest = h.digest()
    # Take first 8 bytes as big-endian unsigned int64
    raw_id = struct.unpack(">Q", digest[:8])[0]
    # Convert to signed int64 range and ensure positive
    if raw_id > (2**63 - 1):
        raw_id = raw_id - 2**64
    return abs(raw_id)


def generate_person_id(patient_id: str, source_system: str) -> int:
    """Create a deterministic person ID from patient identifiers."""
    return generate_id("person", patient_id, source_system)


def generate_visit_id(person_id: int, encounter_id: str) -> int:
    """Create a deterministic visit ID."""
    return generate_id("visit", str(person_id), encounter_id)


def generate_condition_id(person_id: int, condition_code: str, start_date: str) -> int:
    """Create a deterministic condition occurrence ID."""
    return generate_id("condition", str(person_id), condition_code, start_date)


def generate_drug_exposure_id(person_id: int, drug_code: str, start_date: str) -> int:
    """Create a deterministic drug exposure ID."""
    return generate_id("drug", str(person_id), drug_code, start_date)


def generate_procedure_id(person_id: int, procedure_code: str, date: str) -> int:
    """Create a deterministic procedure occurrence ID."""
    return generate_id("procedure", str(person_id), procedure_code, date)


def generate_measurement_id(
    person_id: int, measurement_code: str, date: str, value: str
) -> int:
    """Create a deterministic measurement ID."""
    return generate_id("measurement", str(person_id), measurement_code, date, value)


def generate_observation_id(person_id: int, observation_code: str, date: str) -> int:
    """Create a deterministic observation ID."""
    return generate_id("observation", str(person_id), observation_code, date)


def generate_device_exposure_id(
    person_id: int, device_code: str, start_date: str
) -> int:
    """Create a deterministic device exposure ID."""
    return generate_id("device", str(person_id), device_code, start_date)
