# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "matplotlib==3.10.9",
#     "numpy==2.4.4",
#     "pandas==3.0.2",
#     "graphviz",
# ]
# ///

import marimo

__generated_with = "0.23.5"
app = marimo.App(app_title="Example notebook")


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Example notebook

    This notebook serves as a proof of principle for `marimo-md-export`.

    You can view the original notebook at [`examples/notebook.py`](https://github.com/jmarshrossney/marimo-md-export/examples/notebook.py).
    The command used to convert it to a docs page is the `just docs` command in [`justfile`](https://github.com/jmarshrossney/marimo-md-export/justfile).
    """)
    return


@app.cell(hide_code=True)
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import sys

    return mo, np, pd, plt, sys


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Figures
    """)
    return


@app.cell
def _(np, plt):
    x = np.linspace(0, 4 * np.pi, 300)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(x, np.sin(x), label=r"$\sin(x)$")
    ax.plot(x, np.exp(-x / 6) * np.sin(x), label=r"$e^{-x/6}\sin(x)$", ls="--")
    ax.set_xlabel("x")
    ax.legend()
    fig
    return (x,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Tables
    """)
    return


@app.cell
def _(np, pd, x):
    df = pd.DataFrame(
        {
            "Quantity": ["Mean", "Variance", "Skewness"],
            "sin(x)": [0.0, 0.5, 0.0],
            "damped": [
                round(float(np.mean(np.exp(-x / 6) * np.sin(x))), 4),
                round(float(np.var(np.exp(-x / 6) * np.sin(x))), 4),
                None,
            ],
        }
    )
    df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Console output
    """)
    return


@app.cell
def _(np, x):
    print(f"Number of points: {len(x)}")
    print(f"x range: [{x[0]:.4f}, {x[-1]:.4f}]")
    print(f"Mean of sin(x): {np.mean(np.sin(x)):.6f}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## String output

    Returning a string from a cell preserves escape sequences like `
    ` as actual
    newlines in the exported markdown.
    """)
    return


@app.cell
def _():
    "Line one\nLine two\nLine three"
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Dynamic markdown

    `mo.md()` with f-strings embeds computed values into rendered markdown.
    This is distinct from plain `print()` or returning a string — the output
    is styled as markdown (bold, italics, headers) rather than preformatted
    text.
    """)
    return


@app.cell
def _(mo, np):
    pi_hat = 4 * np.sum(1 / (1 + ((np.arange(1, 10001) - 0.5) / 10000) ** 2)) / 10000
    mo.md(
        f"Estimate: **{pi_hat:.10f}**  \n"
        f"True π:   **{np.pi:.10f}**  \n"
        f"Error:    {abs(pi_hat - np.pi):.2e}"
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    This also works inside fenced code blocks.
    For example,

    ````python
    mo.md(f'''
    ```python
    n_points = {len(x)}
    ```
    ''')
    ````

    becomes
    """)
    return


@app.cell(hide_code=True)
def _(mo, x):
    mo.md(f"""
    ```python
    n_points = {len(x)}
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    /// note | LaTeX math in f-strings
    With f-string interpolation, inline math is exported as `<marimo-tex>`
    with `||(` and `||)` delimiters instead of `$...$`. Register these in
    your KaTeX or MathJax configuration:

    === "KaTeX"

        ```js
        renderMathInElement(body, {
          delimiters: [
            { left: "$$",  right: "$$",  display: true },
            { left: "$",   right: "$",   display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true },
            { left: "||(", right: "||)", display: false },   // <-- new
          ],
        })
        ```

    === "MathJax"

        ```js
        window.MathJax = {
          tex: {
            inlineMath: [["\\(", "\\)"], ["||(", "||)"]],   // <-- new
            displayMath: [["\\[", "\\]"]],
            processEscapes: true,
            processEnvironments: true
          },
          options: {
            ignoreHtmlClass: ".*|",
            processHtmlClass: "arithmatex"
          }
        };
        ```

    See the [Zensical docs](https://zensical.org/docs/authoring/math/) for further guidance.
    ///
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## JSON outputs

    Returning a dict or list from a cell produces a Python-style formatted output
    using `pprint`.
    """)
    return


@app.cell
def _():
    {"name": "damped sinusoid", "amplitude": 1.0, "decay_rate": 0.167}
    return


@app.cell
def _(x):
    [round(float(xi), 4) for xi in x[:5]]
    return


@app.cell
def _():
    {
        "experiment": "damped sinusoid",
        "parameters": {
            "amplitude": 1.0,
            "decay_rate": 0.167,
            "frequency": 1.0,
        },
        "results": {
            "samples": 300,
            "range": [0.0, 12.5664],
            "statistics": {
                "mean": 0.0,
                "variance": 0.5,
                "converged": True,
            },
        },
        "tags": ["oscillation", "damping", "physics"],
    }
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Errors

    Cells that raise exceptions produce error output with traceback.
    """)
    return


@app.cell
def _():
    raise ValueError("This cell demonstrates error output handling")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Output written to `sys.stderr` is captured separately from stdout.
    """)
    return


@app.cell
def _(sys, x):
    sys.stderr.write(f"Warning: computing over {len(x)} points\n")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## SVG graphics

    Inline SVG rendered via `mo.Html`.
    """)
    return


@app.cell
def _(mo):
    mo.Html("""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100">
    <rect x="5" y="5" width="190" height="90" fill="#4a9eff" rx="10"/>
    <text x="100" y="55" text-anchor="middle" fill="white" font-size="14">SVG Image</text>
    </svg>""")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Graphviz graphs

    Graphs created with the `graphviz` package render as SVG and display
    correctly in the exported markdown.
    """)
    return


@app.cell
def _():
    from graphviz import Digraph

    dot = Digraph()
    dot.node("A", "Start")
    dot.node("B", "Process")
    dot.node("C", "End")
    dot.edges(["AB", "BC"])
    dot
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Mermaid diagrams

    Mermaid code fences inside `mo.md()` cells pass through to the exported
    markdown and render on platforms with mermaid support (GitHub, MkDocs with
    pymdownx, etc.).
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ````
    ```mermaid
    graph TD
        A[Start] --> B[Process]
        B --> C[End]
    ```
    ````

    ```mermaid
    graph TD
        A[Start] --> B[Process]
        B --> C[End]
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Admonitions

    Marimo admonitions using the `/// type | title` syntax are automatically
    converted to MkDocs/Zensical-compatible `!!! type "title"` format during
    export.
    """)
    return


@app.cell
def _(mo):
    # NOTE: The adminitions enclosed in backticks are supposed to show what the source looks
    # like to the user, but they are also converted to Zensical !!! syntax in the rendered
    # docs - quite confusing.
    mo.md("""
    ```
    /// note | Important Information
    This is a note admonition. It supports **bold**, *italic*, and other
    markdown formatting inside the block.
    ///
    ```

    /// note | Important Information
    This is a note admonition. It supports **bold**, *italic*, and other
    markdown formatting inside the block.
    ///

    ```
    /// tip
    Admonitions without a title also work — the title is simply omitted.
    ///
    ```

    /// tip
    Admonitions without a title also work — the title is simply omitted.
    ///
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Multiple outputs

    A cell with both console output and an expression result.
    """)
    return


@app.cell
def _(np, x):
    print(f"Computing statistics for {len(x)} points...")
    np.mean(np.sin(x))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Long line outputs

    This cell produces output with very long lines to demonstrate overflow wrapping.
    """)
    return


@app.cell
def _():
    print(
        "A very long line that exceeds the typical container width, stretching well beyond what fits on a single line. In this case the text should scroll, not wrap! "
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    You can pass `--overflow scroll` to the CLI to switch the global behaviour from wrapping to scrolling.
    Note, however, that JSON outputs (lists, dicts, tuples) won't be affected by this.

    You can also control overflow on a per-cell basis.

    Add `# @scroll` to a cell to force horizontal scrolling for its output, regardless of the global `--overflow` setting.
    """)
    return


@app.cell
def _():
    # @scroll
    print(
        "A very long line that exceeds the typical container width, stretching well beyond what fits on a single line. In this case the text should scroll, not wrap! "
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Hiding code

    Marking a cell with `@app.cell(hide_code=True)` (as the marimo editor does when you hide a cell's code) omits its code block from the export while still rendering its output.

    The cell below is annotated with `hide_code=True`, so only its output — a figure — appears:
    """)
    return


@app.cell(hide_code=True)
def _(np, plt, x):
    _fig, _ax = plt.subplots(figsize=(7, 3))
    _ax.plot(x, np.cos(x), color="tab:green")
    _ax.set_xlabel("x")
    _ax.set_title(r"$\cos(x)$")
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Suppressing outputs

    Adding `# @suppress` to a cell prevents its output from appearing in the exported markdown.
    """)
    return


@app.cell
def _():
    # @suppress
    print("This is just for debugging - no need to include in the docs!")
    return


if __name__ == "__main__":
    app.run()
