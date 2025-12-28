# Copyright 2025 Christophe Roeder. All rights reserved.

"""Mapping rule data structures."""

from dataclasses import dataclass, field


@dataclass
class Condition:
    """Filter condition for rule application."""

    type: str = ""  # domain_equals, domain_not_equals, field_equals, field_not_equals
    field: str = ""  # For field conditions: field path to check
    value: str = ""  # Value to compare against


@dataclass
class Extraction:
    """Field extraction specification."""

    field: str = ""  # Target field name
    xpath: str = ""  # XPath expression relative to entry
    type: str = ""  # Value type: code, time, float, int, string, effective_time, quantity


@dataclass
class SourceSpec:
    """Source specification for a mapping rule."""

    section: str = ""  # C-CDA section name
    section_oid: str = ""  # Section template OID
    section_oid_entries_required: str = ""  # "Entries required" template OID
    entry_xpath: str = ""  # XPath to locate entries
    entry_type: str = ""  # Entry type category
    extraction: list[Extraction] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)


@dataclass
class TargetSpec:
    """Target specification for a mapping rule."""

    table: str = ""  # OMOP table name
    type_concept_id: int = 0  # Type concept ID (usually 32817)


@dataclass
class FieldMapping:
    """Field-level mapping specification."""

    target: str = ""  # OMOP column name
    xpath: str = ""  # Primary xpath expression
    fallback_xpath: str = ""  # Fallback xpath if primary returns nil
    vocab_xpath: str = ""  # XPath for code system (vocab lookups)
    transform: str = ""  # Transform function name
    optional: bool = False  # Allow missing values
    # Deprecated fields for backward compatibility
    source: str = ""
    vocab_field: str = ""


@dataclass
class IDGenSpec:
    """ID generation specification."""

    base_fields: list[str] = field(default_factory=list)
    generator: str = ""


@dataclass
class MappingRule:
    """Complete mapping rule specification."""

    name: str = ""
    source: SourceSpec = field(default_factory=SourceSpec)
    target: TargetSpec = field(default_factory=TargetSpec)
    fields: list[FieldMapping] = field(default_factory=list)
    id_gen: IDGenSpec = field(default_factory=IDGenSpec)
