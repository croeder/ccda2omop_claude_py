# Copyright 2025 Christophe Roeder. All rights reserved.

"""Code mapping analysis for C-CDA files."""

import csv
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, TextIO

from lxml import etree

from ..mapper.vocab_loader import VocabLoader
from ..mapper.vocabulary import oid_to_vocabulary_id


@dataclass
class CodeMapping:
    """Represents a single code found in C-CDA and its OMOP mapping."""

    section: str = ""
    xpath: str = ""
    source_code: str = ""
    source_code_system: str = ""
    source_vocabulary: str = ""
    source_display_name: str = ""
    omop_concept_id: int = 0
    omop_concept_name: str = ""
    omop_domain_id: str = ""
    omop_vocabulary_id: str = ""
    is_standard: bool = False
    mapping_status: str = ""  # "mapped", "unmapped", "no_vocab"


@dataclass
class SectionXPath:
    """Defines the XPath and code extraction for a C-CDA section."""

    name: str
    root_xpath: str
    code_paths: list["CodePath"] = field(default_factory=list)


@dataclass
class CodePath:
    """Defines how to extract a code from within an entry."""

    name: str  # Description of this code location
    code_xpath: str  # XPath to the code element relative to entry
    code_attr: str = "code"  # Attribute containing the code
    code_system_attr: str = "codeSystem"  # Attribute containing the code system OID
    display_attr: str = "displayName"  # Attribute containing display name


# Standard C-CDA section definitions
SECTION_DEFINITIONS = [
    SectionXPath(
        name="Problems",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.5.1']/entry/act/entryRelationship/observation",
        code_paths=[
            CodePath(name="Problem Code", code_xpath="value"),
        ],
    ),
    SectionXPath(
        name="Medications",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.1.1']/entry/substanceAdministration",
        code_paths=[
            CodePath(
                name="Medication Code",
                code_xpath="consumable/manufacturedProduct/manufacturedMaterial/code",
            ),
            CodePath(name="Route Code", code_xpath="routeCode"),
        ],
    ),
    SectionXPath(
        name="Immunizations",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.2.1']/entry/substanceAdministration",
        code_paths=[
            CodePath(
                name="Vaccine Code",
                code_xpath="consumable/manufacturedProduct/manufacturedMaterial/code",
            ),
        ],
    ),
    SectionXPath(
        name="Procedures",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.7.1']/entry/procedure",
        code_paths=[
            CodePath(name="Procedure Code", code_xpath="code"),
        ],
    ),
    SectionXPath(
        name="VitalSigns",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.4.1']/entry/organizer/component/observation",
        code_paths=[
            CodePath(name="Vital Sign Code", code_xpath="code"),
        ],
    ),
    SectionXPath(
        name="LabResults",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.3.1']/entry/organizer/component/observation",
        code_paths=[
            CodePath(name="Lab Code", code_xpath="code"),
        ],
    ),
    SectionXPath(
        name="Allergies",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.6.1']/entry/act/entryRelationship/observation",
        code_paths=[
            CodePath(
                name="Allergy Code",
                code_xpath="participant/participantRole/playingEntity/code",
            ),
            CodePath(
                name="Reaction Code",
                code_xpath="entryRelationship/observation[templateId/@root='2.16.840.1.113883.10.20.22.4.9']/value",
            ),
        ],
    ),
    SectionXPath(
        name="SocialHistory",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.17']/entry/observation",
        code_paths=[
            CodePath(name="Social Observation Code", code_xpath="code"),
        ],
    ),
    SectionXPath(
        name="MedicalEquipment",
        root_xpath="//component/section[templateId/@root='2.16.840.1.113883.10.20.22.2.23']/entry",
        code_paths=[
            CodePath(
                name="Device Code",
                code_xpath=".//participant/participantRole/playingDevice/code",
            ),
        ],
    ),
]


