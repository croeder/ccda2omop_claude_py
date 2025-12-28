# Copyright 2025 Christophe Roeder. All rights reserved.

"""OMOP CDM 5.3 data models as Python dataclasses."""

from dataclasses import dataclass, field, fields
from datetime import date, datetime
from typing import ClassVar, Optional


@dataclass
class OMOPRecord:
    """Base class for all OMOP records with CSV serialization support."""

    # CSV column order defined by each subclass
    _csv_columns: ClassVar[list[str]] = []

    def to_csv_row(self) -> list[str]:
        """Convert record to CSV row following column order."""
        result = []
        for col in self._csv_columns:
            value = getattr(self, col)
            result.append(self._format_value(value))
        return result

    @classmethod
    def csv_headers(cls) -> list[str]:
        """Return CSV column headers."""
        return cls._csv_columns.copy()

    @staticmethod
    def _format_value(value) -> str:
        """Format a value for CSV output."""
        if value is None:
            return ""
        if isinstance(value, datetime):
            if value.hour == 0 and value.minute == 0 and value.second == 0:
                return value.strftime("%Y-%m-%d")
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, bool):
            return "1" if value else "0"
        if isinstance(value, float):
            return f"{value:g}"
        return str(value)


@dataclass
class Person(OMOPRecord):
    """OMOP CDM 5.3 PERSON table."""

    person_id: int = 0
    gender_concept_id: int = 0
    year_of_birth: int = 0
    month_of_birth: Optional[int] = None
    day_of_birth: Optional[int] = None
    birth_datetime: Optional[datetime] = None
    race_concept_id: int = 0
    ethnicity_concept_id: int = 0
    location_id: Optional[int] = None
    provider_id: Optional[int] = None
    care_site_id: Optional[int] = None
    person_source_value: str = ""
    gender_source_value: str = ""
    gender_source_concept_id: Optional[int] = None
    race_source_value: str = ""
    race_source_concept_id: Optional[int] = None
    ethnicity_source_value: str = ""
    ethnicity_source_concept_id: Optional[int] = None
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "person_id",
        "gender_concept_id",
        "year_of_birth",
        "month_of_birth",
        "day_of_birth",
        "birth_datetime",
        "race_concept_id",
        "ethnicity_concept_id",
        "location_id",
        "provider_id",
        "care_site_id",
        "person_source_value",
        "gender_source_value",
        "gender_source_concept_id",
        "race_source_value",
        "race_source_concept_id",
        "ethnicity_source_value",
        "ethnicity_source_concept_id",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class VisitOccurrence(OMOPRecord):
    """OMOP CDM 5.3 VISIT_OCCURRENCE table."""

    visit_occurrence_id: int = 0
    person_id: int = 0
    visit_concept_id: int = 0
    visit_start_date: Optional[datetime] = None
    visit_start_datetime: Optional[datetime] = None
    visit_end_date: Optional[datetime] = None
    visit_end_datetime: Optional[datetime] = None
    visit_type_concept_id: int = 0
    provider_id: Optional[int] = None
    care_site_id: Optional[int] = None
    visit_source_value: str = ""
    visit_source_concept_id: Optional[int] = None
    admitted_from_concept_id: Optional[int] = None
    admitted_from_source_value: str = ""
    discharge_to_concept_id: Optional[int] = None
    discharge_to_source_value: str = ""
    preceding_visit_occurrence_id: Optional[int] = None
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "visit_occurrence_id",
        "person_id",
        "visit_concept_id",
        "visit_start_date",
        "visit_start_datetime",
        "visit_end_date",
        "visit_end_datetime",
        "visit_type_concept_id",
        "provider_id",
        "care_site_id",
        "visit_source_value",
        "visit_source_concept_id",
        "admitted_from_concept_id",
        "admitted_from_source_value",
        "discharge_to_concept_id",
        "discharge_to_source_value",
        "preceding_visit_occurrence_id",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class ConditionOccurrence(OMOPRecord):
    """OMOP CDM 5.3 CONDITION_OCCURRENCE table."""

    condition_occurrence_id: int = 0
    person_id: int = 0
    condition_concept_id: int = 0
    condition_start_date: Optional[datetime] = None
    condition_start_datetime: Optional[datetime] = None
    condition_end_date: Optional[datetime] = None
    condition_end_datetime: Optional[datetime] = None
    condition_type_concept_id: int = 0
    condition_status_concept_id: Optional[int] = None
    stop_reason: str = ""
    provider_id: Optional[int] = None
    visit_occurrence_id: Optional[int] = None
    visit_detail_id: Optional[int] = None
    condition_source_value: str = ""
    condition_source_concept_id: Optional[int] = None
    condition_status_source_value: str = ""
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "condition_occurrence_id",
        "person_id",
        "condition_concept_id",
        "condition_start_date",
        "condition_start_datetime",
        "condition_end_date",
        "condition_end_datetime",
        "condition_type_concept_id",
        "condition_status_concept_id",
        "stop_reason",
        "provider_id",
        "visit_occurrence_id",
        "visit_detail_id",
        "condition_source_value",
        "condition_source_concept_id",
        "condition_status_source_value",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class DrugExposure(OMOPRecord):
    """OMOP CDM 5.3 DRUG_EXPOSURE table."""

    drug_exposure_id: int = 0
    person_id: int = 0
    drug_concept_id: int = 0
    drug_exposure_start_date: Optional[datetime] = None
    drug_exposure_start_datetime: Optional[datetime] = None
    drug_exposure_end_date: Optional[datetime] = None
    drug_exposure_end_datetime: Optional[datetime] = None
    verbatim_end_date: Optional[datetime] = None
    drug_type_concept_id: int = 0
    stop_reason: str = ""
    refills: Optional[int] = None
    quantity: Optional[float] = None
    days_supply: Optional[int] = None
    sig: str = ""
    route_concept_id: Optional[int] = None
    lot_number: str = ""
    provider_id: Optional[int] = None
    visit_occurrence_id: Optional[int] = None
    visit_detail_id: Optional[int] = None
    drug_source_value: str = ""
    drug_source_concept_id: Optional[int] = None
    route_source_value: str = ""
    dose_unit_source_value: str = ""
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "drug_exposure_id",
        "person_id",
        "drug_concept_id",
        "drug_exposure_start_date",
        "drug_exposure_start_datetime",
        "drug_exposure_end_date",
        "drug_exposure_end_datetime",
        "verbatim_end_date",
        "drug_type_concept_id",
        "stop_reason",
        "refills",
        "quantity",
        "days_supply",
        "sig",
        "route_concept_id",
        "lot_number",
        "provider_id",
        "visit_occurrence_id",
        "visit_detail_id",
        "drug_source_value",
        "drug_source_concept_id",
        "route_source_value",
        "dose_unit_source_value",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class ProcedureOccurrence(OMOPRecord):
    """OMOP CDM 5.3 PROCEDURE_OCCURRENCE table."""

    procedure_occurrence_id: int = 0
    person_id: int = 0
    procedure_concept_id: int = 0
    procedure_date: Optional[datetime] = None
    procedure_datetime: Optional[datetime] = None
    procedure_type_concept_id: int = 0
    modifier_concept_id: Optional[int] = None
    quantity: Optional[int] = None
    provider_id: Optional[int] = None
    visit_occurrence_id: Optional[int] = None
    visit_detail_id: Optional[int] = None
    procedure_source_value: str = ""
    procedure_source_concept_id: Optional[int] = None
    modifier_source_value: str = ""
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "procedure_occurrence_id",
        "person_id",
        "procedure_concept_id",
        "procedure_date",
        "procedure_datetime",
        "procedure_type_concept_id",
        "modifier_concept_id",
        "quantity",
        "provider_id",
        "visit_occurrence_id",
        "visit_detail_id",
        "procedure_source_value",
        "procedure_source_concept_id",
        "modifier_source_value",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class Measurement(OMOPRecord):
    """OMOP CDM 5.3 MEASUREMENT table."""

    measurement_id: int = 0
    person_id: int = 0
    measurement_concept_id: int = 0
    measurement_date: Optional[datetime] = None
    measurement_datetime: Optional[datetime] = None
    measurement_time: str = ""
    measurement_type_concept_id: int = 0
    operator_concept_id: Optional[int] = None
    value_as_number: Optional[float] = None
    value_as_concept_id: Optional[int] = None
    unit_concept_id: Optional[int] = None
    range_low: Optional[float] = None
    range_high: Optional[float] = None
    provider_id: Optional[int] = None
    visit_occurrence_id: Optional[int] = None
    visit_detail_id: Optional[int] = None
    measurement_source_value: str = ""
    measurement_source_concept_id: Optional[int] = None
    unit_source_value: str = ""
    value_source_value: str = ""
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "measurement_id",
        "person_id",
        "measurement_concept_id",
        "measurement_date",
        "measurement_datetime",
        "measurement_time",
        "measurement_type_concept_id",
        "operator_concept_id",
        "value_as_number",
        "value_as_concept_id",
        "unit_concept_id",
        "range_low",
        "range_high",
        "provider_id",
        "visit_occurrence_id",
        "visit_detail_id",
        "measurement_source_value",
        "measurement_source_concept_id",
        "unit_source_value",
        "value_source_value",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class Observation(OMOPRecord):
    """OMOP CDM 5.3 OBSERVATION table."""

    observation_id: int = 0
    person_id: int = 0
    observation_concept_id: int = 0
    observation_date: Optional[datetime] = None
    observation_datetime: Optional[datetime] = None
    observation_type_concept_id: int = 0
    value_as_number: Optional[float] = None
    value_as_string: str = ""
    value_as_concept_id: Optional[int] = None
    qualifier_concept_id: Optional[int] = None
    unit_concept_id: Optional[int] = None
    provider_id: Optional[int] = None
    visit_occurrence_id: Optional[int] = None
    visit_detail_id: Optional[int] = None
    observation_source_value: str = ""
    observation_source_concept_id: Optional[int] = None
    unit_source_value: str = ""
    qualifier_source_value: str = ""
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "observation_id",
        "person_id",
        "observation_concept_id",
        "observation_date",
        "observation_datetime",
        "observation_type_concept_id",
        "value_as_number",
        "value_as_string",
        "value_as_concept_id",
        "qualifier_concept_id",
        "unit_concept_id",
        "provider_id",
        "visit_occurrence_id",
        "visit_detail_id",
        "observation_source_value",
        "observation_source_concept_id",
        "unit_source_value",
        "qualifier_source_value",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class DeviceExposure(OMOPRecord):
    """OMOP CDM 5.3 DEVICE_EXPOSURE table."""

    device_exposure_id: int = 0
    person_id: int = 0
    device_concept_id: int = 0
    device_exposure_start_date: Optional[datetime] = None
    device_exposure_start_datetime: Optional[datetime] = None
    device_exposure_end_date: Optional[datetime] = None
    device_exposure_end_datetime: Optional[datetime] = None
    device_type_concept_id: int = 0
    unique_device_id: str = ""
    quantity: Optional[int] = None
    provider_id: Optional[int] = None
    visit_occurrence_id: Optional[int] = None
    visit_detail_id: Optional[int] = None
    device_source_value: str = ""
    device_source_concept_id: Optional[int] = None
    mapping_rule: str = ""
    source_file: str = ""

    _csv_columns: ClassVar[list[str]] = [
        "device_exposure_id",
        "person_id",
        "device_concept_id",
        "device_exposure_start_date",
        "device_exposure_start_datetime",
        "device_exposure_end_date",
        "device_exposure_end_datetime",
        "device_type_concept_id",
        "unique_device_id",
        "quantity",
        "provider_id",
        "visit_occurrence_id",
        "visit_detail_id",
        "device_source_value",
        "device_source_concept_id",
        "mapping_rule",
        "source_file",
    ]


@dataclass
class OMOPData:
    """Container for all OMOP CDM tables generated from a C-CDA document."""

    persons: list[Person] = field(default_factory=list)
    visit_occurrences: list[VisitOccurrence] = field(default_factory=list)
    condition_occurrences: list[ConditionOccurrence] = field(default_factory=list)
    drug_exposures: list[DrugExposure] = field(default_factory=list)
    procedure_occurrences: list[ProcedureOccurrence] = field(default_factory=list)
    measurements: list[Measurement] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    device_exposures: list[DeviceExposure] = field(default_factory=list)
