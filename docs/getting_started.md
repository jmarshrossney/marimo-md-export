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

Take a look at the [example notebook](https://github.com/jmarshrossney/marimo-md-export/blob/main/examples/notebook.py), or see the [Marimo docs](https://docs.marimo.io/) for guidance.

### Curate what's visible in the export

`marimo-md-export` respects `hide_code`: a cell decorated with `@app.cell(hide_code=True)` (which the marimo editor does when you hide a cell's code) will be omitted from the export, while its outputs are still rendered.

Cell outputs are rendered in the export by default.
If a cell produces output you don't want in the export, add `# @suppress` anywhere inside the cell.
The cell's code block still appears in the markdown.

### Run the export

`marimo-md-export` is a CLI tool.
There are two required path-like arguments: the `.py` marimo notebook and the output path.

```sh
marimo-md-export notebook.py output.md
```

!!! warning "Existing files are overwritten by default."

    To ensure fully non-interactive operation, `--force` is always passed to `marimo export`, suppressing file-overwrite prompts.

Run `marimo-md-export --help`, or see the [CLI reference](cli.md), for all available options.

## Integrating with documentation sites

`marimo-md-export` is designed to produce markdown pages for static site generators like [mkdocs](https://www.mkdocs.org/) or [zensical](https://zensical.org/).

My suggestion is to add an extra build step that converts your notebook(s) before building the site (and to gitignore the outputs).

For example, this project uses the following [just](https://github.com/casey/just) command to build the docs:

```just
docs:
  marimo-md-export examples/notebook.py docs/example.md
  zensical build
```

This runs `marimo-md-export` to produce a markdown page (with cell outputs injected) and its assets directory, then builds the site.

## Assets directory

By default, any auxiliary files are written under `{output_stem}_assets/` beside the markdown file.
This includes the output of `marimo export html` (given `--keep-html`, the default) and any images (given `--no-self-contained`, the default).

For `docs/example.md` that means:

```text
docs/example.md
docs/example_assets/notebook.html
docs/example_assets/figure-1.png
docs/example_assets/figure-2.svg
…
```

