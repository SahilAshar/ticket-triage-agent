# AGENTS.md — Tool Selection (Python)

When you need to call tools from the shell, use this rubric:

## File & Text
- Find files by file name: `fd`
- Find files with path name: `fd -p <file-path>`
- List files in a directory: `fd . <directory>`
- Find files with extension and pattern: `fd -e <extension> <pattern>`
- Find Text: `rg` (ripgrep)
- Find Code Structure: `ast-grep`
  - Common languages:
    - Python → `ast-grep --lang python -p '<pattern>'`
    - TypeScript → `ast-grep --lang ts -p '<pattern>'`
    - Bash → `ast-grep --lang bash -p '<pattern>'`
    - TSX (React) → `ast-grep --lang tsx -p '<pattern>'`
    - JavaScript → `ast-grep --lang js -p '<pattern>'`
    - Rust → `ast-grep --lang rust -p '<pattern>'`
    - JSON → `ast-grep --lang json -p '<pattern>'`
  - Prefer `ast-grep` over ripgrep/grep unless a plain-text search is explicitly requested.
- Select among matches: pipe to `fzf`

## Data
- JSON: `jq`
- YAML/XML: `yq`

## Python Tooling
- Package Management & Virtual Envs: `uv`
  (fast replacement for pip/pip-tools/virtualenv; use `uv pip install ...`, `uv run ...`)
  - Setup workflow:
    1. `uv sync` — resolves dependencies and creates `.venv` using the Python version declared in `pyproject.toml` (`requires-python >= 3.13`).
    2. `source .venv/bin/activate` — activate the environment so `python`/`pytest`/etc. run under Python 3.13.
    3. Optionally use `uv run <command>` for one-off executions without activating the shell.
    4. Verify with `python --version` (should report 3.13.x) before running tooling.
  - Install new packages with `uv add <package>`.
- Linting & Formatting: `ruff`
  (linter + formatter; use `ruff check .`, `ruff format .`)
- Static Typing: `mypy`
  (type checking; use `mypy .`)
- Security: `bandit`
  (Python security linter; use `bandit -r .`)
- Testing: `pytest`
  (test runner; prefer `uv run pytest -q` or run after activating `.venv`; `pytest -k <pattern>` to filter tests)
- Logging: `loguru`
  (runtime logging utility; import in code:
  ```python
  from loguru import logger
  logger.info("message")
  ```)

## Notes
- Prefer uv for Python dependency and environment management instead of pip/venv/poetry/pip-tools.
- Prefer strong typing for all Python code. Focus on writing strong, maintainable, OOP oriented code.
