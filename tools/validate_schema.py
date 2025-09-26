"""CLI for validating ticket triage dataset against Task/Result schemas."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

# NOTE: we import lazily to avoid circular dependencies when schemas evolve.
from ticket_agent import schemas


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the schema validator."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the JSONL dataset containing ticket tasks and expected results.",
    )
    # TODO: add additional options (e.g., strict mode, schema version) when requirements emerge.

    return parser.parse_args(argv)


def validate_dataset(dataset_path: Path) -> None:
    """Validate each record in the dataset against Task/Result schemas."""

    # TODO: implement JSONL loading, schema validation, and reporting.
    raise NotImplementedError("Dataset validation logic to be implemented in Phase A.")


def main(argv: Iterable[str] | None = None) -> None:
    """Entry point for the schema validation CLI."""

    args = parse_args(argv)
    validate_dataset(args.dataset)


if __name__ == "__main__":
    main()
