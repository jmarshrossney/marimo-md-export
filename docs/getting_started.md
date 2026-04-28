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

```toml
[dependency-groups]
docs = [
  "marimo-md-export",
]
```

=== "uv"

    ```sh
    uv add --group docs marimo-md-export
    ```

=== "pip"

    ```sh
    pip install marimo-md-export
    ```

## Usage

This tool requires marimo notebooks in `.py` format (not `.md`).[^1]

[^1]: Using `.py` format as the notebook source means you can take advantage of Python tooling (linters, type checkers etc.) and `python notebook.py` just works.

### Step 1: Mark cells in your notebook

Add a `# @output: <label>` comment inside any cell whose rendered output you want injected into the export.
Labels must be unique within the notebook.

```python
# @output: my_figure
x = np.linspace(0, 4 * np.pi, 300)
fig, ax = plt.subplots()
ax.plot(x, np.sin(x))
fig
```

The marker can appear anywhere inside the cell — it does not need to be the first line, so you can place it after imports or setup code.

### Step 2: Run the export

```sh
marimo-md-export notebook.py output.md
```

This is a CLI tool — run `marimo-md-export -h` or `marimo-md-export --help` to see all available options.

#### Options

| Flag | Description |
|---|---|
| `--html-output PATH` | If provided, also save the intermediate HTML export to this path |
| `--marimo-args TEXT` | Extra arguments forwarded to `marimo export` (space-separated) |
| `-v`, `--verbose` | Print progress to stdout |
| `-h`, `--help` | Show help and exit |

#### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (warnings may have been emitted to stderr) |
| `1` | `marimo export` failed |
| `2` | No `@output` markers were found in the notebook |

If a marked cell has no matching output in the HTML export, a warning is printed to stderr but the export continues — the unmatched block is left unchanged.