class Analyzer:
    """Extracts codes from C-CDA files and maps them to OMOP concepts."""

    def __init__(self, vocab_loader: Optional[VocabLoader] = None, verbose: bool = False):
        self.vocab_loader = vocab_loader
        self.verbose = verbose

    def analyze_file(self, filepath: str) -> list[CodeMapping]:
        """Analyze a C-CDA file and return all code mappings."""
        tree = etree.parse(filepath)
        root = tree.getroot()
        return self._analyze_root(root)

    def analyze_string(self, xml_string: str) -> list[CodeMapping]:
        """Analyze a C-CDA XML string and return all code mappings."""
        root = etree.fromstring(xml_string.encode())
        return self._analyze_root(root)

    def _analyze_root(self, root: etree._Element) -> list[CodeMapping]:
        """Analyze an XML root element and return all code mappings."""
        mappings = []

        for section in SECTION_DEFINITIONS:
            entries = root.xpath(section.root_xpath)
            for entry in entries:
                for code_path in section.code_paths:
                    # Find code elements within this entry
                    if not code_path.code_xpath or code_path.code_xpath == ".":
                        code_nodes = [entry]
                    else:
                        code_nodes = entry.xpath(code_path.code_xpath)

                    for code_node in code_nodes:
                        code = code_node.get(code_path.code_attr, "")
                        if not code:
                            continue

                        code_system = code_node.get(code_path.code_system_attr, "")
                        display_name = code_node.get(code_path.display_attr, "")

                        # Build XPath for this code
                        xpath = section.root_xpath
                        if code_path.code_xpath and code_path.code_xpath != ".":
                            xpath = f"{xpath}/{code_path.code_xpath}"

                        mapping = self._map_code(
                            section.name, xpath, code, code_system, display_name
                        )
                        mappings.append(mapping)

        return mappings

    def _map_code(
        self,
        section: str,
        xpath: str,
        code: str,
        code_system: str,
        display_name: str,
    ) -> CodeMapping:
        """Map a single code to OMOP concepts."""
        mapping = CodeMapping(
            section=section,
            xpath=xpath,
            source_code=code,
            source_code_system=code_system,
            source_display_name=display_name,
        )

        # Convert OID to vocabulary ID
        vocab_id = oid_to_vocabulary_id(code_system)
        mapping.source_vocabulary = vocab_id

        if not vocab_id:
            mapping.mapping_status = "no_vocab"
            return mapping

        if self.vocab_loader is None:
            mapping.mapping_status = "no_vocab_loader"
            return mapping

        # Look up the source concept
        source_concept = self.vocab_loader.lookup_concept(vocab_id, code)
        if source_concept is None:
            mapping.mapping_status = "unmapped"
            return mapping

        # Get standard concept mappings
        standard_ids = self.vocab_loader.get_standard_concept_ids(vocab_id, code)
        if not standard_ids:
            mapping.mapping_status = "unmapped"
            mapping.omop_concept_id = source_concept.concept_id
            mapping.omop_concept_name = source_concept.concept_name
            mapping.omop_domain_id = source_concept.domain_id
            mapping.omop_vocabulary_id = source_concept.vocabulary_id
            return mapping

        # Use the first standard concept
        standard_concept = self.vocab_loader.lookup_concept_by_id(standard_ids[0])
        if standard_concept:
            mapping.omop_concept_id = standard_concept.concept_id
            mapping.omop_concept_name = standard_concept.concept_name
            mapping.omop_domain_id = standard_concept.domain_id
            mapping.omop_vocabulary_id = standard_concept.vocabulary_id
            mapping.is_standard = standard_concept.standard_concept == "S"
            mapping.mapping_status = "mapped"

            # Note if there are multiple mappings
            if len(standard_ids) > 1:
                mapping.mapping_status = f"mapped ({len(standard_ids)} targets)"
        else:
            mapping.mapping_status = "unmapped"

        return mapping

    def write_csv(self, mappings: list[CodeMapping], writer: TextIO) -> None:
        """Write the mappings to a CSV file."""
        csv_writer = csv.writer(writer)

        # Write header
        header = [
            "Section",
            "XPath",
            "Source_Code",
            "Source_CodeSystem_OID",
            "Source_Vocabulary",
            "Source_DisplayName",
            "OMOP_Concept_ID",
            "OMOP_Concept_Name",
            "OMOP_Domain_ID",
            "OMOP_Vocabulary_ID",
            "Is_Standard",
            "Mapping_Status",
        ]
        csv_writer.writerow(header)

        # Write rows
        for m in mappings:
            row = [
                m.section,
                m.xpath,
                m.source_code,
                m.source_code_system,
                m.source_vocabulary,
                m.source_display_name,
                str(m.omop_concept_id),
                m.omop_concept_name,
                m.omop_domain_id,
                m.omop_vocabulary_id,
                str(m.is_standard).lower(),
                m.mapping_status,
            ]
            csv_writer.writerow(row)

    def print_summary(self, mappings: list[CodeMapping], writer: TextIO) -> None:
        """Print a summary of the analysis to the writer."""
        # Count by section and mapping status
        section_counts: dict[str, int] = {}
        status_counts: dict[str, int] = {}
        domain_counts: dict[str, int] = {}

        for m in mappings:
            section_counts[m.section] = section_counts.get(m.section, 0) + 1
            status_counts[m.mapping_status] = status_counts.get(m.mapping_status, 0) + 1
            if m.omop_domain_id:
                domain_counts[m.omop_domain_id] = domain_counts.get(m.omop_domain_id, 0) + 1

        writer.write("\n=== Analysis Summary ===\n\n")
        writer.write(f"Total codes found: {len(mappings)}\n\n")

        writer.write("By Section:\n")
        for section, count in sorted(section_counts.items()):
            writer.write(f"  {section:<20} {count}\n")

        writer.write("\nBy Mapping Status:\n")
        for status, count in sorted(status_counts.items()):
            writer.write(f"  {status:<20} {count}\n")

        writer.write("\nBy OMOP Domain:\n")
        for domain, count in sorted(domain_counts.items()):
            writer.write(f"  {domain:<20} {count}\n")

        # Show unmapped codes
        writer.write("\n=== Unmapped Codes ===\n")
        for m in mappings:
            if m.mapping_status.startswith("unmapped") or m.mapping_status == "no_vocab":
                writer.write(
                    f"  [{m.section}] {m.source_code} ({m.source_vocabulary}) - {m.source_display_name}\n"
                )

    def write_mapping_summary(self, mappings: list[CodeMapping], writer: TextIO) -> None:
        """Write a summary showing C-CDA sections/paths and their OMOP table mappings."""
        # Group by section and extract code path from XPath
        section_paths: dict[str, "SectionMapping"] = {}

        for m in mappings:
            path_key = _extract_code_path(m.xpath)
            key = f"{m.section}|{path_key}"

            if key not in section_paths:
                section_paths[key] = SectionMapping(
                    section=m.section,
                    code_path=path_key,
                )

            sm = section_paths[key]
            sm.total_codes += 1
            if m.omop_domain_id:
                sm.mapped_codes += 1
                table = _domain_to_table(m.omop_domain_id)
                sm.omop_tables[table] = sm.omop_tables.get(table, 0) + 1

        # Print header
        writer.write("\n")
        writer.write("=" * 80 + "\n")
        writer.write("C-CDA to OMOP Mapping Summary\n")
        writer.write("=" * 80 + "\n\n")

        # Collect and sort sections
        section_map: dict[str, list["SectionMapping"]] = {}
        for sm in section_paths.values():
            if sm.section not in section_map:
                section_map[sm.section] = []
            section_map[sm.section].append(sm)

        # Print by section
        for section in sorted(section_map.keys()):
            paths = sorted(section_map[section], key=lambda x: x.code_path)

            # Calculate section totals
            section_total = sum(p.total_codes for p in paths)
            section_mapped = sum(p.mapped_codes for p in paths)
            section_tables: dict[str, int] = {}
            for p in paths:
                for table, count in p.omop_tables.items():
                    section_tables[table] = section_tables.get(table, 0) + count

            writer.write(f"C-CDA Section: {section}\n")
            writer.write(
                f"  Total codes: {section_total}, Mapped: {section_mapped} "
                f"({_percentage(section_mapped, section_total):.1f}%)\n"
            )

            # Show OMOP tables for this section
            writer.write("  OMOP Tables:\n")
            for table in sorted(section_tables.keys()):
                count = section_tables[table]
                writer.write(f"    → {table:<25} {count} codes\n")

            # Show code paths within section
            writer.write("  Code Paths:\n")
            for p in paths:
                tables = sorted(p.omop_tables.keys())
                table_str = ", ".join(tables) if tables else "(no mapping)"
                writer.write(f"    {p.code_path:<40} → {table_str} ({p.total_codes} codes)\n")
            writer.write("\n")

        # Overall summary
        writer.write("=" * 80 + "\n")
        writer.write("Overall Summary\n")
        writer.write("=" * 80 + "\n\n")

        total_codes = sum(sm.total_codes for sm in section_paths.values())
        mapped_codes = sum(sm.mapped_codes for sm in section_paths.values())
        all_tables: dict[str, int] = {}
        for sm in section_paths.values():
            for table, count in sm.omop_tables.items():
                all_tables[table] = all_tables.get(table, 0) + count

        writer.write(f"Total C-CDA codes analyzed: {total_codes}\n")
        writer.write(
            f"Successfully mapped: {mapped_codes} ({_percentage(mapped_codes, total_codes):.1f}%)\n"
        )
        writer.write(
            f"Unmapped: {total_codes - mapped_codes} "
            f"({_percentage(total_codes - mapped_codes, total_codes):.1f}%)\n\n"
        )

        writer.write("OMOP CDM Tables populated:\n")
        for table in sorted(all_tables.keys()):
            count = all_tables[table]
            writer.write(f"  {table:<30} {count} records\n")


