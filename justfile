_:
  @just --list

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check
  marimo check

# Run the test suite using pytest.
test:
  pytest

# Build the documentation using Zensical.
docs:
  zensical build
  # NOTE: run `python -m http.server -d site 8000` and open to see buttons
