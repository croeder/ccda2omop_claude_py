# Copyright 2025 Christophe Roeder. All rights reserved.

"""Tests for rule execution engine."""

import pytest
from lxml import etree

from ccda2omop.mapper.rule_engine import RuleEngine
from ccda2omop.mapper.rules import Condition, FieldMapping, MappingRule, SourceSpec, TargetSpec
from ccda2omop.mapper.vocabulary import VocabularyMapper


class TestRuleEngine:
    """Tests for RuleEngine class."""

    def test_init(self):
        """Test creating a RuleEngine."""
        vocab = VocabularyMapper()
        engine = RuleEngine(vocab)
        assert engine is not None
        assert engine.vocab is vocab
        assert engine.verbose is False

    def test_init_verbose(self):
        """Test creating a RuleEngine with verbose mode."""
        vocab = VocabularyMapper()
        engine = RuleEngine(vocab, verbose=True)
        assert engine.verbose is True


class TestMapEntry:
    """Tests for map_entry method."""

    @pytest.fixture
    def vocab(self):
        """Create a vocabulary mapper."""
        return VocabularyMapper()

    @pytest.fixture
    def engine(self, vocab):
        """Create a rule engine."""
        return RuleEngine(vocab)

    @pytest.fixture
    def simple_rule(self):
        """Create a simple mapping rule."""
        return MappingRule(
            name="test_rule",
            source=SourceSpec(
                section="Problems",
                entry_type="Act",
            ),
            target=TargetSpec(
                table="condition_occurrence",
                type_concept_id=32817,
            ),
            fields=[
                FieldMapping(
                    target="condition_source_value",
                    xpath="code/@displayName",
                    transform="string",
                ),
            ],
        )

    def test_map_entry_excluded_by_mood_code(self, engine, simple_rule):
        """Test that entries with non-EVN moodCode are excluded."""
        xml = etree.fromstring('<act moodCode="INT"><code displayName="Test"/></act>')
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert result == []

    def test_map_entry_excluded_by_status_code(self, engine, simple_rule):
        """Test that entries with cancelled status are excluded."""
        xml = etree.fromstring(
            '<act moodCode="EVN"><statusCode code="cancelled"/><code displayName="Test"/></act>'
        )
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert result == []

    def test_map_entry_evn_mood_code(self, engine, simple_rule):
        """Test that entries with EVN moodCode are included."""
        xml = etree.fromstring(
            '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Test Condition"/></act>'
        )
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert len(result) == 1
        assert result[0]["condition_source_value"] == "Test Condition"

    def test_map_entry_generates_id(self, engine, simple_rule):
        """Test that map_entry generates an ID."""
        xml = etree.fromstring(
            '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Test"/></act>'
        )
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert len(result) == 1
        assert "condition_occurrence_id" in result[0]
        assert isinstance(result[0]["condition_occurrence_id"], int)

    def test_map_entry_includes_person_id(self, engine, simple_rule):
        """Test that map_entry includes person_id."""
        xml = etree.fromstring(
            '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Test"/></act>'
        )
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert len(result) == 1
        assert result[0]["person_id"] == 12345

    def test_map_entry_includes_type_concept_id(self, engine, simple_rule):
        """Test that map_entry includes type_concept_id."""
        xml = etree.fromstring(
            '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Test"/></act>'
        )
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert len(result) == 1
        assert result[0]["condition_type_concept_id"] == 32817

    def test_map_entry_includes_mapping_rule(self, engine, simple_rule):
        """Test that map_entry includes mapping_rule field."""
        xml = etree.fromstring(
            '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Test"/></act>'
        )
        result = engine.map_entry(simple_rule, xml, 12345, {})
        assert len(result) == 1
        assert result[0]["mapping_rule"] == "RuleMapper:test_rule"


class TestMapEntries:
    """Tests for map_entries method."""

    @pytest.fixture
    def engine(self):
        """Create a rule engine."""
        return RuleEngine(VocabularyMapper())

    @pytest.fixture
    def simple_rule(self):
        """Create a simple mapping rule."""
        return MappingRule(
            name="test_rule",
            source=SourceSpec(section="Problems"),
            target=TargetSpec(table="condition_occurrence", type_concept_id=32817),
            fields=[
                FieldMapping(
                    target="condition_source_value",
                    xpath="code/@displayName",
                    transform="string",
                ),
            ],
        )

    def test_map_entries_empty_list(self, engine, simple_rule):
        """Test mapping empty entry list."""
        result = engine.map_entries(simple_rule, [], 12345, {})
        assert result == []

    def test_map_entries_multiple(self, engine, simple_rule):
        """Test mapping multiple entries."""
        entries = [
            etree.fromstring(
                '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Condition 1"/></act>'
            ),
            etree.fromstring(
                '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Condition 2"/></act>'
            ),
        ]
        result = engine.map_entries(simple_rule, entries, 12345, {})
        assert len(result) == 2
        values = [r["condition_source_value"] for r in result]
        assert "Condition 1" in values
        assert "Condition 2" in values

    def test_map_entries_filters_excluded(self, engine, simple_rule):
        """Test that excluded entries are filtered out."""
        entries = [
            etree.fromstring(
                '<act moodCode="EVN"><statusCode code="completed"/><code displayName="Included"/></act>'
            ),
            etree.fromstring(
                '<act moodCode="INT"><code displayName="Excluded"/></act>'
            ),
        ]
        result = engine.map_entries(simple_rule, entries, 12345, {})
        assert len(result) == 1
        assert result[0]["condition_source_value"] == "Included"