@dataclass
class SectionMapping:
    """Tracks the mapping from a C-CDA section/path to OMOP tables."""

    section: str = ""
    code_path: str = ""
    total_codes: int = 0
    mapped_codes: int = 0
    omop_tables: dict[str, int] = field(default_factory=dict)


def _domain_to_table(domain_id: str) -> str:
    """Map OMOP domain_id to the primary CDM table."""
    domain_map = {
        "Condition": "condition_occurrence",
        "Drug": "drug_exposure",
        "Procedure": "procedure_occurrence",
        "Measurement": "measurement",
        "Observation": "observation",
        "Device": "device_exposure",
        "Visit": "visit_occurrence",
        "Specimen": "specimen",
        "Note": "note",
    }
    return domain_map.get(domain_id, domain_id if domain_id else "(unmapped)")


def _extract_code_path(xpath: str) -> str:
    """Extract a simplified code path from a full XPath."""
    parts = xpath.split("/")
    code_parts = []
    found_entry = False

    for part in parts:
        if not part:
            continue
        # Look for entry-level elements
        if any(
            part.startswith(p)
            for p in [
                "observation[",
                "substanceAdministration[",
                "procedure[",
                "act[",
                "organizer[",
            ]
        ):
            found_entry = True
            continue
        if found_entry:
            # Remove index suffixes for cleaner display
            clean_part = part
            if "[" in part:
                clean_part = part[: part.index("[")]
            code_parts.append(clean_part)

    return "/".join(code_parts) if code_parts else "(root)"


def _percentage(part: int, total: int) -> float:
    """Calculate percentage safely."""
    if total == 0:
        return 0.0
    return float(part) / float(total) * 100.0
