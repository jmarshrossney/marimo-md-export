# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo",
#     "matplotlib==3.10.9",
#     "numpy==2.4.4",
#     "pandas==3.0.2",
# ]
# ///

import marimo

__generated_with = "0.23.3"
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
    ## List and dict outputs

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
    ## Standard error

    Output written to `sys.stderr` is captured separately from stdout.
    """)
    return


@app.cell
def _(sys, x):
    sys.stderr.write(f"Warning: computing over {len(x)} points\n")
    "stderr demo"
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
    ## Suppressed output

    Adding `# @suppress` to a cell prevents its output from appearing in the exported markdown.
    """)
    return


@app.cell
def _(np, x):
    # @suppress
    intermediate = np.sum(x)
    intermediate
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Long line outputs

    These cells produce outputs with very long single lines to test line wrapping.
    """)
    return


@app.cell
def _():
    from collections import OrderedDict

    d = OrderedDict(
        [
            ("very_long_key_name_number_one", "value_one"),
            ("very_long_key_name_number_two", "value_two"),
            ("very_long_key_name_number_three", "value_three"),
            ("very_long_key_name_number_four", "value_four"),
            ("very_long_key_name_number_five", "value_five"),
        ]
    )
    print(d)
    d.keys()
    return


@app.cell
def _():
    import warnings

    warnings.warn(
        "This is a very long warning message that spans well beyond the typical "
        "line length limit of 79 characters and should be wrapped properly when "
        "exported to markdown with the --line-width option configured"
    )
    "warning demo"
    return


if __name__ == "__main__":
    app.run()