class TestCheckConditions:
    """Tests for _check_conditions method."""

    @pytest.fixture
    def engine(self):
        """Create a rule engine."""
        return RuleEngine(VocabularyMapper())

    def test_check_conditions_empty(self, engine):
        """Test checking empty conditions returns True."""
        xml = etree.fromstring("<act/>")
        result = engine._check_conditions([], xml, 12345)
        assert result is True

    def test_check_domain_equals_no_vocab(self, engine):
        """Test domain_equals condition without vocab data."""
        conditions = [Condition(type="domain_equals", value="Condition")]
        xml = etree.fromstring("<act/>")
        # Without vocab data, domain will be empty, so condition fails
        result = engine._check_conditions(conditions, xml, 12345)
        assert result is False

    def test_check_domain_not_equals_no_vocab(self, engine):
        """Test domain_not_equals condition without vocab data."""
        conditions = [Condition(type="domain_not_equals", value="Condition")]
        xml = etree.fromstring("<act/>")
        # Without vocab data, domain is empty, which is not equal to "Condition"
        result = engine._check_conditions(conditions, xml, 12345)
        assert result is True


class TestExtractFieldValue:
    """Tests for _extract_field_value method."""

    @pytest.fixture
    def engine(self):
        """Create a rule engine."""
        return RuleEngine(VocabularyMapper())

    def test_extract_vocab_transform(self, engine):
        """Test vocab transform returns concept_id directly."""
        fm = FieldMapping(target="concept_id", transform="vocab")
        xml = etree.fromstring("<act/>")
        result = engine._extract_field_value(xml, fm, 12345, {})
        assert result == 12345

    def test_extract_string_transform(self, engine):
        """Test string transform extracts text value."""
        fm = FieldMapping(
            target="source_value", xpath="code/@displayName", transform="string"
        )
        xml = etree.fromstring('<act><code displayName="Test Value"/></act>')
        result = engine._extract_field_value(xml, fm, 0, {})
        assert result == "Test Value"

    def test_extract_float_transform(self, engine):
        """Test float transform extracts numeric value."""
        fm = FieldMapping(target="value", xpath="value/@value", transform="float")
        xml = etree.fromstring('<act><value value="98.6"/></act>')
        result = engine._extract_field_value(xml, fm, 0, {})
        assert result == 98.6

    def test_extract_int_transform(self, engine):
        """Test int transform extracts integer value."""
        fm = FieldMapping(target="quantity", xpath="repeatNumber/@value", transform="int")
        xml = etree.fromstring('<act><repeatNumber value="30"/></act>')
        result = engine._extract_field_value(xml, fm, 0, {})
        assert result == 30


class TestExtractXpathValue:
    """Tests for _extract_xpath_value method."""

    @pytest.fixture
    def engine(self):
        """Create a rule engine."""
        return RuleEngine(VocabularyMapper())

    def test_extract_attribute_value(self, engine):
        """Test extracting attribute value."""
        xml = etree.fromstring('<act><code value="12345"/></act>')
        result = engine._extract_xpath_value(xml, "code/@value")
        assert result == "12345"

    def test_extract_text_value(self, engine):
        """Test extracting text content."""
        xml = etree.fromstring("<act><text>Hello World</text></act>")
        result = engine._extract_xpath_value(xml, "text")
        assert result == "Hello World"

    def test_extract_with_fallback(self, engine):
        """Test fallback xpath is used when primary fails."""
        xml = etree.fromstring('<act><fallback value="fallback_value"/></act>')
        result = engine._extract_xpath_value(xml, "primary/@value", "fallback/@value")
        assert result == "fallback_value"

    def test_extract_empty_xpath(self, engine):
        """Test empty xpath returns empty string."""
        xml = etree.fromstring("<act/>")
        result = engine._extract_xpath_value(xml, "")
        assert result == ""

    def test_extract_empty_xpath_with_fallback(self, engine):
        """Test empty xpath uses fallback."""
        xml = etree.fromstring('<act><fallback value="fallback_value"/></act>')
        result = engine._extract_xpath_value(xml, "", "fallback/@value")
        assert result == "fallback_value"

    def test_extract_no_match(self, engine):
        """Test no match returns empty string."""
        xml = etree.fromstring("<act/>")
        result = engine._extract_xpath_value(xml, "missing/@value")
        assert result == ""
