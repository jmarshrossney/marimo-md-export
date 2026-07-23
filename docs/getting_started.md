# Getting Started

## Installation

### As a stand-alone tool

=== "uv"

    ```sh
    uv tool install marimo-md-export
    ```

=== "pipx"

    ```sh
    pipx install marimo-md-export
    ```

The `marimo-md-export` command is then available globally on your system.

To run without installing:

```sh
uvx marimo-md-export notebook.py output.md
```

### As a project dependency

Install and add to your `pyproject.toml`:

=== "uv"

    ```sh
    uv add marimo-md-export
    ```

=== "pip"

    ```sh
    pip install marimo-md-export
    ```

    Then manually add `marimo-md-export` to `pyproject.toml`.

## Usage

### Write your notebook

This tool requires marimo notebooks in `.py` format (not `.md`).[^1]

[^1]: Using `.py` format as the notebook source means you can take advantage of Python tooling (linters, type checkers etc.) and `python notebook.py` just works.

Cell outputs are rendered in the export by default.
If a cell produces output you don't want in the export, add `# @suppress` anywhere inside the cell.

If you mark a cell with `@app.cell(hide_code=True)` (as the marimo editor does when you hide a cell's code), its code block is omitted from the export, while its output is still rendered (unless you use `# @suppress`).


### Run the export

`marimo-md-export` is a CLI tool (built with [Typer](https://typer.tiangolo.com/)).

There are two required path-like arguments: the `.py` marimo notebook and the output path.

```sh
marimo-md-export notebook.py output.md
```

Run `marimo-md-export --help` to see all available options.

**Options**

| Flag | Description |
|---|---|
| `--html-output PATH` | If provided, also save the intermediate HTML export to this path |
| `--marimo-args TEXT` | Extra arguments forwarded to `marimo export` (space-separated) |
| `--sandbox`/`--no-sandbox` | Run `marimo export` in an isolated uv environment |
| `--timeout SECONDS` | Maximum seconds to wait for each `marimo export` subprocess (default: no timeout) |
| `--overflow` | Default overflow behavior for long output lines: `wrap` (default) or `scroll`. Can be overridden per cell with `# @scroll` or `# @wrap`. |
| `-v`, `--verbose` | Print progress to stdout |
| `-h`, `--help` | Show help and exit |



### Integrating with documentation sites

`marimo-md-export` is designed to produce markdown pages for static site generators like [mkdocs](https://www.mkdocs.org/) or [zensical](https://zensical.org/).
Both work identically for this purpose.

My suggestion is to add an extra build step that converts your notebook(s) before building the site (and to gitignore the outputs).

For example, this project uses the following [just](https://github.com/casey/just) command to build the docs:

```just
docs:
  marimo-md-export examples/notebook.py docs/example.md
  zensical build
```

This runs `marimo-md-export` to produce a self-contained markdown page (with cell
outputs injected), then builds the site.

## Gotchas

**Existing files are overwritten by default.**

`marimo-md-export` invokes `marimo export` as a subprocess. 
To ensure fully non-interactive operation, `--force` is always passed to `marimo export`, suppressing file-overwrite prompts. 

**Long output lines are a bit awkward.**

By default, long output lines wrap within the container using CSS `white-space: pre-wrap; overflow-wrap: break-word;`.
This keeps everything visible without scrolling but can break custom `__str__` formatting.

Use `--overflow scroll` to switch to horizontal scrolling globally.
This preserves the original formatting exactly but requires users to scroll horizontally for long lines.

You can also override the global default on a per-cell basis by adding `# @scroll` or `# @wrap` anywhere inside the cell (similar to `# @suppress`).
The last marker in a cell wins if both are present.
