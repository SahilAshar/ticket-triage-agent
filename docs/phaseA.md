# Phase A Plan — Single Ticket Triage Agent

## Goals & Guardrails
- Deliver a reproducible Agent v0 that maps `TicketTask` → `TicketResult` deterministically.
- Meet non-negotiable contracts: validated Task/Result schemas, minimal tool belt, hard constraints on temperature/tool budget/timeout.
- Produce measurable artifacts: labeled dataset, logging outputs, accuracy/latency/$ baselines, CI gate.
- Exit with 95%+ schema-valid responses and published metrics that can be quoted.

## Workstream Timeline (1–2 days)
Work through four mandatory checkpoints (A1–A4) plus an optional optimization (A5). Each checkpoint includes a smoke test that must pass before moving forward.

### Checkpoint A1 — Schema Definition & Seed Data (Day 0.5)
**Objectives**: lock in `TicketTask` & `TicketResult` schemas; create labeled examples.
- Tasks
  - Draft JSON schema (or Pydantic models) capturing required fields, typing, constraints.
  - Document determinism knobs (temperature=0, max_tokens cap, tool budget ≤2, wall-clock timeout, idempotency key usage).
  - Write 25 curated ticket examples: mix of categories/severities, include edge cases that stress schema validation.
  - Store examples in repo (e.g., `data/tickets_phaseA.jsonl`) with metadata for future reuse.
- Artifacts
  - `schemas.py` (or equivalent) with Pydantic models + JSON schema export.
  - `data/tickets_phaseA.jsonl` labeled set.
  - README snippet describing determinism configuration.
- **Smoke Test A1**: run schema validation script against the 25 examples (`python -m tools.validate_schema data/tickets_phaseA.jsonl`) verifying 100% pass.

### Checkpoint A2 — Agent v0 Skeleton (Day 1)
**Objectives**: implement a single-agent pipeline with minimal tool belt.
- Tasks
  - Implement stateful agent wrapper that accepts `TicketTask`, enforces determinism knobs, and returns `TicketResult`.
  - Integrate retriever/classifier/generator abstractions; start with stub tools using local resources or deterministic prompts.
  - Implement tool budget / timeout enforcement with defensive logging.
  - Wire temperature=0 and max token limit into LLM calls (or mocks if model not yet wired).
- Artifacts
  - `agent/ticket_agent.py` (core orchestration).
  - `tools/` directory with `retriever.py`, `classifier.py`, `generator.py` minimal implementations.
  - Config file (`config/agent.yaml`) capturing knobs and defaults.
- **Smoke Test A2**: run dry-run script (`python scripts/smoke_ticket_agent.py --sample 5`) over 5 sample tasks to ensure deterministic completion and schema-valid outputs.

### Checkpoint A3 — Instrumentation & Metrics (Day 1.5)
**Objectives**: add logging for latency, token usage, cost, retries, cache hit flag, failure reason.
- Tasks
  - Instrument agent calls with timing and token accounting hooks.
  - Define structured log format (JSONL) stored under `logs/phaseA/`.
  - Compute per-run summary (`metrics/phaseA_baseline.json`) capturing accuracy placeholder, p95 latency, $/task, retry counts.
  - Add monitoring of tool budget consumption + enforcement.
- Artifacts
  - `logging/metrics.py` utilities.
  - Sample log file from smoke test.
  - Metrics summary file committed.
- **Smoke Test A3**: execute `python scripts/run_agent.py --dataset data/tickets_phaseA.jsonl --limit 10 --emit-metrics` and verify logs include required fields (`accuracy`, `latency_ms`, `tokens_in`, `tokens_out`, `usd_cost`, `cache_hit`, `retries`, `failure_reason`).

### Checkpoint A4 — Eval Harness & CI Gate (Day 2)
**Objectives**: formalize evaluation and gating.
- Tasks
  - Build evaluation harness that compares `TicketResult` vs ground truth (accuracy metric definition, severity/category match, next-step check).
  - Produce baseline metrics table saved to `reports/phaseA_baseline.md`.
  - Add CI job (GitHub Actions or local `make` task) that runs schema validation + eval harness on PRs.
  - Ensure reproducibility: deterministic seeds, fixed model version/config.
- Artifacts
  - `evaluation/eval_ticket_agent.py` harness.
  - CI configuration updates (`.github/workflows/phaseA.yml` or equivalent).
  - Baseline report committed.
- **Smoke Test A4**: run `make phaseA-check` (or `tox -e phaseA`) locally to execute full pipeline; pass condition is ≥95% schema-valid outputs and baseline metric files regenerated without diff.

### Checkpoint A5 (Optional) — Cache Integration & Cost Optimization
**Objectives**: add cache layer keyed on `(prompt_hash, model)` with TTL.
- Tasks
  - Implement simple cache storage (SQLite/Redis/file-based) respecting TTL.
  - Integrate cache hits into agent flow and metrics.
  - Rerun evaluation comparing pre/post cache $/task.
- Artifacts
  - `infrastructure/cache.py` and configuration.
  - Updated metrics table showing reduced cost.
- **Smoke Test A5**: rerun `make phaseA-check` twice; second run should report increased cache-hit rate and lower average cost.

## Testing Strategy
- Unit tests: schemas, tool wrappers, metrics utilities (`pytest tests/`).
- Integration tests: smoke scripts per checkpoint; evaluation harness using labeled dataset.
- Determinism tests: repeat agent runs (`python scripts/run_agent.py --repeat 3 --seed 42`) to ensure identical outputs.
- CI: enforce schema validation + evaluation; block if metrics regress beyond thresholds.

## TODO Backlog
1. Scaffold project structure (`agent/`, `tools/`, `evaluation/`, `scripts/`, `data/`).
2. Implement schema definitions and validation CLI.
3. Author labeled dataset and edge-case coverage guidelines.
4. Build Agent v0 with tool abstractions and determinism guards.
5. Add instrumentation hooks and log storage conventions.
6. Develop evaluation harness + baseline metrics report.
7. Configure CI pipeline and local `make` targets for repeatability.
8. Optional: implement cache layer and rerun evaluations.

## Dependencies & Risks
- Model access: need deterministic LLM (inference endpoint or local) with known cost metrics.
- Token accounting: ensure provider APIs expose token usage or approximate via tokenizer.
- CI environment: confirm access to dataset files and secrets (if model keys needed) without leaking.
- Timeboxed scope: defer advanced tools (e.g., RAG) until failing tests require them.

## Acceptance Checklist (Exit Criteria)
- [ ] Schemas + dataset landed and validated.
- [ ] Agent v0 produces schema-valid outputs on sample set.
- [ ] Metrics logging yields accuracy, p95 latency, cost per task.
- [ ] Eval harness + CI gate operational with reproducible runs.
- [ ] Baseline report ready to quote, including schema validity ≥95%.
- [ ] (Optional) Cache integrated and evaluated.
