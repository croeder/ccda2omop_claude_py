# Copyright 2025 Christophe Roeder. All rights reserved.

"""OMOP vocabulary table loader and indexer."""

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class Concept:
    """Represents a row from the OMOP CONCEPT table."""

    concept_id: int
    concept_name: str
    domain_id: str
    vocabulary_id: str
    concept_class_id: str
    standard_concept: str
    concept_code: str


class VocabLoader:
    """Loads and indexes OMOP vocabulary tables."""

    # Vocabularies we care about
    RELEVANT_VOCABS = {
        "SNOMED",
        "RxNorm",
        "LOINC",
        "ICD10CM",
        "ICD9CM",
        "CPT4",
        "HCPCS",
        "CVX",
        "NDC",
        "UNII",
        "NDFRT",
        "NCI",
        "ActCode",
        "RouteOfAdministration",
        "Gender",
        "Race",
        "Ethnicity",
        "UCUM",
        "Visit",
    }

    def __init__(self):
        # Index by vocabulary_id + concept_code -> Concept
        self._concept_index: dict[str, Concept] = {}

        # Index by concept_id -> Concept
        self._concept_by_id: dict[int, Concept] = {}

        # Maps source concept_id -> target standard concept_ids
        self._maps_to: dict[int, list[int]] = {}

    def _concept_key(self, vocab_id: str, code: str) -> str:
        """Create a lookup key from vocabulary and code."""
        return f"{vocab_id}|{code}"

    def load_concepts(self, filepath: Union[str, Path]) -> int:
        """
        Load the CONCEPT.csv file.

        Args:
            filepath: Path to CONCEPT.csv

        Returns:
            Number of concepts loaded
        """
        filepath = Path(filepath)
        count = 0

        with open(filepath, "r", encoding="utf-8") as f:
            # Use csv reader with tab delimiter
            reader = csv.reader(f, delimiter="\t")

            # Read header
            header = next(reader)
            if not header[0].startswith("concept_id"):
                raise ValueError(f"Unexpected CONCEPT.csv header: {header}")

            for row in reader:
                if len(row) < 10:
                    continue

                vocab_id = row[3]
                # Only load relevant vocabularies to save memory
                if vocab_id not in self.RELEVANT_VOCABS:
                    continue

                try:
                    concept_id = int(row[0])
                except ValueError:
                    continue

                # Skip invalid concepts
                if row[9]:  # invalid_reason
                    continue

                concept = Concept(
                    concept_id=concept_id,
                    concept_name=row[1],
                    domain_id=row[2],
                    vocabulary_id=vocab_id,
                    concept_class_id=row[4],
                    standard_concept=row[5],
                    concept_code=row[6],
                )

                key = self._concept_key(vocab_id, concept.concept_code)
                self._concept_index[key] = concept
                self._concept_by_id[concept_id] = concept
                count += 1

        logger.info(f"Loaded {count} concepts from vocabulary tables")
        return count

    def load_concept_relationships(self, filepath: Union[str, Path]) -> int:
        """
        Load the CONCEPT_RELATIONSHIP.csv file.

        Only loads "Maps to" relationships for mapping source to standard concepts.

        Args:
            filepath: Path to CONCEPT_RELATIONSHIP.csv

        Returns:
            Number of relationships loaded
        """
        filepath = Path(filepath)
        count = 0

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")

            # Read header
            header = next(reader)
            if not header[0].startswith("concept_id_1"):
                raise ValueError(
                    f"Unexpected CONCEPT_RELATIONSHIP.csv header: {header}"
                )

            for row in reader:
                if len(row) < 6:
                    continue

                # Only load "Maps to" relationships
                if row[2] != "Maps to":
                    continue

                # Skip invalid relationships
                if row[5]:  # invalid_reason
                    continue

                try:
                    source_id = int(row[0])
                    target_id = int(row[1])
                except ValueError:
                    continue

                # Only store if source concept is in our index
                if source_id in self._concept_by_id:
                    if source_id not in self._maps_to:
                        self._maps_to[source_id] = []
                    self._maps_to[source_id].append(target_id)
                    count += 1

        logger.info(f"Loaded {count} 'Maps to' relationships")
        return count

    def load_supplementary_vocab(self, filepath: Union[str, Path]) -> int:
        """
        Load additional vocabulary concepts from a CSV file.

        Uses the same format as CONCEPT.csv (tab-separated).
        Lines starting with # are treated as comments and skipped.

        Args:
            filepath: Path to supplementary vocabulary file

        Returns:
            Number of concepts loaded
        """
        filepath = Path(filepath)
        count = 0

        with open(filepath, "r", encoding="utf-8") as f:
            # Skip comment lines until we find header
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not line.startswith("concept_id"):
                    raise ValueError(
                        f"Unexpected header in supplementary vocab: {line}"
                    )
                break  # Found header, continue with csv reader

            # Reset and re-read with csv
            f.seek(0)
            reader = csv.reader(f, delimiter="\t")

            # Skip to header
            for row in reader:
                if row and row[0].startswith("concept_id"):
                    break

            for row in reader:
                if not row or row[0].startswith("#"):
                    continue
                if len(row) < 7:
                    continue

                try:
                    concept_id = int(row[0])
                except ValueError:
                    continue

                # Skip if invalid_reason is set (field 9 if present)
                if len(row) > 9 and row[9]:
                    continue

                concept = Concept(
                    concept_id=concept_id,
                    concept_name=row[1],
                    domain_id=row[2],
                    vocabulary_id=row[3],
                    concept_class_id=row[4],
                    standard_concept=row[5],
                    concept_code=row[6],
                )

                key = self._concept_key(concept.vocabulary_id, concept.concept_code)
                self._concept_index[key] = concept
                self._concept_by_id[concept_id] = concept
                count += 1

        logger.info(f"Loaded {count} supplementary concepts from {filepath}")
        return count

    def lookup_concept(self, vocab_id: str, code: str) -> Optional[Concept]:
        """Find a concept by vocabulary ID and code."""
        key = self._concept_key(vocab_id, code)
        return self._concept_index.get(key)

    def lookup_concept_by_id(self, concept_id: int) -> Optional[Concept]:
        """Find a concept by its ID."""
        return self._concept_by_id.get(concept_id)

    def get_standard_concept_id(self, vocab_id: str, code: str) -> int:
        """
        Get the first standard concept ID for a source concept.

        For concepts with multiple mappings, use get_standard_concept_ids instead.
        """
        ids = self.get_standard_concept_ids(vocab_id, code)
        return ids[0] if ids else 0

    def get_standard_concept_ids(self, vocab_id: str, code: str) -> list[int]:
        """
        Get all standard concept IDs for a source concept.

        A single source concept can map to multiple standard concepts.
        """
        concept = self.lookup_concept(vocab_id, code)
        if concept is None:
            return []

        # If already standard, return it
        if concept.standard_concept == "S":
            return [concept.concept_id]

        # Follow "Maps to" relationships
        target_ids = self._maps_to.get(concept.concept_id, [])
        if target_ids:
            return target_ids

        # Return the source concept ID if no mapping found
        return [concept.concept_id]

    def get_concept_domain(self, concept_id: int) -> str:
        """Get the domain_id for a concept."""
        concept = self._concept_by_id.get(concept_id)
        return concept.domain_id if concept else ""
