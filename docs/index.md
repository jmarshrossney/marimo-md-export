# Home

## What this is

A tool that wraps `marimo export`, extracts rendered outputs from the HTML export, and injects them into the markdown export at positions identified by `# @output: <label>` markers in cell source.
The result is a self-contained markdown document with embedded figures (as base64 `<img>` tags) and tables (as GFM or HTML tables).

See the [example page](example.md) for output produced by `marimo-md-export` itself, running the demo notebook included in this repository.

## Motivations

Marimo supports markdown representations of notebooks (e.g. through `marimo export md`), which can be integrated into markdown-based static site generators like [`mkdocs`](https://www.mkdocs.org/) or [`zensical`](https://zensical.org/).
However, the markdown representation doesn't include cell outputs such as plots, tables etc.[^1]

[^1]: 
    Of course, you could use the HTML representation (`marimo export html`) directly in the site, but you'll lose the layout (e.g. header, navigation, side-bar, footer) and theming (colours, fonts).
    You could also embed the HTML in an iframe but it looks shite.

Essentially, `marimo-md-export` is a **stop-gap solution** for me to easily integrate marimo notebooks into zensical documentation, up until the plugin system in zensical matures and/or tools like [`mkdocs-marimo`](https://marimo-team.github.io/mkdocs-marimo/) support this out of the box.

## How it works

1. Runs `marimo export md` to produce a markdown representation of the notebook (_without_ rendered outputs!), with cell sources in fenced ` ```python {.marimo} ` blocks.
2. Runs `marimo export html` to produce the fully-rendered HTML (with executed outputs).
3. Finds every cell marked `# @output: <label>` in the markdown export.
4. Matches each marked cell to its rendered output in the HTML export by hashing the cell source.
5. Injects each output into the markdown immediately after its code block.

Figures are embedded as base64 `<img>` tags. 
Tables are converted to GFM markdown tables where possible, falling back to raw HTML for tables with merged cells.

## Caveats

**Embedded figures produce large files.** 
Figures are stored as base64-encoded PNGs inline in the markdown. A notebook with many plots can produce a multi-megabyte file.

**Marimo HTML structure may change between versions.** 
Output extraction relies on marimo's internal HTML. 
The tool has been verified against `marimo >= 0.23.3`; a future release that changes the DOM structure could break extraction silently.

