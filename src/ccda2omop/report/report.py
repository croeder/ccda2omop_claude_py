# Copyright 2025 Christophe Roeder. All rights reserved.

"""Conversion reporting and metrics."""

import json
from dataclasses import dataclass, field
from typing import TextIO

from ..omop.models import OMOPData


@dataclass
class FieldStats:
    """Tracks population statistics for a field."""

    populated: int = 0
    total: int = 0


@dataclass
class SectionMetrics:
    """Tracks metrics for a CCDA section."""

    entries_found: int = 0
    records_created: int = 0
    skipped: int = 0
    target_tables: dict[str, int] = field(default_factory=dict)


@dataclass
class VocabStats:
    """Tracks vocabulary mapping statistics."""

    codes_seen: int = 0
    mapped_standard: int = 0
    source_only: int = 0


@dataclass
class DomainRoute:
    """Records when a record is routed to a different table based on domain."""

    source_section: str = ""
    original_target: str = ""
    actual_target: str = ""
    count: int = 0
    reason: str = ""


@dataclass
class ConversionReport:
    """Holds comprehensive metrics about a CCDA-to-OMOP conversion."""

    # Document-level metrics
    documents_processed: int = 0
    documents_with_errors: int = 0

    # Section-level metrics (CCDA sections -> entries found)
    entries_by_section: dict[str, SectionMetrics] = field(default_factory=dict)

    # Output metrics (OMOP tables -> records created)
    records_by_table: dict[str, int] = field(default_factory=dict)

    # Field population rates per table
    field_population: dict[str, dict[str, FieldStats]] = field(default_factory=dict)

    # Concept mapping quality
    concept_mappings: dict[str, VocabStats] = field(default_factory=dict)

    # Domain routing - records moved between tables
    domain_routing: list[DomainRoute] = field(default_factory=list)

    # Skip reasons
    skipped_entries: dict[str, int] = field(default_factory=dict)

    def add_document(self, has_error: bool) -> None:
        """Increment the document counter."""
        self.documents_processed += 1
        if has_error:
            self.documents_with_errors += 1

    def add_section_entry(self, section: str) -> None:
        """Record an entry found in a CCDA section."""
        if section not in self.entries_by_section:
            self.entries_by_section[section] = SectionMetrics()
        self.entries_by_section[section].entries_found += 1

    def add_section_record(self, section: str, target_table: str) -> None:
        """Record a record created from a section entry."""
        if section not in self.entries_by_section:
            self.entries_by_section[section] = SectionMetrics()
        self.entries_by_section[section].records_created += 1
        tables = self.entries_by_section[section].target_tables
        tables[target_table] = tables.get(target_table, 0) + 1

    def add_skipped(self, section: str, reason: str) -> None:
        """Record a skipped entry with reason."""
        if section not in self.entries_by_section:
            self.entries_by_section[section] = SectionMetrics()
        self.entries_by_section[section].skipped += 1
        self.skipped_entries[reason] = self.skipped_entries.get(reason, 0) + 1

    def add_concept_mapping(self, vocab: str, mapped_to_standard: bool) -> None:
        """Record a vocabulary mapping attempt."""
        if vocab not in self.concept_mappings:
            self.concept_mappings[vocab] = VocabStats()
        self.concept_mappings[vocab].codes_seen += 1
        if mapped_to_standard:
            self.concept_mappings[vocab].mapped_standard += 1
        else:
            self.concept_mappings[vocab].source_only += 1

    def add_domain_route(
        self, section: str, original_target: str, actual_target: str, reason: str
    ) -> None:
        """Record domain-based routing."""
        # Find existing route or create new one
        for route in self.domain_routing:
            if (
                route.source_section == section
                and route.original_target == original_target
                and route.actual_target == actual_target
            ):
                route.count += 1
                return
        self.domain_routing.append(
            DomainRoute(
                source_section=section,
                original_target=original_target,
                actual_target=actual_target,
                count=1,
                reason=reason,
            )
        )

    def calculate_from_omop_data(self, data: OMOPData) -> None:
        """Populate the report from OMOP output data."""
        # Record counts by table
        self.records_by_table["person"] = len(data.persons)
        self.records_by_table["visit_occurrence"] = len(data.visit_occurrences)
        self.records_by_table["condition_occurrence"] = len(data.condition_occurrences)
        self.records_by_table["drug_exposure"] = len(data.drug_exposures)
        self.records_by_table["procedure_occurrence"] = len(data.procedure_occurrences)
        self.records_by_table["measurement"] = len(data.measurements)
        self.records_by_table["observation"] = len(data.observations)
        self.records_by_table["device_exposure"] = len(data.device_exposures)

        # Calculate field population rates
        self._calculate_condition_fields(data.condition_occurrences)
        self._calculate_drug_fields(data.drug_exposures)
        self._calculate_procedure_fields(data.procedure_occurrences)
        self._calculate_measurement_fields(data.measurements)
        self._calculate_observation_fields(data.observations)
        self._calculate_device_fields(data.device_exposures)

        # Track section -> table mappings from MappingRule field
        self._track_section_mappings(data)

    def _track_section_mappings(self, data: OMOPData) -> None:
        """Parse MappingRule to extract section info."""
        for c in data.condition_occurrences:
            section = _extract_section_from_rule(c.mapping_rule)
            if section:
                self.add_section_record(section, "condition_occurrence")
        for d in data.drug_exposures:
            section = _extract_section_from_rule(d.mapping_rule)
            if section:
                self.add_section_record(section, "drug_exposure")
        for p in data.procedure_occurrences:
            section = _extract_section_from_rule(p.mapping_rule)
            if section:
                self.add_section_record(section, "procedure_occurrence")
        for m in data.measurements:
            section = _extract_section_from_rule(m.mapping_rule)
            if section:
                self.add_section_record(section, "measurement")
        for o in data.observations:
            section = _extract_section_from_rule(o.mapping_rule)
            if section:
                self.add_section_record(section, "observation")
        for d in data.device_exposures:
            section = _extract_section_from_rule(d.mapping_rule)
            if section:
                self.add_section_record(section, "device_exposure")

    def _calculate_condition_fields(self, records: list) -> None:
        """Calculate field population rates for condition_occurrence."""
        if not records:
            return
        self.field_population["condition_occurrence"] = {}
        total = len(records)

        concept_id_count = sum(1 for r in records if r.condition_concept_id > 0)
        end_date_count = sum(1 for r in records if r.condition_end_date is not None)
        source_value_count = sum(1 for r in records if r.condition_source_value)
        visit_id_count = sum(1 for r in records if r.visit_occurrence_id is not None)

        self.field_population["condition_occurrence"]["condition_concept_id (>0)"] = FieldStats(
            concept_id_count, total
        )
        self.field_population["condition_occurrence"]["condition_end_date"] = FieldStats(
            end_date_count, total
        )
        self.field_population["condition_occurrence"]["condition_source_value"] = FieldStats(
            source_value_count, total
        )
        self.field_population["condition_occurrence"]["visit_occurrence_id"] = FieldStats(
            visit_id_count, total
        )

    def _calculate_drug_fields(self, records: list) -> None:
        """Calculate field population rates for drug_exposure."""
        if not records:
            return
        self.field_population["drug_exposure"] = {}
        total = len(records)

        concept_id_count = sum(1 for r in records if r.drug_concept_id > 0)
        quantity_count = sum(1 for r in records if r.quantity is not None)
        route_count = sum(
            1 for r in records if r.route_concept_id is not None and r.route_concept_id > 0
        )
        source_value_count = sum(1 for r in records if r.drug_source_value)

        self.field_population["drug_exposure"]["drug_concept_id (>0)"] = FieldStats(
            concept_id_count, total
        )
        self.field_population["drug_exposure"]["quantity"] = FieldStats(quantity_count, total)
        self.field_population["drug_exposure"]["route_concept_id (>0)"] = FieldStats(
            route_count, total
        )
        self.field_population["drug_exposure"]["drug_source_value"] = FieldStats(
            source_value_count, total
        )

    def _calculate_procedure_fields(self, records: list) -> None:
        """Calculate field population rates for procedure_occurrence."""
        if not records:
            return
        self.field_population["procedure_occurrence"] = {}
        total = len(records)

        concept_id_count = sum(1 for r in records if r.procedure_concept_id > 0)
        source_value_count = sum(1 for r in records if r.procedure_source_value)
        visit_id_count = sum(1 for r in records if r.visit_occurrence_id is not None)

        self.field_population["procedure_occurrence"]["procedure_concept_id (>0)"] = FieldStats(
            concept_id_count, total
        )
        self.field_population["procedure_occurrence"]["procedure_source_value"] = FieldStats(
            source_value_count, total
        )
        self.field_population["procedure_occurrence"]["visit_occurrence_id"] = FieldStats(
            visit_id_count, total
        )

    def _calculate_measurement_fields(self, records: list) -> None:
        """Calculate field population rates for measurement."""
        if not records:
            return
        self.field_population["measurement"] = {}
        total = len(records)

        concept_id_count = sum(1 for r in records if r.measurement_concept_id > 0)
        value_num_count = sum(1 for r in records if r.value_as_number is not None)
        value_concept_count = sum(
            1 for r in records if r.value_as_concept_id is not None and r.value_as_concept_id > 0
        )
        unit_concept_count = sum(
            1 for r in records if r.unit_concept_id is not None and r.unit_concept_id > 0
        )
        range_count = sum(
            1 for r in records if r.range_low is not None or r.range_high is not None
        )
        source_value_count = sum(1 for r in records if r.measurement_source_value)

        self.field_population["measurement"]["measurement_concept_id (>0)"] = FieldStats(
            concept_id_count, total
        )
        self.field_population["measurement"]["value_as_number"] = FieldStats(
            value_num_count, total
        )
        self.field_population["measurement"]["value_as_concept_id (>0)"] = FieldStats(
            value_concept_count, total
        )
        self.field_population["measurement"]["unit_concept_id (>0)"] = FieldStats(
            unit_concept_count, total
        )
        self.field_population["measurement"]["range_low/high"] = FieldStats(range_count, total)
        self.field_population["measurement"]["measurement_source_value"] = FieldStats(
            source_value_count, total
        )

    def _calculate_observation_fields(self, records: list) -> None:
        """Calculate field population rates for observation."""
        if not records:
            return
        self.field_population["observation"] = {}
        total = len(records)

        concept_id_count = sum(1 for r in records if r.observation_concept_id > 0)
        value_num_count = sum(1 for r in records if r.value_as_number is not None)
        value_string_count = sum(1 for r in records if r.value_as_string)
        value_concept_count = sum(
            1 for r in records if r.value_as_concept_id is not None and r.value_as_concept_id > 0
        )
        source_value_count = sum(1 for r in records if r.observation_source_value)

        self.field_population["observation"]["observation_concept_id (>0)"] = FieldStats(
            concept_id_count, total
        )
        self.field_population["observation"]["value_as_number"] = FieldStats(
            value_num_count, total
        )
        self.field_population["observation"]["value_as_string"] = FieldStats(
            value_string_count, total
        )
        self.field_population["observation"]["value_as_concept_id (>0)"] = FieldStats(
            value_concept_count, total
        )
        self.field_population["observation"]["observation_source_value"] = FieldStats(
            source_value_count, total
        )

    def _calculate_device_fields(self, records: list) -> None:
        """Calculate field population rates for device_exposure."""
        if not records:
            return
        self.field_population["device_exposure"] = {}
        total = len(records)

        concept_id_count = sum(1 for r in records if r.device_concept_id > 0)
        source_value_count = sum(1 for r in records if r.device_source_value)
        unique_id_count = sum(1 for r in records if r.unique_device_id)

        self.field_population["device_exposure"]["device_concept_id (>0)"] = FieldStats(
            concept_id_count, total
        )
        self.field_population["device_exposure"]["device_source_value"] = FieldStats(
            source_value_count, total
        )
        self.field_population["device_exposure"]["unique_device_id"] = FieldStats(
            unique_id_count, total
        )

    def write_text(self, w: TextIO) -> None:
        """Write the report in human-readable text format."""
        w.write("# CCDA-to-OMOP Conversion Report\n\n")

        # Document summary
        w.write("## Document Summary\n\n")
        w.write("| Metric | Value |\n")
        w.write("|--------|-------|\n")
        w.write(f"| Documents Processed | {self.documents_processed} |\n")
        w.write(f"| Documents with Errors | {self.documents_with_errors} |\n")
        if self.documents_processed > 0:
            success_rate = (
                (self.documents_processed - self.documents_with_errors)
                / self.documents_processed
                * 100
            )
            w.write(f"| Success Rate | {success_rate:.1f}% |\n")
        w.write("\n")

        # Records by table
        w.write("## Records Created by OMOP Table\n\n")
        w.write("| Table | Records |\n")
        w.write("|-------|--------:|\n")
        tables = [
            "person",
            "visit_occurrence",
            "condition_occurrence",
            "drug_exposure",
            "procedure_occurrence",
            "measurement",
            "observation",
            "device_exposure",
        ]
        total_records = 0
        for table in tables:
            count = self.records_by_table.get(table, 0)
            total_records += count
            w.write(f"| {table} | {count} |\n")
        w.write(f"| **Total** | **{total_records}** |\n")
        w.write("\n")

        # Section to table mapping
        if self.entries_by_section:
            w.write("## CCDA Section to OMOP Table Mapping\n\n")
            w.write("| Section | Records | Target Tables |\n")
            w.write("|---------|--------:|---------------|\n")

            for section in sorted(self.entries_by_section.keys()):
                metrics = self.entries_by_section[section]
                target_str = _format_target_tables(metrics.target_tables)
                w.write(f"| {section} | {metrics.records_created} | {target_str} |\n")
            w.write("\n")

        # Field population rates
        if self.field_population:
            w.write("## Field Population Rates\n\n")

            for table in tables:
                fields = self.field_population.get(table, {})
                if not fields:
                    continue

                w.write(f"### {table}\n\n")
                w.write("| Field | Populated | Total | Rate |\n")
                w.write("|-------|----------:|------:|-----:|\n")

                for name in sorted(fields.keys()):
                    stats = fields[name]
                    rate = (
                        stats.populated / stats.total * 100 if stats.total > 0 else 0
                    )
                    w.write(f"| {name} | {stats.populated} | {stats.total} | {rate:.1f}% |\n")
                w.write("\n")

        # Concept mapping quality
        if self.concept_mappings:
            w.write("## Concept Mapping Quality\n\n")
            w.write("| Vocabulary | Codes Seen | Mapped Standard | Source Only | Rate |\n")
            w.write("|------------|----------:|-----------------:|------------:|-----:|\n")

            for vocab in sorted(self.concept_mappings.keys()):
                stats = self.concept_mappings[vocab]
                rate = (
                    stats.mapped_standard / stats.codes_seen * 100
                    if stats.codes_seen > 0
                    else 0
                )
                w.write(
                    f"| {vocab} | {stats.codes_seen} | {stats.mapped_standard} | "
                    f"{stats.source_only} | {rate:.1f}% |\n"
                )
            w.write("\n")

        # Domain routing
        if self.domain_routing:
            w.write("## Domain Routing\n\n")
            w.write("Records moved to different tables based on OMOP concept domain:\n\n")
            w.write("| Source Section | Original Target | Actual Target | Count | Reason |\n")
            w.write("|----------------|-----------------|---------------|------:|--------|\n")

            for route in self.domain_routing:
                w.write(
                    f"| {route.source_section} | {route.original_target} | "
                    f"{route.actual_target} | {route.count} | {route.reason} |\n"
                )
            w.write("\n")

        # Skip reasons
        if self.skipped_entries:
            w.write("## Skipped Entries\n\n")
            w.write("| Reason | Count |\n")
            w.write("|--------|------:|\n")

            for reason in sorted(self.skipped_entries.keys()):
                w.write(f"| {reason} | {self.skipped_entries[reason]} |\n")
            w.write("\n")

    def write_json(self, w: TextIO) -> None:
        """Write the report in JSON format."""
        data = {
            "documents_processed": self.documents_processed,
            "documents_with_errors": self.documents_with_errors,
            "entries_by_section": {
                k: {
                    "entries_found": v.entries_found,
                    "records_created": v.records_created,
                    "skipped": v.skipped,
                    "target_tables": v.target_tables,
                }
                for k, v in self.entries_by_section.items()
            },
            "records_by_table": self.records_by_table,
            "field_population": {
                table: {field: {"populated": s.populated, "total": s.total} for field, s in fields.items()}
                for table, fields in self.field_population.items()
            },
            "concept_mappings": {
                k: {
                    "codes_seen": v.codes_seen,
                    "mapped_standard": v.mapped_standard,
                    "source_only": v.source_only,
                }
                for k, v in self.concept_mappings.items()
            },
            "domain_routing": [
                {
                    "source_section": r.source_section,
                    "original_target": r.original_target,
                    "actual_target": r.actual_target,
                    "count": r.count,
                    "reason": r.reason,
                }
                for r in self.domain_routing
            ],
            "skipped_entries": self.skipped_entries,
        }
        json.dump(data, w, indent=2)


def _extract_section_from_rule(rule: str) -> str:
    """Extract section from MappingRule format: 'RuleMapper:section_to_table'."""
    if not rule.startswith("RuleMapper:"):
        return ""
    parts = rule.removeprefix("RuleMapper:").split("_to_")
    return parts[0] if parts else ""


def _format_target_tables(tables: dict[str, int]) -> str:
    """Format target tables for display."""
    if not tables:
        return "-"
    parts = [f"{table}({count})" for table, count in sorted(tables.items())]
    return ", ".join(parts)
