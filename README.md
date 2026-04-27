# marimo-md-export

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
uv sync
just test
just docs
```
