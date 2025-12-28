# Copyright 2025 Christophe Roeder. All rights reserved.

"""Rule execution engine for C-CDA to OMOP mapping."""

from datetime import datetime
from typing import Any, Optional

from lxml import etree

from ..omop import ids as omop_ids
from . import extractor
from .rules import FieldMapping, MappingRule
from .transforms import format_source_value, get_transform
from .vocabulary import CONCEPT_NO_MAPPING, VocabularyMapper, oid_to_vocabulary_id


class RuleEngine:
    """Executes mapping rules to transform C-CDA data to OMOP."""

    def __init__(
        self,
        vocab: VocabularyMapper,
        verbose: bool = False,
    ):
        self.vocab = vocab
        self.verbose = verbose

    def map_entries(
        self,
        rule: MappingRule,
        entries: list[etree._Element],
        person_id: int,
        visit_map: dict[str, int],
        entries_required: bool = True,
    ) -> list[dict[str, Any]]:
        """Map a list of XML entries using a rule."""
        results = []
        for entry in entries:
            mapped = self.map_entry(
                rule, entry, person_id, visit_map, entries_required
            )
            results.extend(mapped)
        return results

    def map_entry(
        self,
        rule: MappingRule,
        entry: etree._Element,
        person_id: int,
        visit_map: dict[str, int],
        entries_required: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Map a single entry, potentially returning multiple records.

        Some entries map to multiple OMOP records when a single source code
        maps to multiple standard concepts.
        """
        # Check if entry should be included
        if not extractor.should_include_entry(entry):
            return []

        # Get concept IDs (may be multiple for multi-mapping)
        concept_ids = self._extract_concept_ids(rule, entry, entries_required)
        if not concept_ids:
            # Try to get at least concept_id=0 if entries aren't required
            if not entries_required:
                concept_ids = [0]
            else:
                return []

        # Check conditions
        if rule.source.conditions:
            if not self._check_conditions(
                rule.source.conditions, entry, concept_ids[0]
            ):
                return []

        # Generate base ID
        base_id = self._generate_id(rule, entry, person_id)

        # Create a record for each concept ID
        results = []
        for i, concept_id in enumerate(concept_ids):
            record = self._create_record(
                rule,
                entry,
                person_id,
                base_id + i,
                concept_id,
                visit_map,
                entries_required,
            )
            if record:
                results.append(record)

        return results

    def _extract_concept_ids(
        self,
        rule: MappingRule,
        entry: etree._Element,
        entries_required: bool,
    ) -> list[int]:
        """Extract concept IDs from the entry using the vocab transform field."""
        # Find the vocab field
        for fm in rule.fields:
            if fm.transform == "vocab":
                code = self._extract_xpath_value(entry, fm.xpath, fm.fallback_xpath)
                if not code:
                    continue

                code_system = ""
                if fm.vocab_xpath:
                    result = entry.xpath(fm.vocab_xpath)
                    if result:
                        code_system = (
                            str(result[0])
                            if not isinstance(result[0], etree._Element)
                            else result[0].text or ""
                        )

                # Map to concept IDs
                vocab_id = oid_to_vocabulary_id(code_system)
                if vocab_id and self.vocab.vocab_loader:
                    ids = self.vocab.vocab_loader.get_standard_concept_ids(
                        vocab_id, code
                    )
                    if ids:
                        return ids

                # If no mapping found, return 0 if entries not required
                if not entries_required:
                    return [0]

        return []

    def _check_conditions(
        self,
        conditions: list,
        entry: etree._Element,
        concept_id: int,
    ) -> bool:
        """Check if all conditions are met."""
        for cond in conditions:
            if cond.type == "domain_equals":
                domain = self.vocab.get_concept_domain(concept_id)
                if domain != cond.value:
                    return False
            elif cond.type == "domain_not_equals":
                domain = self.vocab.get_concept_domain(concept_id)
                if domain == cond.value:
                    return False
            # Add more condition types as needed

        return True

    def _generate_id(
        self,
        rule: MappingRule,
        entry: etree._Element,
        person_id: int,
    ) -> int:
        """Generate a deterministic ID for the record."""
        values = [str(person_id)]

        # Extract base field values for ID generation
        for field_path in rule.id_gen.base_fields:
            # Convert field path to xpath (simplified)
            if "." in field_path:
                parts = field_path.split(".")
                xpath = "/".join(parts[:-1]).lower() + "/@" + parts[-1].lower()
            else:
                xpath = f"{field_path.lower()}/@value"

            result = entry.xpath(xpath)
            if result:
                values.append(str(result[0]))

        # Use appropriate generator based on target table
        generator = rule.id_gen.generator or rule.target.table
        return omop_ids.generate_id(generator, *values)

    def _create_record(
        self,
        rule: MappingRule,
        entry: etree._Element,
        person_id: int,
        record_id: int,
        concept_id: int,
        visit_map: dict[str, int],
        entries_required: bool,
    ) -> Optional[dict[str, Any]]:
        """Create an OMOP record dict from the entry."""
        # Get ID field name based on table
        id_field = f"{rule.target.table}_id"
        type_field = f"{rule.target.table.split('_')[0]}_type_concept_id"

        record: dict[str, Any] = {
            id_field: record_id,
            "person_id": person_id,
            type_field: rule.target.type_concept_id,
        }

        for fm in rule.fields:
            is_optional = fm.optional or not entries_required

            try:
                value = self._extract_field_value(
                    entry, fm, concept_id, visit_map
                )
                if value is not None:
                    record[fm.target] = value
                elif not is_optional:
                    return None
            except Exception:
                if not is_optional:
                    return None

        record["mapping_rule"] = f"RuleMapper:{rule.name}"
        return record

    def _extract_field_value(
        self,
        entry: etree._Element,
        fm: FieldMapping,
        concept_id: int,
        visit_map: dict[str, int],
    ) -> Any:
        """Extract and transform a field value from the entry."""
        # Handle vocab transform specially
        if fm.transform == "vocab":
            return concept_id

        # Extract raw value
        raw = self._extract_xpath_value(entry, fm.xpath, fm.fallback_xpath)

        # Apply transform
        transform = get_transform(fm.transform)

        if fm.transform == "date":
            dt = extractor.extract_time(entry, fm.xpath)
            return transform(dt)
        elif fm.transform == "time_ptr":
            dt = extractor.extract_time(entry, fm.xpath)
            return transform(dt)
        elif fm.transform == "float":
            return transform(raw)
        elif fm.transform == "int":
            return transform(raw)
        elif fm.transform == "unit":
            return self.vocab.map_unit_code(raw) if raw else None
        elif fm.transform == "route":
            code_system = ""
            if fm.vocab_xpath:
                result = entry.xpath(fm.vocab_xpath)
                if result:
                    code_system = str(result[0])
            return self.vocab.map_route_code(raw, code_system) if raw else None
        elif fm.transform == "value_vocab":
            code_system = ""
            if fm.vocab_xpath:
                result = entry.xpath(fm.vocab_xpath)
                if result:
                    code_system = str(result[0])
            return (
                self.vocab.map_observation_value_code(raw, code_system)
                if raw
                else None
            )
        elif fm.transform == "format_source":
            # Extract display name too
            display = ""
            if fm.fallback_xpath:
                result = entry.xpath(fm.fallback_xpath)
                if result:
                    display = str(result[0])
            return format_source_value(raw, display)
        else:
            return transform(raw)

    def _extract_xpath_value(
        self,
        entry: etree._Element,
        xpath: str,
        fallback_xpath: str = "",
    ) -> str:
        """Extract a string value using XPath with optional fallback."""
        if not xpath:
            if fallback_xpath:
                result = entry.xpath(fallback_xpath)
                if result:
                    return (
                        str(result[0])
                        if not isinstance(result[0], etree._Element)
                        else result[0].text or ""
                    )
            return ""

        result = entry.xpath(xpath)
        if result:
            return (
                str(result[0])
                if not isinstance(result[0], etree._Element)
                else result[0].text or ""
            )

        if fallback_xpath:
            result = entry.xpath(fallback_xpath)
            if result:
                return (
                    str(result[0])
                    if not isinstance(result[0], etree._Element)
                    else result[0].text or ""
                )

        return ""
