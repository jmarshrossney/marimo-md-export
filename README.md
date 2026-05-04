# marimo-md-export

[![PyPI version](https://img.shields.io/pypi/v/marimo-md-export)](https://pypi.org/project/marimo-md-export/)
[![Python versions](https://img.shields.io/pypi/pyversions/marimo-md-export)](https://pypi.org/project/marimo-md-export/)
[![License](https://img.shields.io/pypi/l/marimo-md-export)](https://github.com/jmarshrossney/marimo-md-export/blob/main/LICENSE)
[![CI](https://github.com/jmarshrossney/marimo-md-export/actions/workflows/ci.yml/badge.svg)](https://github.com/jmarshrossney/marimo-md-export/actions/workflows/ci.yml)
[![Docs](https://github.com/jmarshrossney/marimo-md-export/actions/workflows/docs.yml/badge.svg)](https://jmarshrossney.github.io/marimo-md-export)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A `uv` tool that wraps `marimo export`, extracts rendered outputs from the HTML export,
and injects them into the markdown export. The result is a self-contained markdown
document with embedded figures (as base64 `<img>` tags) and tables (as GFM or HTML).

**[Full documentation](https://jmarshrossney.github.io/marimo-md-export)**

## Quick start

Mark cells in your marimo `.py` notebook with `# @output: <label>`:

```python
# @output: my_figure
fig, ax = plt.subplots()
ax.plot(x, np.sin(x))
fig
```

Then run:

```sh
uvx marimo-md-export notebook.py output.md
```

## Installation

```sh
uv tool install marimo-md-export   # or: pipx install marimo-md-export
```

## Development

```sh
uv sync  # sync packages
just  # run lint, typecheck, test, build docs
```
