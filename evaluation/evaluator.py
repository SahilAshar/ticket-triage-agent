
"""Core evaluator that runs the agent and metrics over examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from evaluation.agent_runner import AgentRunnerProtocol
from evaluation.metrics import Metric, MetricResult
from evaluation.types import EvalExample, EvalResult


def evaluate_examples(
    examples: Iterable[EvalExample],
    agent_runner: AgentRunnerProtocol,
    metrics: Sequence[Metric],
    limit: int | None = None,
) -> list[EvalResult]:
    """Evaluate examples sequentially using the provided agent runner and metrics."""

    results: list[EvalResult] = []
    count = 0
    for example in examples:
        if limit is not None and count >= limit:
            break
        response = agent_runner.run(example.task)
        metric_outputs: dict[str, float | bool | dict] = {}
        for metric in metrics:
            metric_result = metric.compute(example, response)
            metric_outputs[metric_result.name] = metric_result.value
            if metric_result.details:
                metric_outputs[f"{metric_result.name}_details"] = metric_result.details
        results.append(
            EvalResult(
                ticket_id=example.task.ticket_id,
                output=response.result,
                metrics=metric_outputs,
                metadata=response.metadata,
            )
        )
        count += 1
    return results


@dataclass(slots=True)
class AggregateSummary:
    """Container for aggregate metrics across the evaluation run."""

    total_examples: int
    categorical_accuracy: float
    next_step_match_rate: float
    schema_valid_pct: float
    total_cost_usd: float


def summarize_results(results: Sequence[EvalResult]) -> AggregateSummary:
    total = len(results)
    if total == 0:
        return AggregateSummary(0, 0.0, 0.0, 0.0, 0.0)

    accuracy_sum = 0.0
    next_step_sum = 0.0
    schema_valid_sum = 0.0
    cost_sum = 0.0

    for result in results:
        metrics = result.metrics
        accuracy_sum += float(metrics.get("categorical_accuracy", 0.0))
        next_step = metrics.get("next_step_match")
        if isinstance(next_step, bool):
            next_step_sum += 1.0 if next_step else 0.0
        schema_valid = metrics.get("schema_valid")
        if isinstance(schema_valid, bool):
            schema_valid_sum += 1.0 if schema_valid else 0.0
        cost_sum += float(metrics.get("usd_cost", 0.0))

    return AggregateSummary(
        total_examples=total,
        categorical_accuracy=accuracy_sum / total,
        next_step_match_rate=next_step_sum / total,
        schema_valid_pct=schema_valid_sum / total,
        total_cost_usd=cost_sum,
    )

