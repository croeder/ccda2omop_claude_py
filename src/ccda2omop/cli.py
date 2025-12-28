# Copyright 2025 Christophe Roeder. All rights reserved.

"""Command-line interface for ccda2omop."""

import logging
import sys
from pathlib import Path

import click

from .analyzer import Analyzer
from .converter import Config, Converter
from .mapper.vocab_loader import VocabLoader


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )


def find_xml_files(directory: Path) -> list[str]:
    """Return a sorted list of XML files from a directory."""
    files = [str(f) for f in directory.iterdir() if f.suffix.lower() == ".xml" and f.is_file()]
    return sorted(files)


@click.command()
@click.option(
    "-i",
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to C-CDA XML file or directory of XML files",
)
@click.option(
    "-o",
    "--output",
    "output_dir",
    default="./output",
    type=click.Path(),
    help="Directory for OMOP CSV output files",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
@click.option(
    "--concept",
    "concept_file",
    type=click.Path(exists=True),
    help="Path to OMOP CONCEPT.csv vocabulary file",
)
@click.option(
    "--relationship",
    "relationship_file",
    type=click.Path(exists=True),
    help="Path to OMOP CONCEPT_RELATIONSHIP.csv file",
)
@click.option(
    "--rules-file",
    "rules_file",
    type=click.Path(exists=True),
    help="Path to custom YAML rules file or directory",
)
@click.option(
    "--analyze",
    "analyze_flag",
    is_flag=True,
    help="Analyze input file(s) and show code mappings (requires --concept)",
)
@click.option(
    "--analyze-output",
    "analyze_output",
    type=click.Path(),
    help="Output CSV file for analysis (default: stdout)",
)
@click.option(
    "--summary",
    is_flag=True,
    help="Show summary of C-CDA sections to OMOP table mappings (use with --analyze)",
)
@click.option(
    "--vocab-dir",
    "vocab_dir",
    type=click.Path(exists=True),
    help="Path to directory containing supplementary vocabulary CSV files",
)
@click.option("--report", "report_flag", is_flag=True, help="Generate conversion coverage report")
@click.option(
    "--report-output",
    "report_output",
    type=click.Path(),
    help="Output file for report (default: stdout). Use .json extension for JSON format",
)
def main(
    input_path: str,
    output_dir: str,
    verbose: bool,
    concept_file: str,
    relationship_file: str,
    rules_file: str,
    analyze_flag: bool,
    analyze_output: str,
    summary: bool,
    vocab_dir: str,
    report_flag: bool,
    report_output: str,
) -> None:
    """Convert C-CDA XML documents to OMOP CDM 5.3 CSV files.

    Examples:

    \b
    # Convert a single file
    ccda2omop -i patient.xml -o output/ --concept CONCEPT.csv

    \b
    # Convert a directory of files
    ccda2omop -i ./ccda_files/ -o output/ --concept CONCEPT.csv

    \b
    # Analyze codes in a file
    ccda2omop -i patient.xml --analyze --concept CONCEPT.csv

    \b
    # Generate conversion report
    ccda2omop -i patient.xml -o output/ --report --report-output report.md
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    input_path_obj = Path(input_path)

    # Collect XML files
    if input_path_obj.is_dir():
        xml_files = find_xml_files(input_path_obj)
        if not xml_files:
            click.echo(f"No XML files found in directory: {input_path}", err=True)
            sys.exit(1)
        if verbose:
            logger.info(f"Found {len(xml_files)} XML files in {input_path}")
    else:
        xml_files = [str(input_path_obj)]

    # Analyze mode
    if analyze_flag:
        try:
            run_analyze(
                xml_files,
                concept_file or "",
                relationship_file or "",
                vocab_dir or "",
                analyze_output or "",
                summary,
                verbose,
            )
        except Exception as e:
            click.echo(f"Analysis failed: {e}", err=True)
            sys.exit(1)
        return

    # Convert mode
    cfg = Config(
        output_dir=output_dir,
        verbose=verbose,
        concept_file=concept_file or "",
        relationship_file=relationship_file or "",
        vocab_dir=vocab_dir or "",
        rules_file=rules_file or "",
        generate_report=report_flag,
    )

    converter = Converter()
    try:
        stats = converter.run_batch(xml_files, cfg)
    except Exception as e:
        click.echo(f"Conversion failed: {e}", err=True)
        sys.exit(1)

    click.echo(
        f"Conversion complete. Processed {len(xml_files)} file(s). Output written to: {output_dir}"
    )
    click.echo(
        f"  {stats.persons} person, {stats.visit_occurrences} visit, "
        f"{stats.condition_occurrences} condition, {stats.drug_exposures} drug, "
        f"{stats.procedure_occurrences} procedure, {stats.measurements} measurement, "
        f"{stats.observations} observation, {stats.device_exposures} device"
    )

    # Output report if requested
    if report_flag and stats.report:
        try:
            write_report(stats.report, report_output or "")
        except Exception as e:
            click.echo(f"Failed to write report: {e}", err=True)
            sys.exit(1)


def run_analyze(
    input_files: list[str],
    concept_file: str,
    relationship_file: str,
    vocab_dir: str,
    output_file: str,
    show_summary: bool,
    verbose: bool,
) -> None:
    """Run code mapping analysis on input files."""
    logger = logging.getLogger(__name__)

    # Load vocabulary if provided
    vocab_loader = None
    if concept_file:
        if verbose:
            logger.info(f"Loading OMOP vocabulary from {concept_file}")
        vocab_loader = VocabLoader()
        vocab_loader.load_concepts(concept_file)

        if relationship_file:
            if verbose:
                logger.info(f"Loading concept relationships from {relationship_file}")
            vocab_loader.load_concept_relationships(relationship_file)

        # Load supplementary vocabularies
        if vocab_dir:
            load_supplementary_vocabs(vocab_loader, vocab_dir, verbose)

    # Create analyzer
    analyzer = Analyzer(vocab_loader, verbose)

    # Analyze all files and aggregate mappings
    all_mappings = []
    for i, input_file in enumerate(input_files):
        if verbose:
            logger.info(f"Analyzing file {i + 1}/{len(input_files)}: {input_file}")
        mappings = analyzer.analyze_file(input_file)
        all_mappings.extend(mappings)

    if verbose and len(input_files) > 1:
        logger.info(f"Aggregated {len(all_mappings)} mappings from {len(input_files)} files")

    # Summary mode
    if show_summary:
        analyzer.write_mapping_summary(all_mappings, sys.stdout)
        return

    # Output results
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            analyzer.write_csv(all_mappings, f)
        analyzer.print_summary(all_mappings, sys.stderr)
        click.echo(f"\nAnalysis written to: {output_file}", err=True)
    else:
        analyzer.write_csv(all_mappings, sys.stdout)


def load_supplementary_vocabs(vocab_loader: VocabLoader, vocab_dir: str, verbose: bool) -> None:
    """Load all CSV files from a directory as supplementary vocabularies."""
    logger = logging.getLogger(__name__)
    dir_path = Path(vocab_dir)

    for filepath in sorted(dir_path.iterdir()):
        if filepath.is_file() and filepath.suffix.lower() == ".csv":
            if verbose:
                logger.info(f"Loading supplementary vocabulary from {filepath}")
            vocab_loader.load_supplementary_vocab(str(filepath))


def write_report(report, output_file: str) -> None:
    """Write the conversion report to the specified output."""
    from .report import ConversionReport

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            # Use JSON format if file ends with .json
            if output_file.lower().endswith(".json"):
                report.write_json(f)
            else:
                report.write_text(f)
        click.echo(f"Report written to: {output_file}", err=True)
    else:
        report.write_text(sys.stdout)


if __name__ == "__main__":
    main()
