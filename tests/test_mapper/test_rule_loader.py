# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for YAML rule loader."""

import tempfile
from pathlib import Path

import pytest

from ccda2omop.mapper.rule_loader import (
    get_rule_by_name,
    get_rule_by_section,
    index_rules_by_section,
    load_rules_from_yaml,
)
from ccda2omop.mapper.rules import MappingRule


class TestLoadRulesFromYaml:
    """Tests for load_rules_from_yaml function."""

    def test_load_single_rule_file(self):
        """Test loading a single rule from a YAML file."""
        yaml_content = """
name: test_rule
source:
  section: Problems
  entry_type: Act
target:
  table: condition_occurrence
  type_concept_id: 32817
fields:
  - target: condition_concept_id
    xpath: "code/@code"
    transform: vocab
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert len(rules) == 1
            assert rules[0].name == "test_rule"
            assert rules[0].source.section == "Problems"
            assert rules[0].target.table == "condition_occurrence"
            assert rules[0].target.type_concept_id == 32817
            assert len(rules[0].fields) == 1
        finally:
            filepath.unlink()

    def test_load_multi_rule_file(self):
        """Test loading multiple rules from a YAML file with 'rules' key."""
        yaml_content = """
rules:
  - name: rule_one
    source:
      section: Problems
    target:
      table: condition_occurrence
    fields: []
  - name: rule_two
    source:
      section: Medications
    target:
      table: drug_exposure
    fields: []
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert len(rules) == 2
            assert rules[0].name == "rule_one"
            assert rules[1].name == "rule_two"
        finally:
            filepath.unlink()

    def test_load_rules_from_directory(self):
        """Test loading rules from a directory of YAML files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two rule files
            rule1 = Path(tmpdir) / "rule1.yaml"
            rule1.write_text(
                """
name: rule_one
source:
  section: Problems
target:
  table: condition_occurrence
fields: []
"""
            )

            rule2 = Path(tmpdir) / "rule2.yml"
            rule2.write_text(
                """
name: rule_two
source:
  section: Medications
target:
  table: drug_exposure
fields: []
"""
            )

            rules = load_rules_from_yaml(tmpdir)
            assert len(rules) == 2
            # Files should be loaded in sorted order
            names = [r.name for r in rules]
            assert "rule_one" in names
            assert "rule_two" in names

    def test_load_empty_file(self):
        """Test loading an empty YAML file returns empty list."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("")
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert rules == []
        finally:
            filepath.unlink()

    def test_load_file_without_name_or_rules(self):
        """Test loading file without 'name' or 'rules' key returns empty list."""
        yaml_content = """
some_other_key: value
another_key: 123
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert rules == []
        finally:
            filepath.unlink()

    def test_load_rule_with_conditions(self):
        """Test loading a rule with source conditions."""
        yaml_content = """
name: test_rule_with_conditions
source:
  section: Procedures
  conditions:
    - type: domain_equals
      value: Procedure
target:
  table: procedure_occurrence
fields: []
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert len(rules) == 1
            assert len(rules[0].source.conditions) == 1
            assert rules[0].source.conditions[0].type == "domain_equals"
            assert rules[0].source.conditions[0].value == "Procedure"
        finally:
            filepath.unlink()

    def test_load_rule_with_extractions(self):
        """Test loading a rule with source extractions."""
        yaml_content = """
name: test_rule_with_extractions
source:
  section: VitalSigns
  extraction:
    - field: value
      xpath: "value/@value"
      type: float
target:
  table: measurement
fields: []
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert len(rules) == 1
            assert len(rules[0].source.extraction) == 1
            assert rules[0].source.extraction[0].field == "value"
            assert rules[0].source.extraction[0].xpath == "value/@value"
        finally:
            filepath.unlink()

    def test_load_rule_with_id_gen(self):
        """Test loading a rule with ID generation spec."""
        yaml_content = """
name: test_rule_with_id_gen
source:
  section: Problems
target:
  table: condition_occurrence
