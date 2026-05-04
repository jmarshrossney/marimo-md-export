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
| `--sandbox`/`--no-sandbox` | Run `marimo export` in an isolated uv environment |
| `--timeout SECONDS` | Maximum seconds to wait for each `marimo export` subprocess (default 120; set to 0 to disable) |
| `-v`, `--verbose` | Print progress to stdout |
| `-h`, `--help` | Show help and exit |

#### Exit codes

| Code | Meaning |
|---|---|
| `0` | Success (warnings may have been emitted to stderr) |
| `1` | `marimo export` failed |
| `2` | No `@output` markers were found in the notebook |

If a marked cell has no matching output in the HTML export, a warning is printed to stderr but the export continues — the unmatched block is left unchanged.

### Subprocess behaviour

`marimo-md-export` invokes `marimo export` as a subprocess. To ensure fully non-interactive operation:

- `--force` is always passed to `marimo export`, suppressing file-overwrite prompts. The intermediate files written by `marimo export` are temporary and deleted after the tool finishes.
- `MPLBACKEND=Agg` is set in the subprocess environment, preventing matplotlib from trying to open an interactive display window (which would hang in a headless context).
- `MARIMO_MANAGE_SCRIPT_METADATA=true` is set, suppressing marimo's sandbox confirmation prompt when a notebook has inline PEP 723 dependencies but `--sandbox` is not requested.
- A timeout (default 120s) prevents the subprocess from hanging indefinitely. If your notebook takes longer, use `--timeout <seconds>` or `--timeout 0` to disable the timeout.

If you need to run `marimo export` interactively (e.g. to respond to prompts), use `marimo export` directly. This tool is designed for automated documentation generation.
