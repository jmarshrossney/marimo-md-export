_:
  @just lint typecheck test docs

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check --fix
  marimo check examples/notebook.py

# Same as `lint`, but doesn't make any formatting changes.
lint-check:
  ruff format --check
  ruff check
  marimo check examples/notebook.py

# Run the test suite using pytest.
test:
  pytest

# Run tests with coverage report (requires pytest-cov).
test-cov:
  pytest --cov=marimo_md_export --cov-report=term-missing --cov-fail-under=90

# Run static type checker.
typecheck:
  pyright src/marimo_md_export

# Build the documentation using Zensical.
docs:
  marimo-md-export examples/notebook.py docs/example.md
  zensical build
