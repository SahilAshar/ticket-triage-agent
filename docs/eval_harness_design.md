# Eval Harness Design (Phase A)

Objective: provide a reusable evaluation harness that consumes ticket tasks and gold labels, executes the agent deterministically, and emits accuracy/latency/cost metrics suitable for CI gating. The design should generalize to additional agent types without major rewrites.

## High-Level Flow
1. **Input Loading**
   - Use existing `tickets_phaseA.jsonl` (tasks) and `expected_results_phaseA.jsonl` (labels).
   - Parse via shared utility capable of handling future dataset variants (e.g., `dataset/io.py`).
2. **Join & Validation**
   - Reuse `tools.validate_schema` to ensure schema compliance prior to evaluation.
   - Build an in-memory index keyed by `ticket_id`, producing `EvalExample` objects that combine task payload, gold result, and difficulty.
3. **Agent Execution Layer**
   - Introduce `agent/runner.py` providing an `AgentRunner` abstraction that accepts `TicketTask` and returns `TicketResult` plus metadata (tokens, latency, tool calls).
   - Support dependency injection so tests can swap in mock agents.
4. **Metric Computation**
   - Implement `evaluation/metrics.py` with modular metric interfaces:
     - `SchemaValidityMetric` (pass/fail per output).
     - `CategoricalAccuracyMetric` (category/severity match).
     - `NextStepMatcher` (rule-based string/intent comparison; start simple with exact match + normalization).
     - `CostAggregator` (tokens + $ cost, derived from agent metadata).
   - Compose metrics in a pipeline to produce both per-example annotations and aggregate summaries.
5. **Reporting & Artifacts**
   - Emit JSONL with per-example results (`reports/phaseA/eval_examples.jsonl`).
   - Emit aggregate summary (`reports/phaseA/summary.json`) containing accuracy %, schema-valid %, p95 latency, avg $/task, tool budget usage.
   - Optionally render Markdown table (`reports/phaseA/latest.md`) for human-friendly review.
6. **CLI Entrypoint**
   - Provide `python -m evaluation.run --tasks ... --labels ... --agent-config config/agent.yaml`.
   - Flags for filtered evaluation (e.g., `--difficulty medium`, `--limit 10`).

## Data Structures
- `EvalExample` (dataclass)
  - `task: TicketTask`
  - `gold: TicketResult`
  - `difficulty: str`
- `EvalResult` (dataclass)
  - `ticket_id`
  - `output: TicketResult`
  - `metrics: dict[str, float | bool]`
  - `metadata: AgentRunMetadata`
- `AgentRunMetadata`
  - `latency_ms`
  - `tokens_in`
  - `tokens_out`
  - `usd_cost`
  - `tool_calls`
  - `retries`
  - `failure_reason`

## Modularity & Extensibility Considerations
- **Pluggable Schemas**: Keep schema references abstracted so future tasks can supply their own `TaskModel`/`ResultModel` (strategy pattern or simple registry).
- **Metric Registry**: Allow registering additional metric classes via config; metrics implement `compute(example, output, metadata) -> MetricResult`.
- **Agent Interface**: Define protocol (`AgentProtocol`) with `run(task: BaseModel) -> AgentResponse`; different agents (LLM-backed, rule-based) can satisfy it.
- **Dataset Abstraction**: Use loader functions that can accept alternate file layouts (e.g., combined JSONL) to avoid duplicating logic when Phase B adds new datasets.

## Pseudo-code Sketch
```python
# evaluation/run.py
def main(argv: Sequence[str]) -> None:
    args = parse_args(argv)
    validate_schema(args.tasks, args.labels)
    examples = load_examples(args.tasks, args.labels)

    agent = build_agent(args.agent_config)
    metrics = load_metrics(args.metrics_config)

    evaluator = Evaluator(agent=agent, metrics=metrics)
    results = evaluator.evaluate(examples, limit=args.limit)

    write_example_logs(results, args.output_examples)
    summary = aggregate_metrics(results)
    write_summary(summary, args.output_summary)
    render_markdown(summary, args.output_markdown)

    if summary["schema_valid_pct"] < 0.95:
        raise SystemExit("Schema validity below threshold")
```

```python
# evaluation/evaluator.py
class Evaluator:
    def __init__(self, agent: AgentProtocol, metrics: list[Metric]):
        self.agent = agent
        self.metrics = metrics

    def evaluate(self, examples: Iterable[EvalExample], limit: int | None = None) -> list[EvalResult]:
        results = []
        for example in itertools.islice(examples, limit):
            response = self.agent.run(example.task)
            metric_outputs = {
                metric.name: metric.compute(example, response)
                for metric in self.metrics
            }
            results.append(EvalResult(
                ticket_id=example.task.ticket_id,
                output=response.result,
                metrics=metric_outputs,
                metadata=response.metadata,
            ))
        return results
```

## Logging & Observability
- Integrate structured logging via `logging` or `loguru` to capture per-run telemetry.
- Support verbosity flag to emit verbose logs for debugging failing examples.

## Future-Proofing Notes
- Difficulty metadata can drive stratified metrics (e.g., accuracy by difficulty band).
- Add cache-awareness by recording `cache_hit` from metadata and reflecting cost savings.
- For future multi-agent phases, evaluator can accept a strategy that orchestrates multiple agents sequentially.

```
