# Phase A Reporting Strategy

## Summary
The evaluation harness must surface clear, machine-parseable signals so CI and developers can distinguish between:
1. Schema failures (outputs violate `TicketResult` contract).
2. Join mismatches (tasks or labels missing/duplicated `ticket_id`).
3. Metric regressions (accuracy/latency/cost outside tolerated ranges).

## Reporting Categories
- **SchemaFailure**: Emitted when either the input datasets or agent outputs fail schema validation. Sources:
  - `tools.validate_schema` (dataset preprocessing).
  - `SchemaValidityMetric` (agent output evaluation).
- **JoinMismatch**: Raised when `ticket_id` reconciliation reveals missing or orphan records.
- **MetricRegression**: Triggered when aggregate metrics fall below configured thresholds (e.g., accuracy < 0.9, schema-valid < 0.95, p95 latency > target, cost > budget).

Each category maps to a structured payload:
```json
{
  "issue_type": "SchemaFailure | JoinMismatch | MetricRegression",
  "ticket_id": "TKT-0001 | null",
  "details": "human-readable context for debugging",
  "metrics": {"accuracy": 0.84, "schema_valid": true},
  "timestamp": "2024-10-01T12:34:56Z"
}
```

## Reusable Error Class
Introduce `EvaluationIssue` dataclass in `evaluation/issues.py`:
- Fields: `issue_type`, `ticket_id`, `details`, `metrics`, `severity`.
- Enum `IssueType` with initial values: `SCHEMA_FAILURE`, `JOIN_MISMATCH`, `METRIC_REGRESSION`.
- Helper constructors (e.g., `EvaluationIssue.schema_failure(...)`) to standardize message formats.

### Benefits
- Centralizes error semantics; future phases can add types (`CACHE_STALE`, `TOOL_FAILURE`) without rewriting aggregate logic.
- Simplifies CI parsing; JSON output can be consumed by GitHub annotations or dashboards.
- Encourages consistent logging structure across validator, evaluator, and metrics modules.

### Usage Flow
1. Validation CLI: on error, emit `EvaluationIssue.schema_failure` entries alongside stderr messages and write to `reports/phaseA/issues.jsonl`.
2. Evaluator: accumulate issues during execution; persist at end of run for artifact review.
3. CI: fail job when critical issues appear (e.g., `IssueType != METRIC_REGRESSION` with severity `ERROR`).

## Output Artifacts
- `reports/phaseA/issues.jsonl`: machine-consumable log of `EvaluationIssue` entries.
- `reports/phaseA/summary.json`: aggregate metrics with thresholds and status (`pass`/`fail`).
- `reports/phaseA/latest.md`: human-readable report summarizing metrics and listing top issues.

## Next Steps
- Implement `evaluation/issues.py` with dataclass + Enum.
- Update evaluator prototype to collect and emit issues.
- Extend CI workflow to surface issue logs as artifacts for inspection.
