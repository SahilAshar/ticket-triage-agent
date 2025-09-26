"""CLI for validating ticket triage datasets against Task/Result schemas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Iterator

from pydantic import ValidationError

from ticket_agent import schemas

ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}

def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, help="JSONL ticket task inputs")
    parser.add_argument("--labels", type=Path, help="JSONL expected results keyed by ticket_id")
    return parser.parse_args(argv)

def iter_json_lines(path: Path, errors: list[str]) -> Iterator[tuple[int, dict[str, object]]]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for lineno, raw in enumerate(handle, 1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    yield lineno, json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path}:{lineno} invalid JSON ({exc.msg})")
    except OSError as exc:  # pragma: no cover - surfaced directly to CLI
        errors.append(f"{path}: unable to open file ({exc})")

def validate_tasks(tasks_path: Path, errors: list[str]) -> dict[str, schemas.TicketTask]:
    index: dict[str, schemas.TicketTask] = {}
    for lineno, payload in iter_json_lines(tasks_path, errors):
        if not isinstance(payload, dict):
            errors.append(f"{tasks_path}:{lineno} expected an object root")
            continue
        if "difficulty" in payload:
            errors.append(f"{tasks_path}:{lineno} difficulty must not appear on task ingress")
        task_data = payload.get("task")
        if task_data is None:
            errors.append(f"{tasks_path}:{lineno} missing 'task' field")
            continue
        try:
            task = schemas.TicketTask.model_validate(task_data)
        except ValidationError as exc:
            errors.append(f"{tasks_path}:{lineno} task schema violation: {exc.errors()} ")
            continue
        ticket_id = task.ticket_id
        if ticket_id in index:
            errors.append(f"{tasks_path}:{lineno} duplicate ticket_id '{ticket_id}'")
            continue
        index[ticket_id] = task
    return index

def validate_labels(
    labels_path: Path, errors: list[str]
) -> dict[str, tuple[schemas.TicketResult, str]]:
    index: dict[str, tuple[schemas.TicketResult, str]] = {}
    for lineno, payload in iter_json_lines(labels_path, errors):
        if not isinstance(payload, dict):
            errors.append(f"{labels_path}:{lineno} expected an object root")
            continue
        ticket_id = payload.get("ticket_id")
        if not isinstance(ticket_id, str) or not ticket_id:
            errors.append(f"{labels_path}:{lineno} missing or invalid 'ticket_id'")
            continue
        difficulty = payload.get("difficulty")
        if difficulty not in ALLOWED_DIFFICULTY:
            errors.append(
                f"{labels_path}:{lineno} difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}"
            )
        expected_data = payload.get("expected_result")
        if expected_data is None:
            errors.append(f"{labels_path}:{lineno} missing 'expected_result' field")
            continue
        try:
            result = schemas.TicketResult.model_validate(expected_data)
        except ValidationError as exc:
            errors.append(f"{labels_path}:{lineno} result schema violation: {exc.errors()} ")
            continue
        if ticket_id in index:
            errors.append(f"{labels_path}:{lineno} duplicate ticket_id '{ticket_id}'")
            continue
        index[ticket_id] = (result, difficulty if isinstance(difficulty, str) else "")
    return index


def validate_dataset(tasks_path: Path | None, labels_path: Path | None) -> list[str]:
    errors: list[str] = []
    tasks: dict[str, schemas.TicketTask] = {}
    labels: dict[str, tuple[schemas.TicketResult, str]] = {}

    if tasks_path is not None:
        tasks = validate_tasks(tasks_path, errors)
    if labels_path is not None:
        labels = validate_labels(labels_path, errors)

    if tasks and labels:
        task_ids = set(tasks)
        label_ids = set(labels)
        for ticket_id in sorted(task_ids - label_ids):
            errors.append(f"missing expected result for ticket_id '{ticket_id}'")
        for ticket_id in sorted(label_ids - task_ids):
            errors.append(f"orphan expected result for ticket_id '{ticket_id}'")
    return errors


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    if args.tasks is None and args.labels is None:
        print("No files provided; nothing to validate. Pass --tasks and/or --labels.", file=sys.stderr)
        raise SystemExit(0)

    errors = validate_dataset(args.tasks, args.labels)
    if errors:
        for issue in errors:
            print(f"ERROR: {issue}", file=sys.stderr)
        print(f"Validation failed with {len(errors)} issue(s).", file=sys.stderr)
        raise SystemExit(1)
    print("Validation succeeded: tasks and expected results are schema-compliant.")


if __name__ == "__main__":
    main()
