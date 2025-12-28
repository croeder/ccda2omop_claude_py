# Copyright 2025 Christophe Roeder. All rights reserved.

"""Batch processing for C-CDA to OMOP conversion."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..ccda.parser import CCDAParser
from ..mapper.rule_loader import load_rules_from_yaml
from ..mapper.rule_mapper import RuleBasedMapper
from ..mapper.vocab_loader import VocabLoader
from ..mapper.vocabulary import VocabularyMapper
from ..omop.models import OMOPData
from ..omop.writer import CSVWriter
from ..report.report import ConversionReport

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration for C-CDA to OMOP conversion."""

    input_file: str = ""
    output_dir: str = ""
    verbose: bool = False
    concept_file: str = ""  # Path to CONCEPT.csv
    relationship_file: str = ""  # Path to CONCEPT_RELATIONSHIP.csv
    vocab_dir: str = ""  # Path to directory with supplementary vocabulary files
    rules_file: str = ""  # Path to YAML rules file (optional)
    generate_report: bool = False  # Generate conversion report


@dataclass
class ConversionSummary:
    """Counts of records created during conversion."""

    persons: int = 0
    visit_occurrences: int = 0
    condition_occurrences: int = 0
    drug_exposures: int = 0
    procedure_occurrences: int = 0
    measurements: int = 0
    observations: int = 0
    device_exposures: int = 0
    report: Optional[ConversionReport] = None


