
"""Dataset loading utilities for the evaluation harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from pydantic import ValidationError

from evaluation.issues import EvaluationIssue, IssueType
from evaluation.types import EvalExample
from ticket_agent import schemas


@dataclass(slots=True)
class DatasetLoadResult:
    examples: list[EvalExample]
    issues: list[EvaluationIssue]


def _append_issue(issues: list[EvaluationIssue], issue_type: IssueType, details: str, ticket_id: str | None = None) -> None:
    issues.append(EvaluationIssue(issue_type=issue_type, ticket_id=ticket_id, details=details))


def _iter_lines(path: Path) -> Iterator[tuple[int, str]]:
    with path.open("r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, 1):
            line = raw.strip()
            if line:
                yield lineno, line


def _parse_json(path: Path, lineno: int, raw: str, issues: list[EvaluationIssue]) -> dict | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        _append_issue(issues, IssueType.SCHEMA_FAILURE, f"{path}:{lineno} invalid JSON ({exc.msg})")
        return None
    if not isinstance(payload, dict):
        _append_issue(issues, IssueType.SCHEMA_FAILURE, f"{path}:{lineno} expected object root")
        return None
    return payload


def load_tasks(path: Path) -> tuple[dict[str, schemas.TicketTask], list[EvaluationIssue]]:
    tasks: dict[str, schemas.TicketTask] = {}
    issues: list[EvaluationIssue] = []
    for lineno, raw in _iter_lines(path):
        payload = _parse_json(path, lineno, raw, issues)
        if payload is None:
            continue
        task_data = payload.get("task")
        if task_data is None:
            _append_issue(
                issues,
                IssueType.SCHEMA_FAILURE,
                f"{path}:{lineno} missing 'task' field",
                str(payload.get("ticket_id", "")) or None,
            )
            continue
        try:
            task = schemas.TicketTask.model_validate(task_data)
        except ValidationError as exc:
            candidate = task_data.get("ticket_id") if isinstance(task_data, dict) else None
            _append_issue(issues, IssueType.SCHEMA_FAILURE, f"{path}:{lineno} task schema violation: {exc.errors()}", candidate)
            continue
        if task.ticket_id in tasks:
            _append_issue(issues, IssueType.JOIN_MISMATCH, f"{path}:{lineno} duplicate ticket_id", task.ticket_id)
            continue
        tasks[task.ticket_id] = task
    return tasks, issues


def load_labels(path: Path) -> tuple[dict[str, tuple[schemas.TicketResult, str | None]], list[EvaluationIssue]]:
    labels: dict[str, tuple[schemas.TicketResult, str | None]] = {}
    issues: list[EvaluationIssue] = []
    for lineno, raw in _iter_lines(path):
        payload = _parse_json(path, lineno, raw, issues)
        if payload is None:
            continue
        ticket_id = payload.get("ticket_id")
        if not isinstance(ticket_id, str) or not ticket_id:
            _append_issue(issues, IssueType.SCHEMA_FAILURE, f"{path}:{lineno} missing or invalid 'ticket_id'")
            continue
        expected = payload.get("expected_result")
        if expected is None:
            _append_issue(issues, IssueType.SCHEMA_FAILURE, f"{path}:{lineno} missing 'expected_result' field", ticket_id)
            continue
        try:
            result = schemas.TicketResult.model_validate(expected)
        except ValidationError as exc:
            _append_issue(issues, IssueType.SCHEMA_FAILURE, f"{path}:{lineno} result schema violation: {exc.errors()}", ticket_id)
            continue
        difficulty = payload.get("difficulty")
        if ticket_id in labels:
            _append_issue(issues, IssueType.JOIN_MISMATCH, f"{path}:{lineno} duplicate ticket_id", ticket_id)
            continue
        labels[ticket_id] = (result, difficulty if isinstance(difficulty, str) else None)
    return labels, issues


def assemble_examples(tasks_path: Path, labels_path: Path) -> DatasetLoadResult:
    examples: list[EvalExample] = []
    issues: list[EvaluationIssue] = []

    tasks, task_issues = load_tasks(tasks_path)
    labels, label_issues = load_labels(labels_path)
    issues.extend(task_issues)
    issues.extend(label_issues)

    task_ids = set(tasks)
    label_ids = set(labels)

    for ticket_id in sorted(task_ids - label_ids):
        _append_issue(issues, IssueType.JOIN_MISMATCH, "missing expected result for ticket_id", ticket_id)
    for ticket_id in sorted(label_ids - task_ids):
        _append_issue(issues, IssueType.JOIN_MISMATCH, "orphan expected result without matching task", ticket_id)

    for ticket_id in sorted(task_ids & label_ids):
        task = tasks[ticket_id]
        result, difficulty = labels[ticket_id]
        examples.append(EvalExample(task=task, gold=result, difficulty=difficulty))

    return DatasetLoadResult(examples=examples, issues=issues)

