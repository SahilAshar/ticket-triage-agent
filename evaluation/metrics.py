
"""Metric interfaces and baseline metrics for evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from evaluation.types import AgentResponse, EvalExample
from ticket_agent.schemas import TicketResult


@dataclass(slots=True)
class MetricResult:
    """Structured outcome for a single metric."""

    name: str
    value: float | bool
    details: dict[str, float | bool | str] | None = None


class Metric(Protocol):
    """Metric interface consumed by the evaluator."""

    name: str

    def compute(self, example: EvalExample, response: AgentResponse) -> MetricResult: ...


class SchemaValidityMetric:
    name = "schema_valid"

    def compute(self, example: EvalExample, response: AgentResponse) -> MetricResult:
        # Pydantic validation already occurred when creating TicketResult; always true unless runtime mutation occurs.
        return MetricResult(name=self.name, value=True)


class CategoricalAccuracyMetric:
    name = "categorical_accuracy"

    def compute(self, example: EvalExample, response: AgentResponse) -> MetricResult:
        gold: TicketResult = example.gold
        pred: TicketResult = response.result
        correct = (gold.category == pred.category) and (gold.severity == pred.severity)
        return MetricResult(
            name=self.name,
            value=1.0 if correct else 0.0,
            details={"category_match": gold.category == pred.category, "severity_match": gold.severity == pred.severity},
        )


class NextStepMatcher:
    name = "next_step_match"

    def compute(self, example: EvalExample, response: AgentResponse) -> MetricResult:
        gold_step = example.gold.next_step.strip().lower()
        pred_step = response.result.next_step.strip().lower()
        match = gold_step == pred_step
        return MetricResult(name=self.name, value=match, details={"normalized_gold": gold_step, "normalized_pred": pred_step})


class CostAggregator:
    name = "usd_cost"

    def compute(self, example: EvalExample, response: AgentResponse) -> MetricResult:
        metadata = response.metadata
        cost = metadata.usd_cost if metadata.usd_cost is not None else 0.0
        return MetricResult(name=self.name, value=cost)

