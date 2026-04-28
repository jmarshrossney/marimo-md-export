_:
  @just --list

# Format and lint the package using ruff, and lint the examples using marimo.
lint:
  ruff format
  ruff check
  marimo check tests/integration/example.py

# Run the test suite using pytest.
test:
  pytest

# Build the documentation using Zensical.
docs:
  marimo-md-export tests/integration/example.py docs/example.md \
    --html-output docs/example-notebook.html
  zensical build
  # NOTE: run `python -m http.server -d site 8000` and open to see buttons
