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

Add to your `pyproject.toml`, for example under a `docs` dependency group:

=== "uv"

    ```sh
    uv add --group docs marimo-md-export
    ```

=== "pip"

    ```sh
    pip install marimo-md-export
    ```

    Then manually add `marimo-md-export` to `pyproject.toml`.

    ```toml
    [dependency-groups]
    docs = [
      "marimo-md-export",
    ]
    ```

## Usage

This tool requires marimo notebooks in `.py` format (not `.md`).[^1]

[^1]: Using `.py` format as the notebook source means you can take advantage of Python tooling (linters, type checkers etc.) and `python notebook.py` just works.

### Step 1: Write your notebook

Cell outputs are rendered in the export by default. No special comments are needed.

```python
x = np.linspace(0, 4 * np.pi, 300)
fig, ax = plt.subplots()
ax.plot(x, np.sin(x))
fig
```

### Step 2: Suppress unwanted outputs (optional)

If a cell produces output you don't want in the export, add `# @suppress` anywhere inside the cell:

```python
# @suppress
import numpy as np
import matplotlib.pyplot as plt
```

### Step 3: Run the export

```sh
marimo-md-export notebook.py output.md
```

This is a CLI tool — run `marimo-md-export -h` or `marimo-md-export --help` to see all available options.

**Options**

| Flag | Description |
|---|---|
| `--html-output PATH` | If provided, also save the intermediate HTML export to this path |
| `--marimo-args TEXT` | Extra arguments forwarded to `marimo export` (space-separated) |
| `--sandbox`/`--no-sandbox` | Run `marimo export` in an isolated uv environment |
| `--timeout SECONDS` | Maximum seconds to wait for each `marimo export` subprocess (default: no timeout) |
| `-v`, `--verbose` | Print progress to stdout |
| `-h`, `--help` | Show help and exit |



## Gotchas

**Existing files are overwritten by default.**

`marimo-md-export` invokes `marimo export` as a subprocess. 
To ensure fully non-interactive operation, `--force` is always passed to `marimo export`, suppressing file-overwrite prompts. 