id_gen:
  base_fields:
    - code.code
    - effectiveTime.low
  generator: condition
fields: []
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert len(rules) == 1
            assert rules[0].id_gen.base_fields == ["code.code", "effectiveTime.low"]
            assert rules[0].id_gen.generator == "condition"
        finally:
            filepath.unlink()

    def test_load_rule_with_field_options(self):
        """Test loading a rule with various field options."""
        yaml_content = """
name: test_rule_with_fields
source:
  section: Medications
target:
  table: drug_exposure
fields:
  - target: drug_concept_id
    xpath: "code/@code"
    fallback_xpath: "consumable/manufacturedProduct/manufacturedMaterial/code/@code"
    vocab_xpath: "code/@codeSystem"
    transform: vocab
    optional: false
    source: code
    vocab_field: concept_id
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()
            filepath = Path(f.name)

        try:
            rules = load_rules_from_yaml(filepath)
            assert len(rules) == 1
            field = rules[0].fields[0]
            assert field.target == "drug_concept_id"
            assert field.xpath == "code/@code"
            assert field.fallback_xpath.startswith("consumable/")
            assert field.vocab_xpath == "code/@codeSystem"
            assert field.transform == "vocab"
            assert field.optional is False
        finally:
            filepath.unlink()


class TestIndexRulesBySection:
    """Tests for index_rules_by_section function."""

    def test_index_empty_rules(self):
        """Test indexing empty rules list."""
        result = index_rules_by_section([])
        assert result == {}

    def test_index_single_rule(self):
        """Test indexing a single rule."""
        rule = MappingRule(name="test")
        rule.source.section = "Problems"
        result = index_rules_by_section([rule])
        assert "Problems" in result
        assert len(result["Problems"]) == 1

    def test_index_multiple_rules_same_section(self):
        """Test indexing multiple rules with same section."""
        rule1 = MappingRule(name="rule1")
        rule1.source.section = "Problems"
        rule2 = MappingRule(name="rule2")
        rule2.source.section = "Problems"

        result = index_rules_by_section([rule1, rule2])
        assert "Problems" in result
        assert len(result["Problems"]) == 2

    def test_index_multiple_sections(self):
        """Test indexing rules with different sections."""
        rule1 = MappingRule(name="rule1")
        rule1.source.section = "Problems"
        rule2 = MappingRule(name="rule2")
        rule2.source.section = "Medications"

        result = index_rules_by_section([rule1, rule2])
        assert "Problems" in result
        assert "Medications" in result
        assert len(result["Problems"]) == 1
        assert len(result["Medications"]) == 1


class TestGetRuleBySection:
    """Tests for get_rule_by_section function."""

    def test_get_existing_section(self):
        """Test getting a rule by existing section name."""
        rule = MappingRule(name="test_rule")
        rule.source.section = "Problems"

        result = get_rule_by_section([rule], "Problems")
        assert result is not None
        assert result.name == "test_rule"

    def test_get_nonexistent_section(self):
        """Test getting a rule by nonexistent section returns None."""
        rule = MappingRule(name="test_rule")
        rule.source.section = "Problems"

        result = get_rule_by_section([rule], "Medications")
        assert result is None

    def test_get_from_empty_list(self):
        """Test getting a rule from empty list returns None."""
        result = get_rule_by_section([], "Problems")
        assert result is None


class TestGetRuleByName:
    """Tests for get_rule_by_name function."""

    def test_get_existing_name(self):
        """Test getting a rule by existing name."""
        rule = MappingRule(name="my_rule")

        result = get_rule_by_name([rule], "my_rule")
        assert result is not None
        assert result.name == "my_rule"

    def test_get_nonexistent_name(self):
        """Test getting a rule by nonexistent name returns None."""
        rule = MappingRule(name="my_rule")

        result = get_rule_by_name([rule], "other_rule")
        assert result is None

    def test_get_from_empty_list(self):
        """Test getting a rule from empty list returns None."""
        result = get_rule_by_name([], "my_rule")
        assert result is None
