.PHONY: phaseA-validate

phaseA-validate:
	uv sync
	uv run pytest -q
