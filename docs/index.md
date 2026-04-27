# marimo-md-export

## Overview

A `uv` tool that wraps `marimo export`, extracts rendered outputs from the HTML export,
and injects them into the markdown export at positions identified by `# @output: <label>`
markers in cell source. The result is a self-contained markdown document with embedded
figures (as base64 `<img>` tags) and tables (as GFM or HTML tables).

See the [example page](example.md) for output produced by `marimo-md-export` itself,
running the demo notebook included in this repository.

## How it works

1. Runs `marimo export md` to produce a markdown representation of the notebook, with
   cell sources in fenced ` ```python {.marimo} ` blocks.
2. Runs `marimo export html` to produce the fully-rendered HTML (with executed outputs).
3. Finds every cell marked `# @output: <label>` in the markdown export.
4. Matches each marked cell to its rendered output in the HTML export by hashing the
   cell source.
5. Injects each output into the markdown immediately after its code block.

Figures are embedded as base64 `<img>` tags. Tables are converted to GFM markdown
tables where possible, falling back to raw HTML for tables with merged cells.

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

This tool requires marimo notebooks in `.py` format (not `.md`). The `.py` format works
with Python tooling — linters, type checkers, `python notebook.py` — and is the default
format when you create a new marimo notebook.

### Step 1: Mark cells in your notebook

Add a `# @output: <label>` comment inside any cell whose rendered output you want
injected into the export. Labels must be unique within the notebook.

```python
# @output: my_figure
x = np.linspace(0, 4 * np.pi, 300)
fig, ax = plt.subplots()
ax.plot(x, np.sin(x))
fig
```

The marker can appear anywhere inside the cell — it does not need to be the first line,
so you can place it after imports or setup code.

### Step 2: Run the export

```sh
marimo-md-export notebook.py output.md
```

### Options

| Flag | Description |
|---|---|
| `--marimo-args TEXT` | Extra arguments forwarded to `marimo export` (space-separated) |
| `-v`, `--verbose` | Print progress to stdout |
| `-h`, `--help` | Show help and exit |

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (warnings may have been emitted to stderr) |
| `1` | `marimo export` failed |
| `2` | No `@output` markers were found in the notebook |

If a marked cell has no matching output in the HTML export, a warning is printed to
stderr but the export continues — the unmatched block is left unchanged.

## Caveats

**The notebook runs twice.** `marimo export md` and `marimo export html` each execute
the notebook independently. For notebooks with side effects (writing files, network
calls), make sure they are idempotent.

**Embedded figures produce large files.** Figures are stored as base64-encoded PNGs
inline in the markdown. A notebook with many plots can produce a multi-megabyte file.

**Marimo HTML structure may change between versions.** Output extraction relies on
marimo's internal HTML. The tool has been verified against `marimo >= 0.23.3`; a future
release that changes the DOM structure could break extraction silently. Pin your marimo
version if output stability matters.
