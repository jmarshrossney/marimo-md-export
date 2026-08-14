# Troubleshooting

## Why some `mo.md()` cells show their code

A `mo.md("""...""")` cell usually disappears into the page, leaving only its prose.
A cell like `mo.md(f"""...{value}...""")` instead leaves a visible ` ```python {.marimo}` block, with the prose underneath it.

This is decided by `marimo export md`, upstream of this tool.
When marimo writes the markdown export it tries to read the text of each `mo.md()` call straight out of the source, without running the notebook.
That only works when the cell references nothing but `mo` and the argument is a single string literal.
An f-string with interpolation fails both tests, so marimo leaves the cell as a code block, and `marimo-md-export` appends the rendered output after it.

The trigger is **interpolation**, not the string prefix — `r"""`, `f"""` and `rf"""` all inline fine as long as there are no `{...}` placeholders.

Either way the prose itself comes through as plain markdown, math included.
To hide the code block as well, mark the cell `@app.cell(hide_code=True)`; see [Write your notebook](getting_started.md#write-your-notebook).

## `mo.md()` inside a layout helper renders as HTML

When `mo.md()` is nested inside a layout helper such as `mo.hstack`, `mo.vstack` or `mo.accordion`, the cell's output is the *layout*, not markdown.
It is injected as HTML, and any math inside it is wrapped in `<marimo-tex>` tags with non-standard delimiters:

```html
<div style='display: flex;...'><span class="markdown prose dark:prose-invert contents"><span
class="paragraph">nested: <marimo-tex class="arithmatex">||(\beta_{42}||)</marimo-tex></span></span></div>
```

The simplest fix is to hoist the markdown into its own cell, so it is a bare `mo.md(...)` call.
Assigning it to a name first is also fine — `body = mo.md(f"""...""")` followed by `body` still exports as plain markdown.

If you need the layout, register the delimiters with your math renderer.
Inline math uses `||(` and `||)`; display math uses `||[` and `||]`.

=== "KaTeX"

    ```js
    renderMathInElement(body, {
      delimiters: [
        { left: "$$",  right: "$$",  display: true },
        { left: "$",   right: "$",   display: false },
        { left: "||(", right: "||)", display: false },
        { left: "||[", right: "||]", display: true },
      ],
    })
    ```

=== "MathJax"

    ```js
    window.MathJax = {
      tex: {
        inlineMath: [["\\(", "\\)"], ["||(", "||)"]],
        displayMath: [["\\[", "\\]"], ["||[", "||]"]],
        processEscapes: true,
        processEnvironments: true
      },
      options: {
        ignoreHtmlClass: ".*|",
        processHtmlClass: "arithmatex"
      }
    };
    ```

The square brackets appear HTML-escaped in the markdown, as `||&#91;` and `||&#93;`, because brackets inside injected HTML are escaped so they aren't mistaken for link syntax.
A browser decodes them before the math renderer sees them.

See the [Zensical docs](https://zensical.org/docs/authoring/math/) for further guidance.

## LaTeX braces inside f-strings

In an f-string, `{` and `}` are interpolation syntax, so LaTeX braces must be doubled:

```python
x = 42

mo.md(rf"""
Wrong:   $\sigma_{x}$      renders as \sigma_42
Right:   $\sigma_{{x}}$    renders as \sigma_x
""")
```

A single `{x}` silently interpolates the variable rather than producing a LaTeX group, so you usually get valid-but-wrong math rather than an error.

## Interactive elements don't survive

The HTML export is run with `MARIMO_NO_JS=true`, so marimo renders outputs as it would for a viewer with no JavaScript.
That is what lets `mo.md()` emit real markdown, but it also means interactive elements have no interactive form to fall back on:

- `mo.ui.slider` and friends produce inert markup — there is no way to make them work in a static page.
- `mo.ui.table` renders as a static table. A DataFrame becomes a GFM table; other data (a list of dicts, say) falls back to a plain `repr`.

For genuinely interactive content, link out to the full HTML export of the notebook.

## Other output types

For figure sizes, unsupported rich outputs, and long output lines, see the [Caveats](index.md#caveats) on the home page and the [Gotchas](getting_started.md#gotchas) in Getting Started.
