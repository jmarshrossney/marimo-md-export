import marimo

__generated_with = "0.23.3"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd

    return mo, np, pd, plt


@app.cell
def _(np, plt):
    # @output: fig_wave
    x = np.linspace(0, 4 * np.pi, 300)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(x, np.sin(x), label=r"$\sin(x)$")
    ax.plot(x, np.exp(-x / 6) * np.sin(x), label=r"$e^{-x/6}\sin(x)$", ls="--")
    ax.set_xlabel("x")
    ax.legend()
    fig
    return (x,)


@app.cell
def _(np, pd, x):
    # @output: table_summary
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


@app.cell
def _(mo):
    mo.md("""
    ## Interpretation

    The damped sinusoid decays as exp(-x/6), reducing variance by roughly a factor
    of (1 - exp(-2π/3)) per cycle. This notebook serves as a proof of principle
    for `marimo-docs-exporter`.
    """)
    return


if __name__ == "__main__":
    app.run()
