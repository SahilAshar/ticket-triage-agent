
"""Unit tests for evaluation.metrics module."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from evaluation.metrics import (
    CategoricalAccuracyMetric,
    CostAggregator,
    NextStepMatcher,
    SchemaValidityMetric,
)
from evaluation.types import AgentResponse, AgentRunMetadata, EvalExample
from ticket_agent.schemas import TicketResult, TicketTask


def _example(*, category: str = "bug", severity: str = "medium", next_step: str = "Fix it") -> EvalExample:
    task = TicketTask(
        ticket_id="TKT-1",
        title="Example",
        description="Example desc",
        metadata={"product_area": "testing"},
    )
    gold = TicketResult(
        category=category,
        severity=severity,
        next_step=next_step,
        confidence=0.9,
    )
    return EvalExample(task=task, gold=gold, difficulty="easy")


def _response(
    *,
    category: str = "bug",
    severity: str = "medium",
    next_step: str = "Fix it",
    cost: float | None = 0.0,
) -> AgentResponse:
    result = TicketResult(
        category=category,
        severity=severity,
        next_step=next_step,
        confidence=0.8,
    )
    metadata = AgentRunMetadata(latency_ms=10.0, usd_cost=cost)
    return AgentResponse(result=result, metadata=metadata)


def test_schema_validity_metric() -> None:
    metric = SchemaValidityMetric()
    example = _example()
    response = _response()
    result = metric.compute(example, response)
    assert result.name == "schema_valid"
    assert result.value is True


def test_categorical_accuracy_metric_exact_match() -> None:
    metric = CategoricalAccuracyMetric()
    example = _example()
    response = _response()
    result = metric.compute(example, response)
    assert result.value == 1.0
    assert result.details == {"category_match": True, "severity_match": True}


def test_categorical_accuracy_metric_mismatch() -> None:
    metric = CategoricalAccuracyMetric()
    example = _example()
    response = _response(category="incident", severity="medium")
    result = metric.compute(example, response)
    assert result.value == 0.0
    assert result.details == {"category_match": False, "severity_match": True}


def test_next_step_matcher_normalizes_input() -> None:
    metric = NextStepMatcher()
    example = _example(next_step="Fix it")
    response = _response(next_step="  fix it  ")
    result = metric.compute(example, response)
    assert result.value is True
    assert result.details == {"normalized_gold": "fix it", "normalized_pred": "fix it"}


def test_cost_aggregator_uses_metadata() -> None:
    metric = CostAggregator()
    example = _example()
    response = _response(cost=1.23)
    result = metric.compute(example, response)
    assert pytest.approx(result.value, rel=1e-6) == 1.23


def test_cost_aggregator_defaults_to_zero() -> None:
    metric = CostAggregator()
    example = _example()
    response = _response(cost=None)
    result = metric.compute(example, response)
    assert result.value == 0.0

