# Phase A Ticket Dataset

## Files
- `tickets_phaseA.jsonl`: ticket task inputs.
- `expected_results_phaseA.jsonl`: ground-truth results keyed by `ticket_id`, with a difficulty label for debugging.
- `difficulty_backlog.md`: notes on future hard-mode scenarios to extend the dataset.

## Record Formats

`tickets_phaseA.jsonl`
```json
{
  "task": {
    "ticket_id": "TKT-XXXX",
    "title": "…",
    "description": "…",
    "metadata": {"optional": "tags"}
  }
}
```

`expected_results_phaseA.jsonl`
```json
{
  "ticket_id": "TKT-XXXX",
  "difficulty": "easy | medium | hard",
  "expected_result": {
    "category": "bug | incident | request | question",
    "severity": "low | medium | high | critical",
    "next_step": "Action to take",
    "confidence": 0.0
  }
}
```

> Difficulty is reserved for internal debugging/analysis and must never be surfaced to the agent ingress.

### Confidence Values
Confidence is currently a heuristic derived from difficulty:
- `easy` → 0.9
- `medium` → 0.8
- `hard` (reserved for future additions) → 0.7

Validate inputs with `python -m tools.validate_schema --tasks data/tickets_phaseA.jsonl` and labels with `python -m tools.validate_schema --labels data/expected_results_phaseA.jsonl`; pass both paths to enforce ticket_id reconciliation.

These values act as placeholders until empirical calibration is available from live agent runs.

## Dataset QA Summary (Planned)
- Run `python -m tools.validate_schema --tasks data/tickets_phaseA.jsonl --labels data/expected_results_phaseA.jsonl --summary --output-dir reports/phaseA/runs/latest` to produce a deterministic QA snapshot.
- JSON output fields:
  - `record_count`: per-file record totals.
  - `difficulty_distribution`: counts of `easy`/`medium`/`hard` tickets (labels only).
  - `duplicate_ticket_ids`: duplicates detected, if any.
  - `missing_vs_orphan_counts`: counts for missing expected results and orphan labels.
  - `random_schema_samples`: up to `--sample-size` ticket IDs selected with seed `--seed` (defaults 3 and 42).
  - `last_modified`: ISO-8601 timestamps for the dataset files when QA was run.
- When `--output-dir` is provided the CLI also writes `dataset_summary.md` with the same stats rendered in Markdown for quick review.
- CI will call the summary command during `make phaseA-validate` once the implementation lands, ensuring any dataset drift is surfaced alongside schema validation.
