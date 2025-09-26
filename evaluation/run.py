
"""CLI entrypoint for running the Phase A evaluation harness."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from evaluation.agent_runner import CallableAgentRunner, NoOpAgentRunner
from evaluation.dataset import assemble_examples
from evaluation.evaluator import AggregateSummary, evaluate_examples, summarize_results
from evaluation.metrics import (
    CategoricalAccuracyMetric,
    CostAggregator,
    Metric,
    NextStepMatcher,
    SchemaValidityMetric,
)
from evaluation.types import AgentResponse, AgentRunMetadata, EvalExample
from ticket_agent.schemas import TicketResult, TicketTask


DEFAULT_REPORT_ROOT = Path("reports/phaseA/runs")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=Path, required=True, help="Path to ticket tasks JSONL")
    parser.add_argument("--labels", type=Path, required=True, help="Path to expected results JSONL")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on number of examples")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Base directory for artifacts (timestamped subdirectory will be created automatically).",
    )
    parser.add_argument(
        "--agent-mode",
        choices=["noop", "gold"],
        default="noop",
        help="Agent implementation mode: 'gold' echoes expected results as a baseline.",
    )
    return parser.parse_args(argv)


def _resolve_output_dir(base: Path | None) -> Path:
    root = base or DEFAULT_REPORT_ROOT
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    output_dir = root / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _metrics() -> list[Metric]:
    return [
        SchemaValidityMetric(),
        CategoricalAccuracyMetric(),
        NextStepMatcher(),
        CostAggregator(),
    ]


def _build_gold_runner(examples: Iterable[tuple[str, TicketResult]]) -> CallableAgentRunner:
    mapping = {ticket_id: result for ticket_id, result in examples}

    def _run(task: TicketTask) -> AgentResponse:
        result = mapping.get(task.ticket_id)
        if result is None:
            raise KeyError(f"No gold label for ticket_id {task.ticket_id}")
        return AgentResponse(result=result, metadata=AgentRunMetadata(latency_ms=0.0))

    return CallableAgentRunner(_run)


def _build_agent_runner(mode: str, dataset_examples: Sequence[EvalExample]) -> CallableAgentRunner | NoOpAgentRunner:
    if mode == "noop":
        return NoOpAgentRunner()
    if mode == "gold":
        pairs = [(example.task.ticket_id, example.gold) for example in dataset_examples]
        return _build_gold_runner(pairs)
    raise ValueError(f"Unsupported agent mode: {mode}")


def _issue_to_dict(issue) -> dict:
    return {
        "issue_type": issue.issue_type.value,
        "ticket_id": issue.ticket_id,
        "details": issue.details,
        "metrics": issue.metrics,
        "severity": issue.severity,
    }


def _write_issues(path: Path, issues) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for issue in issues:
            handle.write(json.dumps(_issue_to_dict(issue)) + "\n")


def _write_summary(path: Path, summary: AggregateSummary) -> None:
    payload = {
        "total_examples": summary.total_examples,
        "categorical_accuracy": summary.categorical_accuracy,
        "next_step_match_rate": summary.next_step_match_rate,
        "schema_valid_pct": summary.schema_valid_pct,
        "total_cost_usd": summary.total_cost_usd,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")



def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    output_dir = _resolve_output_dir(args.output_dir)
    summary_path = output_dir / "summary.json"
    issues_path = output_dir / "issues.jsonl"

    dataset = assemble_examples(args.tasks, args.labels)
    _write_issues(issues_path, dataset.issues)

    if not dataset.examples:
        _write_summary(summary_path, AggregateSummary(0, 0.0, 0.0, 0.0, 0.0))
        return

    agent_runner = _build_agent_runner(args.agent_mode, dataset.examples)
    metrics = _metrics()
    results = evaluate_examples(dataset.examples, agent_runner, metrics, limit=args.limit)
    summary = summarize_results(results)
    _write_summary(summary_path, summary)

    if summary.schema_valid_pct < 0.95:
        raise SystemExit("Schema validity below 95% threshold")


if __name__ == "__main__":
    main()

