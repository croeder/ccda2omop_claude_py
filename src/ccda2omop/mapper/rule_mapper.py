# Copyright 2025 Christophe Roeder. All rights reserved.

"""High-level rule-based mapper for C-CDA to OMOP conversion."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

from lxml import etree

from ..ccda.models import Document, Encounter, Patient
from ..omop import ids as omop_ids
from ..omop.models import (
    ConditionOccurrence,
    DeviceExposure,
    DrugExposure,
    Measurement,
    Observation,
    OMOPData,
    Person,
    ProcedureOccurrence,
    VisitOccurrence,
)
from .rule_engine import RuleEngine
from .rule_loader import index_rules_by_section, load_rules_from_yaml
from .rules import MappingRule
from .vocab_loader import VocabLoader
from .vocabulary import CONCEPT_EHR_ENCOUNTER, VocabularyMapper

logger = logging.getLogger(__name__)


class RuleBasedMapper:
    """Uses declarative rules to transform C-CDA documents to OMOP."""

    def __init__(
        self,
        vocab: VocabularyMapper,
        rules: list[MappingRule],
        verbose: bool = False,
    ):
        self.engine = RuleEngine(vocab, verbose)
        self.rules_by_section = index_rules_by_section(rules)
        self.verbose = verbose

    @classmethod
    def from_vocab_loader(
        cls,
        loader: VocabLoader,
        rules: list[MappingRule],
        verbose: bool = False,
    ) -> "RuleBasedMapper":
        """Create a mapper with a vocabulary loader."""
        vocab = VocabularyMapper(vocab_loader=loader)
        return cls(vocab, rules, verbose)

    @classmethod
    def from_yaml(
        cls,
        rules_path: Union[str, Path],
        vocab: VocabularyMapper,
        verbose: bool = False,
    ) -> "RuleBasedMapper":
        """Create a mapper with rules loaded from YAML."""
        rules = load_rules_from_yaml(rules_path)
        return cls(vocab, rules, verbose)

    @classmethod
    def from_yaml_with_loader(
        cls,
        rules_path: Union[str, Path],
        loader: VocabLoader,
        verbose: bool = False,
    ) -> "RuleBasedMapper":
        """Create a mapper with YAML rules and vocab loader."""
        vocab = VocabularyMapper(vocab_loader=loader)
        rules = load_rules_from_yaml(rules_path)
        return cls(vocab, rules, verbose)

    def map_document(self, doc: Document) -> OMOPData:
        """Transform a C-CDA document to OMOP data using rules."""
        data = OMOPData()

        # Generate person ID
        person_id = omop_ids.generate_person_id(doc.patient.id, "CCDA")

        # Map patient (direct mapping - person is special)
        person = self._map_person(doc.patient, person_id)
        data.persons.append(person)

        # Map encounters (direct - visits are special)
        visit_map: dict[str, int] = {}
        for enc in doc.encounters:
            visit = self._map_encounter(enc, person_id)
            visit_map[enc.id] = visit.visit_occurrence_id
            data.visit_occurrences.append(visit)
        if self.verbose:
            logger.info(f"Mapped {len(doc.encounters)} encounters")

        # Map problems using rules with conditional filtering
        problem_rules = self._get_rules_by_section("Problems")
        if problem_rules:
            condition_count = 0
            observation_count = 0
            for rule in problem_rules:
                results = self._map_with_rule_or_xpath(
                    rule, doc.problems, doc.xml_root, person_id, visit_map, doc.section_meta
                )
                for r in results:
                    if rule.target.table == "condition_occurrence":
                        data.condition_occurrences.append(self._to_condition_occurrence(r))
                        condition_count += 1
                    elif rule.target.table == "observation":
                        data.observations.append(self._to_observation(r))
                        observation_count += 1
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.problems)} problems: {condition_count} to condition, "
                    f"{observation_count} to observation (conditional)"
                )

        # Map medications using rules
        if rule := self._get_rule_by_section("Medications"):
            drugs = self._map_with_rule_or_xpath(
                rule, doc.medications, doc.xml_root, person_id, visit_map, doc.section_meta
            )
            for d in drugs:
                data.drug_exposures.append(self._to_drug_exposure(d))
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.medications)} medications to {len(drugs)} drug records (rule-based)"
                )

        # Map immunizations using rules
        if rule := self._get_rule_by_section("Immunizations"):
            imms = self._map_with_rule_or_xpath(
                rule, doc.immunizations, doc.xml_root, person_id, visit_map, doc.section_meta
            )
            for d in imms:
                data.drug_exposures.append(self._to_drug_exposure(d))
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.immunizations)} immunizations to {len(imms)} drug records (rule-based)"
                )

        # Map procedures using rules with conditional filtering
        procedure_rules = self._get_rules_by_section("Procedures")
        if procedure_rules:
            procedure_count = 0
            measurement_count = 0
            observation_count = 0
            for rule in procedure_rules:
                results = self._map_with_rule_or_xpath(
                    rule, doc.procedures, doc.xml_root, person_id, visit_map, doc.section_meta
                )
                for r in results:
                    if rule.target.table == "procedure_occurrence":
                        data.procedure_occurrences.append(self._to_procedure_occurrence(r))
                        procedure_count += 1
                    elif rule.target.table == "measurement":
                        data.measurements.append(self._to_measurement(r))
                        measurement_count += 1
                    elif rule.target.table == "observation":
                        data.observations.append(self._to_observation(r))
                        observation_count += 1
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.procedures)} procedures: {procedure_count} to procedure, "
                    f"{measurement_count} to measurement, {observation_count} to observation (conditional)"
                )

        # Map vital signs using rules with conditional filtering
        vital_rules = self._get_rules_by_section("VitalSigns")
        if vital_rules:
            measurement_count = 0
            observation_count = 0
            for rule in vital_rules:
                results = self._map_with_rule_or_xpath(
                    rule, doc.vital_signs, doc.xml_root, person_id, visit_map, doc.section_meta
                )
                for r in results:
                    if rule.target.table == "measurement":
                        data.measurements.append(self._to_measurement(r))
                        measurement_count += 1
                    elif rule.target.table == "observation":
                        data.observations.append(self._to_observation(r))
                        observation_count += 1
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.vital_signs)} vital signs: {measurement_count} to measurement, "
                    f"{observation_count} to observation (conditional)"
                )

        # Map lab results using rules with conditional filtering
        lab_rules = self._get_rules_by_section("LabResults")
        if lab_rules:
            measurement_count = 0
            observation_count = 0
            for rule in lab_rules:
                results = self._map_with_rule_or_xpath(
                    rule, doc.lab_results, doc.xml_root, person_id, visit_map, doc.section_meta
                )
                for r in results:
                    if rule.target.table == "measurement":
                        data.measurements.append(self._to_measurement(r))
                        measurement_count += 1
                    elif rule.target.table == "observation":
                        data.observations.append(self._to_observation(r))
                        observation_count += 1
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.lab_results)} lab results: {measurement_count} to measurement, "
                    f"{observation_count} to observation (conditional)"
                )

        # Map allergies using rules with conditional filtering
        allergy_rules = self._get_rules_by_section("Allergies")
        if allergy_rules:
            observation_count = 0
            condition_count = 0
            for rule in allergy_rules:
                results = self._map_with_rule_or_xpath(
                    rule, doc.allergies, doc.xml_root, person_id, visit_map, doc.section_meta
                )
                for r in results:
                    if rule.target.table == "observation":
                        data.observations.append(self._to_observation(r))
                        observation_count += 1
                    elif rule.target.table == "condition_occurrence":
                        data.condition_occurrences.append(self._to_condition_occurrence(r))
                        condition_count += 1
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.allergies)} allergies: {observation_count} to observation, "
                    f"{condition_count} to condition (conditional)"
                )

        # Map social observations using rules with conditional filtering
        social_rules = self._get_rules_by_section("Observations")
        if social_rules:
            observation_count = 0
            measurement_count = 0
            condition_count = 0
            for rule in social_rules:
                results = self._map_with_rule_or_xpath(
                    rule, doc.observations, doc.xml_root, person_id, visit_map, doc.section_meta
                )
                for r in results:
                    if rule.target.table == "observation":
                        data.observations.append(self._to_observation(r))
                        observation_count += 1
                    elif rule.target.table == "measurement":
                        data.measurements.append(self._to_measurement(r))
                        measurement_count += 1
                    elif rule.target.table == "condition_occurrence":
                        data.condition_occurrences.append(self._to_condition_occurrence(r))
                        condition_count += 1
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.observations)} social observations: {observation_count} to observation, "
                    f"{measurement_count} to measurement, {condition_count} to condition (conditional)"
                )

        # Map devices using rules
        if rule := self._get_rule_by_section("Devices"):
            devices = self._map_with_rule_or_xpath(
                rule, doc.devices, doc.xml_root, person_id, visit_map, doc.section_meta
            )
            for d in devices:
                data.device_exposures.append(self._to_device_exposure(d))
            if self.verbose:
                logger.info(
                    f"Mapped {len(doc.devices)} devices to {len(devices)} device records (rule-based)"
                )

        return data

    def _get_rule_by_section(self, section: str) -> Optional[MappingRule]:
        """Return first rule by section name from the loaded rules."""
        rules = self.rules_by_section.get(section, [])
        return rules[0] if rules else None

    def _get_rules_by_section(self, section: str) -> list[MappingRule]:
        """Return all rules matching a section name."""
        return self.rules_by_section.get(section, [])

    def _rule_uses_xpath(self, rule: MappingRule) -> bool:
        """Check if a rule uses the xpath format."""
        for fm in rule.fields:
            if fm.xpath:
                return True
        return False

    def _map_with_rule_or_xpath(
        self,
        rule: MappingRule,
        entries: list,
        xml_root: Optional[etree._Element],
        person_id: int,
        visit_map: dict[str, int],
        section_meta: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Map entries using xpath when available, otherwise use typed struct mapping."""
        if self._rule_uses_xpath(rule) and xml_root is not None:
            return self._map_with_xpath(rule, xml_root, person_id, visit_map, section_meta)
        return self._map_with_rule_and_meta(rule, entries, person_id, visit_map, section_meta)

    def _map_with_rule_and_meta(
        self,
        rule: MappingRule,
        entries: list,
        person_id: int,
        visit_map: dict[str, int],
        section_meta: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Apply a rule to entries, using section metadata for optionality."""
        # Check if entries are required for this section
        entries_required = True
        if rule.source.section in section_meta:
            meta = section_meta[rule.source.section]
            entries_required = meta.entries_required

        # Convert entries to XML nodes if needed (they may already be lxml elements)
        xml_entries = []
        for entry in entries:
            if isinstance(entry, etree._Element):
                xml_entries.append(entry)
            # If not XML, we'd need different handling - skip for now
            # The Go version handles typed structs differently

        return self.engine.map_entries(rule, xml_entries, person_id, visit_map, entries_required)

    def _map_with_xpath(
        self,
        rule: MappingRule,
        xml_root: etree._Element,
        person_id: int,
        visit_map: dict[str, int],
        section_meta: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract entries from XML using xpath and map them using the rule."""
        if xml_root is None:
            return []

        # Find the section by template OID
        section = None
        sections = xml_root.xpath("//component/section")
        for s in sections:
            templates = s.xpath("templateId")
            for t in templates:
                root = t.get("root", "")
                if root == rule.source.section_oid or root == rule.source.section_oid_entries_required:
                    section = s
                    break
            if section is not None:
                break

        if section is None:
            return []  # Section not found

        # Check if entries are required
        entries_required = True
        if rule.source.section in section_meta:
            meta = section_meta[rule.source.section]
            entries_required = meta.entries_required

        # Extract entries using the rule's entry xpath
        entries = section.xpath(rule.source.entry_xpath)
        if not entries:
            return []

        # Map each entry using xpath extraction
        results = []
        for entry in entries:
            mapped = self.engine.map_entry(rule, entry, person_id, visit_map, entries_required)
            results.extend(mapped)

        return results

    # Person and Encounter mapping (kept as direct mapping since they're special)

    def _map_person(self, p: Patient, person_id: int) -> Person:
        """Map a C-CDA patient to an OMOP person."""
        person = Person(
            person_id=person_id,
            gender_concept_id=self.engine.vocab.map_gender(p.gender.code),
            year_of_birth=p.birth_time.year if p.birth_time else 1900,
            race_concept_id=self.engine.vocab.map_race(p.race.code),
            ethnicity_concept_id=self.engine.vocab.map_ethnicity(p.ethnicity.code),
            person_source_value=p.id,
            gender_source_value=p.gender.display_name,
            race_source_value=p.race.display_name,
            ethnicity_source_value=p.ethnicity.display_name,
            mapping_rule="RuleMapper:Person",
        )

        if p.birth_time:
            person.month_of_birth = p.birth_time.month
            person.day_of_birth = p.birth_time.day
            person.birth_datetime = p.birth_time

        return person

    def _map_encounter(self, enc: Encounter, person_id: int) -> VisitOccurrence:
        """Map a C-CDA encounter to an OMOP visit occurrence."""
        visit_id = omop_ids.generate_visit_id(person_id, enc.id)

        start_date = enc.effective_time.low
        if not start_date:
            start_date = enc.effective_time.value

        end_date = enc.effective_time.high
        if not end_date:
            end_date = start_date

        return VisitOccurrence(
            visit_occurrence_id=visit_id,
            person_id=person_id,
            visit_concept_id=self.engine.vocab.map_visit_type(enc.code.code),
            visit_start_date=start_date or datetime.min,
            visit_start_datetime=start_date,
            visit_end_date=end_date or datetime.min,
            visit_end_datetime=end_date,
            visit_type_concept_id=CONCEPT_EHR_ENCOUNTER,
            visit_source_value=enc.code.display_name,
            mapping_rule="RuleMapper:Encounter",
        )

    # Conversion functions from dict to OMOP dataclasses

    def _to_condition_occurrence(self, record: dict[str, Any]) -> ConditionOccurrence:
        """Convert a record dict to a ConditionOccurrence."""
        return ConditionOccurrence(
            condition_occurrence_id=_get_int(record, "condition_occurrence_id"),
            person_id=_get_int(record, "person_id"),
            condition_concept_id=_get_int(record, "condition_concept_id"),
            condition_start_date=_get_datetime(record, "condition_start_date") or datetime.min,
            condition_start_datetime=_get_datetime(record, "condition_start_datetime"),
            condition_end_date=_get_datetime(record, "condition_end_date"),
            condition_end_datetime=_get_datetime(record, "condition_end_datetime"),
            condition_type_concept_id=_get_int(record, "condition_type_concept_id"),
            condition_source_value=_get_str(record, "condition_source_value"),
            mapping_rule=_get_str(record, "mapping_rule"),
        )

    def _to_drug_exposure(self, record: dict[str, Any]) -> DrugExposure:
        """Convert a record dict to a DrugExposure."""
        return DrugExposure(
            drug_exposure_id=_get_int(record, "drug_exposure_id"),
            person_id=_get_int(record, "person_id"),
            drug_concept_id=_get_int(record, "drug_concept_id"),
            drug_exposure_start_date=_get_datetime(record, "drug_exposure_start_date") or datetime.min,
            drug_exposure_start_datetime=_get_datetime(record, "drug_exposure_start_datetime"),
            drug_exposure_end_date=_get_datetime(record, "drug_exposure_end_date") or datetime.min,
            drug_exposure_end_datetime=_get_datetime(record, "drug_exposure_end_datetime"),
            drug_type_concept_id=_get_int(record, "drug_type_concept_id"),
            quantity=_get_float(record, "quantity"),
            days_supply=_get_int_opt(record, "days_supply"),
            refills=_get_int_opt(record, "refills"),
            route_concept_id=_get_int_opt(record, "route_concept_id"),
            drug_source_value=_get_str(record, "drug_source_value"),
            route_source_value=_get_str(record, "route_source_value"),
            lot_number=_get_str(record, "lot_number"),
            sig=_get_str(record, "sig"),
            dose_unit_source_value=_get_str(record, "dose_unit_source_value"),
            mapping_rule=_get_str(record, "mapping_rule"),
        )

    def _to_procedure_occurrence(self, record: dict[str, Any]) -> ProcedureOccurrence:
        """Convert a record dict to a ProcedureOccurrence."""
        return ProcedureOccurrence(
            procedure_occurrence_id=_get_int(record, "procedure_occurrence_id"),
            person_id=_get_int(record, "person_id"),
            procedure_concept_id=_get_int(record, "procedure_concept_id"),
            procedure_date=_get_datetime(record, "procedure_date") or datetime.min,
            procedure_datetime=_get_datetime(record, "procedure_datetime"),
            procedure_type_concept_id=_get_int(record, "procedure_type_concept_id"),
            procedure_source_value=_get_str(record, "procedure_source_value"),
            modifier_source_value=_get_str(record, "modifier_source_value"),
            mapping_rule=_get_str(record, "mapping_rule"),
        )

    def _to_measurement(self, record: dict[str, Any]) -> Measurement:
        """Convert a record dict to a Measurement."""
        return Measurement(
            measurement_id=_get_int(record, "measurement_id"),
            person_id=_get_int(record, "person_id"),
            measurement_concept_id=_get_int(record, "measurement_concept_id"),
            measurement_date=_get_datetime(record, "measurement_date") or datetime.min,
            measurement_datetime=_get_datetime(record, "measurement_datetime"),
            measurement_type_concept_id=_get_int(record, "measurement_type_concept_id"),
            value_as_number=_get_float(record, "value_as_number"),
            value_as_concept_id=_get_int_opt(record, "value_as_concept_id"),
            unit_concept_id=_get_int_opt(record, "unit_concept_id"),
            range_low=_get_float(record, "range_low"),
            range_high=_get_float(record, "range_high"),
            measurement_source_value=_get_str(record, "measurement_source_value"),
            unit_source_value=_get_str(record, "unit_source_value"),
            value_source_value=_get_str(record, "value_source_value"),
            mapping_rule=_get_str(record, "mapping_rule"),
        )

    def _to_observation(self, record: dict[str, Any]) -> Observation:
        """Convert a record dict to an Observation."""
        return Observation(
            observation_id=_get_int(record, "observation_id"),
            person_id=_get_int(record, "person_id"),
            observation_concept_id=_get_int(record, "observation_concept_id"),
            observation_date=_get_datetime(record, "observation_date") or datetime.min,
            observation_datetime=_get_datetime(record, "observation_datetime"),
            observation_type_concept_id=_get_int(record, "observation_type_concept_id"),
            value_as_number=_get_float(record, "value_as_number"),
            value_as_string=_get_str(record, "value_as_string"),
            value_as_concept_id=_get_int_opt(record, "value_as_concept_id"),
            qualifier_source_value=_get_str(record, "qualifier_source_value"),
            unit_source_value=_get_str(record, "unit_source_value"),
            observation_source_value=_get_str(record, "observation_source_value"),
            mapping_rule=_get_str(record, "mapping_rule"),
        )

    def _to_device_exposure(self, record: dict[str, Any]) -> DeviceExposure:
        """Convert a record dict to a DeviceExposure."""
        return DeviceExposure(
            device_exposure_id=_get_int(record, "device_exposure_id"),
            person_id=_get_int(record, "person_id"),
            device_concept_id=_get_int(record, "device_concept_id"),
            device_exposure_start_date=_get_datetime(record, "device_exposure_start_date") or datetime.min,
            device_exposure_start_datetime=_get_datetime(record, "device_exposure_start_datetime"),
            device_exposure_end_date=_get_datetime(record, "device_exposure_end_date"),
            device_exposure_end_datetime=_get_datetime(record, "device_exposure_end_datetime"),
            device_type_concept_id=_get_int(record, "device_type_concept_id"),
            unique_device_id=_get_str(record, "unique_device_id"),
            device_source_value=_get_str(record, "device_source_value"),
            mapping_rule=_get_str(record, "mapping_rule"),
        )


# Helper functions for extracting values from dicts


def _get_int(m: dict[str, Any], key: str) -> int:
    """Extract an integer value from a dict."""
    v = m.get(key)
    if v is None:
        return 0
    if isinstance(v, (int, float)):
        return int(v)
    return 0


def _get_int_opt(m: dict[str, Any], key: str) -> Optional[int]:
    """Extract an optional integer value from a dict."""
    v = m.get(key)
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    return None


def _get_str(m: dict[str, Any], key: str) -> str:
    """Extract a string value from a dict."""
    v = m.get(key)
    if v is None:
        return ""
    return str(v)


def _get_float(m: dict[str, Any], key: str) -> Optional[float]:
    """Extract a float value from a dict."""
    v = m.get(key)
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None


def _get_datetime(m: dict[str, Any], key: str) -> Optional[datetime]:
    """Extract a datetime value from a dict."""
    v = m.get(key)
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    return None
