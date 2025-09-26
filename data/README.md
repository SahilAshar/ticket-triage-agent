# Phase A Ticket Dataset

## Files
- `tickets_phaseA.jsonl`: ticket task inputs.
- `expected_results_phaseA.jsonl`: ground-truth results keyed by `ticket_id`, with a difficulty label for debugging.
- `difficulty_backlog.md`: notes on future hard-mode scenarios to extend the dataset.

## Record Formats

`tickets_phaseA.jsonl`
```json
{
  "difficulty": "easy | medium | hard",
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

### Confidence Values
Confidence is currently a heuristic derived from difficulty:
- `easy` → 0.9
- `medium` → 0.8
- `hard` (reserved for future additions) → 0.7

These values act as placeholders until empirical calibration is available from live agent runs.
