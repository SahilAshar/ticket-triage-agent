"""Tests for evaluation.dataset utilities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from evaluation.dataset import assemble_examples
from evaluation.issues import IssueType


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _task(ticket_id: str) -> dict[str, dict[str, str | dict[str, str]]]:
    return {
        "task": {
            "ticket_id": ticket_id,
            "title": "Example title",
            "description": "Example description",
            "metadata": {"product_area": "testing"},
        }
    }


def _label(ticket_id: str, difficulty: str = "easy") -> dict[str, str | dict[str, str | float]]:
    return {
        "ticket_id": ticket_id,
        "difficulty": difficulty,
        "expected_result": {
            "category": "bug",
            "severity": "medium",
            "next_step": "Fix it",
            "confidence": 0.9,
        },
    }


def test_assemble_examples_happy_path(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    _write_jsonl(tasks_path, [_task("TKT-1")])
    _write_jsonl(labels_path, [_label("TKT-1")])

    result = assemble_examples(tasks_path, labels_path)

    assert len(result.examples) == 1
    example = result.examples[0]
    assert example.task.ticket_id == "TKT-1"
    assert example.gold.category == "bug"
    assert example.difficulty == "easy"
    assert result.issues == []


def test_assemble_examples_reports_missing_label(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    _write_jsonl(tasks_path, [_task("TKT-present"), _task("TKT-missing")])
    _write_jsonl(labels_path, [_label("TKT-present")])

    result = assemble_examples(tasks_path, labels_path)

    missing = [issue for issue in result.issues if issue.issue_type == IssueType.JOIN_MISMATCH]
    assert any(issue.ticket_id == "TKT-missing" for issue in missing)


def test_assemble_examples_invalid_json(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    tasks_path.write_text("{not json}\n", encoding="utf-8")
    _write_jsonl(labels_path, [_label("TKT-1")])

    result = assemble_examples(tasks_path, labels_path)

    assert any(issue.issue_type == IssueType.SCHEMA_FAILURE for issue in result.issues)
    assert result.examples == []

