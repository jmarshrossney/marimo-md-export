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
The cell's code block still appears in the markdown — only its rendered output is omitted.

To hide the code instead, mark the cell `@app.cell(hide_code=True)` (as the marimo editor does when you hide a cell's code).
Its code block is then omitted from the export, while its output is still rendered (unless you also use `# @suppress`).

Note that a `mo.md()` cell whose code you don't want to see may not need `hide_code` at all — see [why some `mo.md()` cells show their code](troubleshooting.md#some-momd-cells-show-their-code).


### Run the export

`marimo-md-export` is a CLI tool (built with [Typer](https://typer.tiangolo.com/)).

There are two required path-like arguments: the `.py` marimo notebook and the output path.

```sh
marimo-md-export notebook.py output.md
```

Run `marimo-md-export --help`, or see the [CLI reference](cli.md), for all available options.

### Integrating with documentation sites

`marimo-md-export` is designed to produce markdown pages for static site generators like [mkdocs](https://www.mkdocs.org/) or [zensical](https://zensical.org/).
Both work identically for this purpose.

My suggestion is to add an extra build step that converts your notebook(s) before building the site (and to gitignore the outputs).

For example, this project uses the following [just](https://github.com/casey/just) command to build the docs:

```just
docs:
  marimo-md-export examples/notebook.py docs/example.md --figures-dir figures
  zensical build
```

This runs `marimo-md-export` to produce a markdown page (with cell outputs injected), then builds the site.

`--figures-dir` writes figures out as image files rather than embedding them as base64 data URIs, which keeps the generated page small — see [writing figures to files](cli.md#writing-figures-to-files).
