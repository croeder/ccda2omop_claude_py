# Copyright 2025 Christophe Roeder. All rights reserved.

"""C-CDA data models as Python dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from lxml.etree import _Element


@dataclass
class CodedValue:
    """Represents a coded entry with code system information."""

    code: str = ""
    code_system: str = ""
    code_system_name: str = ""
    display_name: str = ""
    original_text: str = ""


@dataclass
class EffectiveTime:
    """Represents a time or time range."""

    low: Optional[datetime] = None
    high: Optional[datetime] = None
    value: Optional[datetime] = None


@dataclass
class Quantity:
    """Represents a quantity with unit."""

    value: float = 0.0
    unit: str = ""


@dataclass
class Name:
    """Represents a person's name."""

    given: str = ""
    family: str = ""
    suffix: str = ""
    prefix: str = ""


@dataclass
class Address:
    """Represents a postal address."""

    street_address: list[str] = field(default_factory=list)
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""


@dataclass
class Telecom:
    """Represents a telecommunication address (phone, email, etc.)."""

    use: str = ""
    value: str = ""


@dataclass
class Author:
    """Represents the document author."""

    time: Optional[datetime] = None
    id: str = ""
    name: Name = field(default_factory=Name)
    organization: str = ""


@dataclass
class Custodian:
    """Represents the document custodian organization."""

    id: str = ""
    name: str = ""
    address: Address = field(default_factory=Address)
    telecom: Telecom = field(default_factory=Telecom)


@dataclass
class Patient:
    """Represents patient demographics from the C-CDA recordTarget."""

    id: str = ""
    name: Name = field(default_factory=Name)
    birth_time: Optional[datetime] = None
    gender: CodedValue = field(default_factory=CodedValue)
    race: CodedValue = field(default_factory=CodedValue)
    ethnicity: CodedValue = field(default_factory=CodedValue)
    address: Address = field(default_factory=Address)
    telecom: list[Telecom] = field(default_factory=list)
    marital_status: CodedValue = field(default_factory=CodedValue)
    language: CodedValue = field(default_factory=CodedValue)


@dataclass
class Encounter:
    """Represents an encounter from the Encounters section."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    performer: str = ""
    location: str = ""
    discharge_code: CodedValue = field(default_factory=CodedValue)


@dataclass
class Problem:
    """Represents a problem/condition from the Problems section."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    status: CodedValue = field(default_factory=CodedValue)
    severity: CodedValue = field(default_factory=CodedValue)


@dataclass
class Medication:
    """Represents a medication from the Medications section."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    dose_quantity: Quantity = field(default_factory=Quantity)
    rate_quantity: Quantity = field(default_factory=Quantity)
    route_code: CodedValue = field(default_factory=CodedValue)
    status: CodedValue = field(default_factory=CodedValue)
    instructions: str = ""
    refills: int = 0
    days_supply: int = 0


@dataclass
class Procedure:
    """Represents a procedure from the Procedures section."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    status: CodedValue = field(default_factory=CodedValue)
    target_site: CodedValue = field(default_factory=CodedValue)
    performer: str = ""


@dataclass
class ReferenceRange:
    """Represents a lab result reference range."""

    low: float = 0.0
    high: float = 0.0
    text: str = ""


@dataclass
class VitalSign:
    """Represents a vital sign measurement."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: Optional[datetime] = None
    value: float = 0.0
    unit: str = ""
    interpretation: CodedValue = field(default_factory=CodedValue)


@dataclass
class LabResult:
    """Represents a laboratory result."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: Optional[datetime] = None
    value: float = 0.0
    value_string: str = ""
    unit: str = ""
    reference_range: ReferenceRange = field(default_factory=ReferenceRange)
    interpretation: CodedValue = field(default_factory=CodedValue)
    status: CodedValue = field(default_factory=CodedValue)


@dataclass
class Allergy:
    """Represents an allergy or intolerance."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    status: CodedValue = field(default_factory=CodedValue)
    severity: CodedValue = field(default_factory=CodedValue)
    reaction: CodedValue = field(default_factory=CodedValue)
    substance: CodedValue = field(default_factory=CodedValue)


@dataclass
class Immunization:
    """Represents an immunization administration."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: Optional[datetime] = None
    status: CodedValue = field(default_factory=CodedValue)
    route_code: CodedValue = field(default_factory=CodedValue)
    dose_quantity: Quantity = field(default_factory=Quantity)
    lot_number: str = ""
    manufacturer: str = ""


@dataclass
class Device:
    """Represents a medical device."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    status: CodedValue = field(default_factory=CodedValue)
    udi: str = ""  # Unique Device Identifier


@dataclass
class SocialObservation:
    """Represents a social history observation."""

    id: str = ""
    code: CodedValue = field(default_factory=CodedValue)
    effective_time: EffectiveTime = field(default_factory=EffectiveTime)
    value: CodedValue = field(default_factory=CodedValue)
    value_quantity: Quantity = field(default_factory=Quantity)
    status: CodedValue = field(default_factory=CodedValue)


@dataclass
class SectionMetadata:
    """Contains metadata about a parsed C-CDA section."""

    template_oid: str = ""
    entries_required: bool = False


@dataclass
class Document:
    """Represents a parsed C-CDA clinical document."""

    patient: Patient = field(default_factory=Patient)
    author: Author = field(default_factory=Author)
    custodian: Custodian = field(default_factory=Custodian)
    encounters: list[Encounter] = field(default_factory=list)
    problems: list[Problem] = field(default_factory=list)
    medications: list[Medication] = field(default_factory=list)
    procedures: list[Procedure] = field(default_factory=list)
    vital_signs: list[VitalSign] = field(default_factory=list)
    lab_results: list[LabResult] = field(default_factory=list)
    allergies: list[Allergy] = field(default_factory=list)
    immunizations: list[Immunization] = field(default_factory=list)
    devices: list[Device] = field(default_factory=list)
    observations: list[SocialObservation] = field(default_factory=list)
    section_meta: dict[str, SectionMetadata] = field(default_factory=dict)
    xml_root: Optional[_Element] = None  # Store for xpath-based extraction
