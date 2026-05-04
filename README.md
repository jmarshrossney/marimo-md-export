# marimo-md-export

[![PyPI version](https://img.shields.io/pypi/v/marimo-md-export)](https://pypi.org/project/marimo-md-export/)
[![Python versions](https://img.shields.io/pypi/pyversions/marimo-md-export)](https://pypi.org/project/marimo-md-export/)
[![License](https://img.shields.io/pypi/l/marimo-md-export)](https://github.com/jmarshrossney/marimo-md-export/blob/main/LICENSE)
[![CI](https://github.com/jmarshrossney/marimo-md-export/actions/workflows/ci.yml/badge.svg)](https://github.com/jmarshrossney/marimo-md-export/actions/workflows/ci.yml)
[![Docs](https://github.com/jmarshrossney/marimo-md-export/actions/workflows/docs.yml/badge.svg)](https://jmarshrossney.github.io/marimo-md-export)

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

If you want the tool to be available globally you can "install" it with

```sh
uv tool install marimo-md-export
```

## Integrating with documentation sites

`marimo-md-export` is designed to produce markdown pages for static site generators like
[mkdocs](https://www.mkdocs.org/) (Python) or
[zensical](https://zensical.org/) (Rust). Both work identically for this purpose.

**1. Add as a docs dependency:**

```sh
uv add --group docs marimo-md-export
```

**2. Add a build step** that converts your notebook(s) before building the site.

For example, this project uses the following [just](https://github.com/casey/just) command to build the docs:

```just
docs:
  marimo-md-export examples/notebook.py docs/example.md \
    --html-output docs/example-notebook.html
  zensical build
```

This runs `marimo-md-export` to produce a self-contained markdown page (with any
`# @output:` cells injected as figures/tables), then builds the site.

## Development

```sh
uv sync  # sync packages
just  # run lint, typecheck, test, build docs
```
