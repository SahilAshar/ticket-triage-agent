"""Tests for the dataset validation CLI utilities."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from tools import validate_schema


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _make_task(ticket_id: str) -> dict[str, object]:
    return {
        "task": {
            "ticket_id": ticket_id,
            "title": "Sample title",
            "description": "Detailed description",
            "metadata": {"product_area": "sample"},
        }
    }


def _make_label(ticket_id: str, difficulty: str = "easy") -> dict[str, object]:
    return {
        "ticket_id": ticket_id,
        "difficulty": difficulty,
        "expected_result": {
            "category": "bug",
            "severity": "medium",
            "next_step": "Do something helpful",
            "confidence": 0.9,
        },
    }


def test_validate_dataset_tasks_only_ok(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    _write_jsonl(tasks_path, [_make_task("TKT-1")])

    errors = validate_schema.validate_dataset(tasks_path, None)

    assert errors == []


def test_validate_dataset_labels_only_ok(tmp_path: Path) -> None:
    labels_path = tmp_path / "labels.jsonl"
    _write_jsonl(labels_path, [_make_label("TKT-1")])

    errors = validate_schema.validate_dataset(None, labels_path)

    assert errors == []


def test_validate_dataset_both_ok(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    _write_jsonl(tasks_path, [_make_task("TKT-1")])
    _write_jsonl(labels_path, [_make_label("TKT-1")])

    errors = validate_schema.validate_dataset(tasks_path, labels_path)

    assert errors == []


def test_validate_dataset_task_schema_violation(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    bad_task = {
        "task": {
            "ticket_id": "TKT-1",
            "title": "Sample title",
            # description missing to trigger validation error
            "metadata": {"product_area": "sample"},
        }
    }
    _write_jsonl(tasks_path, [bad_task])

    errors = validate_schema.validate_dataset(tasks_path, None)

    assert errors and "task schema violation" in errors[0]


def test_validate_dataset_duplicate_ticket_id(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    _write_jsonl(tasks_path, [_make_task("TKT-1"), _make_task("TKT-1")])

    errors = validate_schema.validate_dataset(tasks_path, None)

    assert any("duplicate ticket_id" in err for err in errors)


def test_validate_dataset_missing_and_orphan_labels(tmp_path: Path) -> None:
    tasks_path = tmp_path / "tasks.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    _write_jsonl(tasks_path, [_make_task("TKT-present"), _make_task("TKT-missing")])
    _write_jsonl(labels_path, [_make_label("TKT-present"), _make_label("TKT-orphan")])

    errors = validate_schema.validate_dataset(tasks_path, labels_path)

    assert any("missing expected result" in err for err in errors)
    assert any("orphan expected result" in err for err in errors)


def test_validate_dataset_invalid_label_difficulty(tmp_path: Path) -> None:
    labels_path = tmp_path / "labels.jsonl"
    invalid_label = _make_label("TKT-1", difficulty="unknown")
    _write_jsonl(labels_path, [invalid_label])

    errors = validate_schema.validate_dataset(None, labels_path)

    assert any("difficulty must be one of" in err for err in errors)


def test_validate_dataset_missing_expected_result_field(tmp_path: Path) -> None:
    labels_path = tmp_path / "labels.jsonl"
    label = {"ticket_id": "TKT-1", "difficulty": "easy"}
    _write_jsonl(labels_path, [label])

    errors = validate_schema.validate_dataset(None, labels_path)

    assert any("missing 'expected_result'" in err for err in errors)
