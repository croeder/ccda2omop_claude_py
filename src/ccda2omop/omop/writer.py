# Copyright 2025 Christophe Roeder. All rights reserved.

"""CSV writer for OMOP CDM tables."""

import csv
from pathlib import Path
from typing import Union

from .models import (
    ConditionOccurrence,
    DeviceExposure,
    DrugExposure,
    Measurement,
    Observation,
    OMOPData,
    OMOPRecord,
    Person,
    ProcedureOccurrence,
    VisitOccurrence,
)


class CSVWriter:
    """Writes OMOP data to CSV files."""

    def __init__(self, output_dir: Union[str, Path]):
        """
        Initialize CSV writer.

        Args:
            output_dir: Directory for CSV output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_all(self, data: OMOPData) -> None:
        """
        Write all OMOP tables to CSV files.

        Args:
            data: OMOPData container with all tables
        """
        self._write_table("person.csv", data.persons, Person)
        self._write_table(
            "visit_occurrence.csv", data.visit_occurrences, VisitOccurrence
        )
        self._write_table(
            "condition_occurrence.csv", data.condition_occurrences, ConditionOccurrence
        )
        self._write_table("drug_exposure.csv", data.drug_exposures, DrugExposure)
        self._write_table(
            "procedure_occurrence.csv", data.procedure_occurrences, ProcedureOccurrence
        )
        self._write_table("measurement.csv", data.measurements, Measurement)
        self._write_table("observation.csv", data.observations, Observation)
        self._write_table(
            "device_exposure.csv", data.device_exposures, DeviceExposure
        )

    def _write_table(
        self,
        filename: str,
        records: list[OMOPRecord],
        record_class: type[OMOPRecord],
    ) -> None:
        """
        Write a single OMOP table to a CSV file.

        Args:
            filename: Name of the CSV file
            records: List of OMOP records
            record_class: The dataclass type for headers
        """
        filepath = self.output_dir / filename

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write headers
            headers = record_class.csv_headers()
            writer.writerow(headers)

            # Write data rows
            for record in records:
                writer.writerow(record.to_csv_row())
