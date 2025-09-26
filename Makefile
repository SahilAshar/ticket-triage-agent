.PHONY: phaseA-validate

phaseA-validate:
	uv sync
	uv run pytest tests/test_validate_schema.py
	uv run pytest tests/test_evaluation_dataset.py
	uv run pytest tests/test_evaluation_metrics.py
	uv run pytest tests/test_evaluation_e2e.py

.PHONY: phaseA-eval

phaseA-eval:
	uv sync
	uv run python -m evaluation.run --tasks data/tickets_phaseA.jsonl --labels data/expected_results_phaseA.jsonl --agent-mode gold
