# ccda2omop

Convert C-CDA XML clinical documents to OMOP CDM 5.3 CSV files.

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Usage

### Convert C-CDA to OMOP

```bash
# Single file
ccda2omop convert -i patient.xml -o output/

# With vocabulary mapping
ccda2omop convert -i patient.xml -o output/ --concept CONCEPT.csv --relationship CONCEPT_RELATIONSHIP.csv

# Directory of files
ccda2omop convert -i ccda_files/ -o output/

# With custom rules
ccda2omop convert -i patient.xml -o output/ --rules-file rules/

# Generate conversion report
ccda2omop convert -i patient.xml -o output/ --report --report-output report.json
```

### Analyze Code Mappings

```bash
ccda2omop analyze -i patient.xml --concept CONCEPT.csv
ccda2omop analyze -i patient.xml --concept CONCEPT.csv --summary
ccda2omop analyze -i patient.xml --concept CONCEPT.csv -o analysis.csv
```

## Output Tables

The converter generates 8 OMOP CDM 5.3 tables as CSV files:

- `person.csv`
- `visit_occurrence.csv`
- `condition_occurrence.csv`
- `drug_exposure.csv`
- `procedure_occurrence.csv`
- `measurement.csv`
- `observation.csv`
- `device_exposure.csv`

## YAML Mapping Rules

Custom mapping rules can be defined in YAML format. See the `rules/` directory for examples.

## License

MIT License - Copyright 2025 Christophe Roeder
