
"""End-to-end evaluation harness tests using a stub agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from evaluation.agent_runner import AgentRunnerProtocol
from evaluation.dataset import assemble_examples
from evaluation.evaluator import evaluate_examples, summarize_results
from evaluation.metrics import (
    CategoricalAccuracyMetric,
    CostAggregator,
    NextStepMatcher,
    SchemaValidityMetric,
)
from evaluation.types import AgentResponse, AgentRunMetadata
from ticket_agent.schemas import TicketResult, TicketTask


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")


def _make_task(ticket_id: str, title: str) -> dict:
    return {
        "task": {
            "ticket_id": ticket_id,
            "title": title,
            "description": "Stub description",
            "metadata": {"product_area": "testing"},
        }
    }


def _make_label(ticket_id: str, category: str, severity: str, next_step: str) -> dict:
    return {
        "ticket_id": ticket_id,
        "difficulty": "easy",
        "expected_result": {
            "category": category,
            "severity": severity,
            "next_step": next_step,
            "confidence": 0.9,
        },
    }


class MappingAgentRunner(AgentRunnerProtocol):
    """Stub runner that returns preconfigured results keyed by ticket_id."""

    def __init__(self, mapping: dict[str, TicketResult], *, usd_cost: float = 0.0) -> None:
        self._mapping = mapping
        self._usd_cost = usd_cost

    def run(self, task: TicketTask) -> AgentResponse:
        try:
            result = self._mapping[task.ticket_id]
        except KeyError as exc:
            raise AssertionError(f"Missing stub result for {task.ticket_id}") from exc
        metadata = AgentRunMetadata(latency_ms=5.0, usd_cost=self._usd_cost)
        return AgentResponse(result=result, metadata=metadata)


@pytest.fixture()
def sample_dataset(tmp_path: Path) -> tuple[list, Path, Path]:
    tasks_path = tmp_path / "tasks.jsonl"
    labels_path = tmp_path / "labels.jsonl"
    _write_jsonl(
        tasks_path,
        [
            _make_task("TKT-1", "Login fails"),
            _make_task("TKT-2", "Billing question"),
        ],
    )
    _write_jsonl(
        labels_path,
        [
            _make_label("TKT-1", "bug", "high", "Escalate to engineering"),
            _make_label("TKT-2", "question", "low", "Send billing FAQ"),
        ],
    )
    dataset = assemble_examples(tasks_path, labels_path)
    assert not dataset.issues, "fixture should not produce dataset issues"
    return dataset.examples, tasks_path, labels_path


def test_evaluator_end_to_end_success(sample_dataset: tuple[list, Path, Path]) -> None:
    examples, _, _ = sample_dataset
    mapping = {ex.task.ticket_id: ex.gold for ex in examples}
    runner = MappingAgentRunner(mapping, usd_cost=0.25)
    metrics = [SchemaValidityMetric(), CategoricalAccuracyMetric(), NextStepMatcher(), CostAggregator()]

    results = evaluate_examples(examples, runner, metrics)
    assert len(results) == 2
    for result in results:
        assert result.metrics["categorical_accuracy"] == 1.0
        assert result.metrics.get("next_step_match") is True
        assert pytest.approx(result.metrics["usd_cost"], rel=1e-6) == 0.25

    summary = summarize_results(results)
    assert summary.total_examples == 2
    assert summary.categorical_accuracy == 1.0
    assert summary.next_step_match_rate == 1.0
    assert summary.schema_valid_pct == 1.0
    assert pytest.approx(summary.total_cost_usd, rel=1e-6) == 0.5


def test_evaluator_highlights_incorrect_results(sample_dataset: tuple[list, Path, Path]) -> None:
    examples, _, _ = sample_dataset
    mapping = {
        "TKT-1": TicketResult(
            category="bug",
            severity="high",
            next_step="Escalate to engineering",
            confidence=0.7,
        ),
        "TKT-2": TicketResult(
            category="incident",  # wrong category
            severity="low",
            next_step="Send billing FAQ",
            confidence=0.7,
        ),
    }
    runner = MappingAgentRunner(mapping, usd_cost=0.1)
    metrics = [SchemaValidityMetric(), CategoricalAccuracyMetric(), NextStepMatcher(), CostAggregator()]

    results = evaluate_examples(examples, runner, metrics)
    summary = summarize_results(results)

    assert summary.total_examples == 2
    assert summary.categorical_accuracy == 0.5  # one of two tickets mismatched
    assert summary.next_step_match_rate == 1.0  # steps align despite category miss
    assert summary.schema_valid_pct == 1.0
    assert pytest.approx(summary.total_cost_usd, rel=1e-6) == 0.2

    failing_result = next(r for r in results if r.ticket_id == "TKT-2")
    assert failing_result.metrics["categorical_accuracy"] == 0.0
    assert failing_result.metrics["categorical_accuracy_details"] == {
        "category_match": False,
        "severity_match": True,
    }

