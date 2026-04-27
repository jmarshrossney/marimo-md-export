# marimo-md-export

## Overview

A `uv` tool that wraps `marimo export`, extracts rendered outputs from the HTML export,
and injects them into the markdown export at positions identified by `# @output: <label>`
markers in cell source. The result is a self-contained markdown document with embedded
figures (as base64 `<img>` tags) and tables (as HTML or markdown tables).

This site uses `marimo-md-export` itself to generate example.html (LINK TO PAGE).

To see how to set this up you can just look at the github repo.

## Installation

### As a stand-alone tool

=== "uv"

    ```sh
    uv tool install
    ```

=== "pipx"

    ```sh
    pipx install
    ```

The `marimo-md-export` command should now be available globally on your system.


### As a project dependency

Add to your `pyproject.toml`, e.g. under a `docs` dependency group:

```toml
[dependency-groups]
docs = [
  ...
  marimo-md-export,
  ...
]
```

=== "uv"

    ```sh
    uv add
    ```

=== "pip"

    ```sh
    pip install
    ```

## Usage

This tool assumes your marimo notebooks are in `.py` format.

Note: why not just write them in md from the start? Because `.py` benefits from all the python tooling, e.g. linters, type checkers, and can run with `python notebook.py`.

### In your notebook

Need to add the bespoke marker.

### On the command line

Run the command

```sh
marimo-md-export ...
```


## Caveats

To do.


## Contributing?
