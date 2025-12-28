# Copyright 2025 Christophe Roeder. All rights reserved.

"""YAML rule file loader."""

from pathlib import Path
from typing import Any, Optional, Union

import yaml

from .rules import (
    Condition,
    Extraction,
    FieldMapping,
    IDGenSpec,
    MappingRule,
    SourceSpec,
    TargetSpec,
)


def load_rules_from_yaml(path: Union[str, Path]) -> list[MappingRule]:
    """
    Load mapping rules from a YAML file or directory.

    If path is a directory, loads all .yaml/.yml files from that directory.
    If path is a file, loads rules from that single file.

    Args:
        path: Path to YAML file or directory

    Returns:
        List of MappingRule objects
    """
    path = Path(path)

    if path.is_dir():
        return _load_rules_from_directory(path)
    return _load_rules_from_file(path)


def _load_rules_from_directory(dir_path: Path) -> list[MappingRule]:
    """Load all YAML rule files from a directory."""
    rules = []

    # Get and sort filenames for deterministic ordering
    yaml_files = sorted(
        f for f in dir_path.iterdir()
        if f.suffix in (".yaml", ".yml") and f.is_file()
    )

    for filepath in yaml_files:
        file_rules = _load_rules_from_file(filepath)
        rules.extend(file_rules)

    return rules


def _load_rules_from_file(filepath: Path) -> list[MappingRule]:
    """
    Load rules from a single YAML file.

    Supports both single-rule format (rule at top level) and
    multi-rule format (rules under "rules:" key).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return []

    # Try as single rule first (new format with "name" at top level)
    if "name" in data:
        return [_convert_yaml_rule(data)]

    # Try as multi-rule file (old format with "rules:" key)
    if "rules" in data:
        return [_convert_yaml_rule(r) for r in data["rules"]]

    return []


def _convert_yaml_rule(data: dict[str, Any]) -> MappingRule:
    """Convert a YAML dict to a MappingRule dataclass."""
    source_data = data.get("source", {})
    target_data = data.get("target", {})
    id_gen_data = data.get("id_gen", {})

    # Parse conditions
    conditions = [
        Condition(
            type=c.get("type", ""),
            field=c.get("field", ""),
            value=c.get("value", ""),
        )
        for c in source_data.get("conditions", [])
    ]

    # Parse extractions
    extractions = [
        Extraction(
            field=e.get("field", ""),
            xpath=e.get("xpath", ""),
            type=e.get("type", ""),
        )
        for e in source_data.get("extraction", [])
    ]

    # Parse fields
    fields = [
        FieldMapping(
            target=f.get("target", ""),
            xpath=f.get("xpath", ""),
            fallback_xpath=f.get("fallback_xpath", ""),
            vocab_xpath=f.get("vocab_xpath", ""),
            transform=f.get("transform", ""),
            optional=f.get("optional", False),
            source=f.get("source", ""),
            vocab_field=f.get("vocab_field", ""),
        )
        for f in data.get("fields", [])
    ]

    return MappingRule(
        name=data.get("name", ""),
        source=SourceSpec(
            section=source_data.get("section", ""),
            section_oid=source_data.get("section_oid", ""),
            section_oid_entries_required=source_data.get(
                "section_oid_entries_required", ""
            ),
            entry_xpath=source_data.get("entry_xpath", ""),
            entry_type=source_data.get("entry_type", ""),
            extraction=extractions,
            conditions=conditions,
        ),
        target=TargetSpec(
            table=target_data.get("table", ""),
            type_concept_id=target_data.get("type_concept_id", 0),
        ),
        fields=fields,
        id_gen=IDGenSpec(
            base_fields=id_gen_data.get("base_fields", []),
            generator=id_gen_data.get("generator", ""),
        ),
    )


def index_rules_by_section(rules: list[MappingRule]) -> dict[str, list[MappingRule]]:
    """Convert a list of rules to a dict keyed by section name."""
    result: dict[str, list[MappingRule]] = {}
    for rule in rules:
        section = rule.source.section
        if section not in result:
            result[section] = []
        result[section].append(rule)
    return result


def get_rule_by_section(rules: list[MappingRule], section: str) -> Optional[MappingRule]:
    """Get a rule by section name from a list of rules."""
    for rule in rules:
        if rule.source.section == section:
            return rule
    return None


def get_rule_by_name(rules: list[MappingRule], name: str) -> Optional[MappingRule]:
    """Get a rule by name from a list of rules."""
    for rule in rules:
        if rule.name == name:
            return rule
    return None