class Converter:
    """Orchestrates C-CDA to OMOP conversion."""

    def __init__(self):
        self._vocab_loader: Optional[VocabLoader] = None

    def load_vocabulary(
        self,
        concept_file: str,
        relationship_file: str = "",
        vocab_dir: str = "",
        verbose: bool = False,
    ) -> None:
        """Load vocabulary files and cache them for reuse."""
        if self._vocab_loader is not None:
            return  # Already loaded

        if not concept_file:
            return  # No vocabulary files specified

        if verbose:
            logger.info(f"Loading OMOP vocabulary from {concept_file}")

        self._vocab_loader = VocabLoader()
        self._vocab_loader.load_concepts(concept_file)

        if relationship_file:
            if verbose:
                logger.info(f"Loading concept relationships from {relationship_file}")
            self._vocab_loader.load_concept_relationships(relationship_file)

        # Load supplementary vocabularies from directory if provided
        if vocab_dir:
            self._load_supplementary_vocabs(vocab_dir, verbose)

    def _load_supplementary_vocabs(self, vocab_dir: str, verbose: bool) -> None:
        """Load all CSV files from a directory as supplementary vocabularies."""
        dir_path = Path(vocab_dir)
        if not dir_path.is_dir():
            raise ValueError(f"Vocab directory not found: {vocab_dir}")

        for filepath in sorted(dir_path.iterdir()):
            if filepath.is_file() and filepath.suffix.lower() == ".csv":
                if self._vocab_loader:
                    self._vocab_loader.load_supplementary_vocab(str(filepath))

    def run_batch(self, files: list[str], cfg: Config) -> ConversionSummary:
        """Process multiple C-CDA files and aggregate results into a single output."""
        # Load vocabulary if specified and not already loaded
        if cfg.concept_file and self._vocab_loader is None:
            self.load_vocabulary(
                cfg.concept_file, cfg.relationship_file, cfg.vocab_dir, cfg.verbose
            )

        # Create output directory if it doesn't exist
        output_path = Path(cfg.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Aggregate all OMOP data
        aggregated_data = OMOPData()

        # Initialize report if requested
        conv_report: Optional[ConversionReport] = None
        if cfg.generate_report:
            conv_report = ConversionReport()

        for i, input_file in enumerate(files):
            if cfg.verbose:
                logger.info(f"Processing file {i + 1}/{len(files)}: {input_file}")

            try:
                omop_data = self._process_file(input_file, cfg)
            except Exception as e:
                if conv_report:
                    conv_report.add_document(has_error=True)
                raise RuntimeError(f"Failed to process {input_file}: {e}") from e

            if conv_report:
                conv_report.add_document(has_error=False)

            # Set source file on all records
            source_file = Path(input_file).name
            self._set_source_file(omop_data, source_file)

            # Aggregate the data
            aggregated_data.persons.extend(omop_data.persons)
            aggregated_data.visit_occurrences.extend(omop_data.visit_occurrences)
            aggregated_data.condition_occurrences.extend(omop_data.condition_occurrences)
            aggregated_data.drug_exposures.extend(omop_data.drug_exposures)
            aggregated_data.procedure_occurrences.extend(omop_data.procedure_occurrences)
            aggregated_data.measurements.extend(omop_data.measurements)
            aggregated_data.observations.extend(omop_data.observations)
            aggregated_data.device_exposures.extend(omop_data.device_exposures)

        # Write aggregated OMOP CSV files
        writer = CSVWriter(cfg.output_dir)
        writer.write_all(aggregated_data)

        # Calculate report from aggregated data if requested
        if conv_report:
            conv_report.calculate_from_omop_data(aggregated_data)

        # Build summary
        summary = ConversionSummary(
            persons=len(aggregated_data.persons),
            visit_occurrences=len(aggregated_data.visit_occurrences),
            condition_occurrences=len(aggregated_data.condition_occurrences),
            drug_exposures=len(aggregated_data.drug_exposures),
            procedure_occurrences=len(aggregated_data.procedure_occurrences),
            measurements=len(aggregated_data.measurements),
            observations=len(aggregated_data.observations),
            device_exposures=len(aggregated_data.device_exposures),
            report=conv_report,
        )

        if cfg.verbose:
            logger.info(f"Wrote {summary.persons} person records")
            logger.info(f"Wrote {summary.visit_occurrences} visit_occurrence records")
            logger.info(f"Wrote {summary.condition_occurrences} condition_occurrence records")
            logger.info(f"Wrote {summary.drug_exposures} drug_exposure records")
            logger.info(f"Wrote {summary.procedure_occurrences} procedure_occurrence records")
            logger.info(f"Wrote {summary.measurements} measurement records")
            logger.info(f"Wrote {summary.observations} observation records")
            logger.info(f"Wrote {summary.device_exposures} device_exposure records")

        return summary

    def _process_file(self, input_file: str, cfg: Config) -> OMOPData:
        """Process a single C-CDA file and return OMOP data without writing."""
        if cfg.verbose:
            logger.info(f"Parsing C-CDA file: {input_file}")

        # Parse the C-CDA document
        parser = CCDAParser()
        doc = parser.parse_file(input_file)

        if cfg.verbose:
            logger.info(
                f"Successfully parsed C-CDA document for patient: "
                f"{doc.patient.name.given} {doc.patient.name.family}"
            )

        # Map C-CDA to OMOP using rule-based mapper
        if cfg.rules_file:
            # Load rules from YAML file
            if cfg.verbose:
                logger.info(f"Loading mapping rules from {cfg.rules_file}")
            rules = load_rules_from_yaml(cfg.rules_file)
            if self._vocab_loader:
                vocab = VocabularyMapper(vocab_loader=self._vocab_loader)
                rm = RuleBasedMapper(vocab, rules, cfg.verbose)
            else:
                rm = RuleBasedMapper(VocabularyMapper(), rules, cfg.verbose)
        else:
            # Use default rules (would need to be defined)
            rules = load_rules_from_yaml(
                Path(__file__).parent.parent.parent.parent / "rules"
            )
            if self._vocab_loader:
                vocab = VocabularyMapper(vocab_loader=self._vocab_loader)
                rm = RuleBasedMapper(vocab, rules, cfg.verbose)
            else:
                rm = RuleBasedMapper(VocabularyMapper(), rules, cfg.verbose)

        return rm.map_document(doc)

    def run(self, cfg: Config) -> None:
        """Process a single C-CDA file."""
        # Load vocabulary if specified and not already loaded
        if cfg.concept_file and self._vocab_loader is None:
            self.load_vocabulary(
                cfg.concept_file, cfg.relationship_file, cfg.vocab_dir, cfg.verbose
            )

        if cfg.verbose:
            logger.info(f"Parsing C-CDA file: {cfg.input_file}")

        # Parse the C-CDA document
        parser = CCDAParser()
        doc = parser.parse_file(cfg.input_file)

        if cfg.verbose:
            logger.info(
                f"Successfully parsed C-CDA document for patient: "
                f"{doc.patient.name.given} {doc.patient.name.family}"
            )

        # Create output directory if it doesn't exist
        output_path = Path(cfg.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Map C-CDA to OMOP using rule-based mapper
        if cfg.rules_file:
            if cfg.verbose:
                logger.info(f"Loading mapping rules from {cfg.rules_file}")
            rules = load_rules_from_yaml(cfg.rules_file)
            if self._vocab_loader:
                vocab = VocabularyMapper(vocab_loader=self._vocab_loader)
                rm = RuleBasedMapper(vocab, rules, cfg.verbose)
            else:
                rm = RuleBasedMapper(VocabularyMapper(), rules, cfg.verbose)
        else:
            rules = load_rules_from_yaml(
                Path(__file__).parent.parent.parent.parent / "rules"
            )
            if self._vocab_loader:
                vocab = VocabularyMapper(vocab_loader=self._vocab_loader)
                rm = RuleBasedMapper(vocab, rules, cfg.verbose)
            else:
                rm = RuleBasedMapper(VocabularyMapper(), rules, cfg.verbose)

        omop_data = rm.map_document(doc)

        # Set source file on all records
        source_file = Path(cfg.input_file).name
        self._set_source_file(omop_data, source_file)

        # Write OMOP CSV files
        writer = CSVWriter(cfg.output_dir)
        writer.write_all(omop_data)

        if cfg.verbose:
            logger.info(f"Wrote {len(omop_data.persons)} person records")
            logger.info(f"Wrote {len(omop_data.visit_occurrences)} visit_occurrence records")
            logger.info(f"Wrote {len(omop_data.condition_occurrences)} condition_occurrence records")
            logger.info(f"Wrote {len(omop_data.drug_exposures)} drug_exposure records")
            logger.info(f"Wrote {len(omop_data.procedure_occurrences)} procedure_occurrence records")
            logger.info(f"Wrote {len(omop_data.measurements)} measurement records")
            logger.info(f"Wrote {len(omop_data.observations)} observation records")
            logger.info(f"Wrote {len(omop_data.device_exposures)} device_exposure records")

    def _set_source_file(self, data: OMOPData, source_file: str) -> None:
        """Set the source_file field on all records in the OMOP data."""
        for person in data.persons:
            person.source_file = source_file
        for visit in data.visit_occurrences:
            visit.source_file = source_file
        for condition in data.condition_occurrences:
            condition.source_file = source_file
        for drug in data.drug_exposures:
            drug.source_file = source_file
        for procedure in data.procedure_occurrences:
            procedure.source_file = source_file
        for measurement in data.measurements:
            measurement.source_file = source_file
        for observation in data.observations:
            observation.source_file = source_file
        for device in data.device_exposures:
            device.source_file = source_file
