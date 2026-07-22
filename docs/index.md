# Home

## What this is

A tool that wraps [`marimo export`](https://docs.marimo.io/guides/exporting/), extracts rendered outputs from the HTML export, and injects them into the markdown export for every cell. 
The result is a self-contained markdown document with embedded figures, tables, console output, and other outputs.

See the [example page](example.md) for output produced by `marimo-md-export` itself, running the demo notebook included in this repository.

## Motivations

Marimo supports markdown representations of notebooks (e.g. through `marimo export md`), which can be integrated into markdown-based static site generators like [`mkdocs`](https://www.mkdocs.org/) or [`zensical`](https://zensical.org/).
However, the markdown representation doesn't include cell outputs such as plots, tables, console output, errors, etc.[^1]

[^1]: 
    Of course, you could use the HTML representation (`marimo export html`) directly in the site, but you'll lose the layout (e.g. header, navigation, side-bar, footer) and theming (colours, fonts).
    You could also embed the HTML in an iframe but it looks shite.

Essentially, `marimo-md-export` is a **stop-gap solution** for me to easily integrate marimo notebooks into zensical documentation, up until the plugin system in zensical matures and/or tools like [`mkdocs-marimo`](https://marimo-team.github.io/mkdocs-marimo/) support this out of the box.

## How it works

1. Runs `marimo export md` to produce a markdown representation of the notebook (_without_ rendered outputs!), with cell sources in fenced ` ```python {.marimo}` blocks.
2. Runs `marimo export html` to produce the fully-rendered HTML (with executed outputs).
3. Collects all fenced code blocks from the markdown export.
4. Matches each cell to its rendered output in the HTML export by hashing the cell source.
5. Injects each output into the markdown immediately after its code block, labelled with the cell's marimo ID.

Different cell outputs are handled as follows:

- Figures are embedded as base64 `<img>` tags.
- Tables are converted to GFM markdown tables where possible, falling back to raw HTML for tables with merged cells.
- Console output (stdout and stderr) is captured and rendered as `<pre>` blocks.
- JSON values (dicts, lists) are pretty-printed in code blocks, with marimo type prefixes stripped.
- Error outputs are rendered as plain-text `<pre>` blocks with the traceback and exception message.
- SVG graphics and other HTML outputs are passed through as-is.
- Unsupported output types (vega, jupyter widgets, etc.) produce placeholder comments.
- The outputs of any cells marked with `# @suppress` are ignored (but the cell itself still appears).

The [example page](example.md) shows how these look in practice.

## Caveats

**Embedded figures produce large files.**

Figures are stored as base64-encoded PNGs inline in the markdown.
A notebook with many plots can produce a multi-megabyte file.

Some suggestions:

- Do not commit generated notebooks to source control; instead, generate them in the documentation workflow.
- Consider using `# @suppress` in cells whose outputs you don't need.

**Some output types are not fully supported.**

Vega charts, Jupyter widgets, and other rich outputs cannot be rendered in static markdown.
These produce a placeholder comment (e.g. `<!-- unsupported output type: application/vnd.vega.v5+json -->`).

**Some outputs just look bad.**

Not everything renders nicely, sorry.
Some things might reasonably be improved through further development of this tool, but for very complex outputs you might just consider providing a link to the full HTML version of the marimo notebook for viewing the full interactive output.
