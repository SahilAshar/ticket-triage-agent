.PHONY: phaseA-validate

phaseA-validate:
	uv sync
	uv run pytest tests/test_validate_schema.py
