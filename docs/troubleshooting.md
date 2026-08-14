# Troubleshooting

## Some `mo.md()` cells show their code

"Normal" `mo.md("""...""")` cells are converted directly to markdown.
However, cells of the form `mo.md(f"""...{value}...""")` leave a visible ` ```python {.marimo}` block in the exported markdown, with the exported content underneath.

This is due to behaviour of `marimo export md`, i.e. marimo itself, not `marimo-md-export`.
When marimo writes the markdown export it tries to read the text of each `mo.md()` call straight out of the source, without running the notebook.
That only works for cells that

1. Comprise a single bare `mo.md(...)` statement
2. Depend on `mo` and nothing else
3. Don't define any variables
4. Contain a single string literal

Any cells that don't satisfy these conditions are left as code blocks.
This includes some common cases: 

- f-strings with variable interpolation
- cells that compute a value before calling `mo.md()`

If this is undesirable, the code cell can be hidden using `hide_code=True`.

## Math is broken for `mo.md()` inside a layout helper

When `mo.md()` is nested inside a layout helper such as `mo.hstack`, `mo.vstack` or `mo.accordion`, the cell's output is the *layout*, not markdown, and it gets injected into the exported markdown document as HTML.

For docs sites this HTML should render nicely, so this isn't really a problem unless you're viewing the exported markdown using a tool that doesn't render HTML.

The main issue I've encountered in such cases is that **math gets wrapped in `<marimo-tex>` tags with non-standard delimiters**, e.g.

```html
<div style='display: flex;...'><span class="markdown prose dark:prose-invert contents"><span
class="paragraph">nested: <marimo-tex class="arithmatex">||(\beta_{42}||)</marimo-tex></span></span></div>
```

This fails to render unless you register the necessary delimiters with your math renderer.
E.g. for this Zensical site I add the following:

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

See the [Zensical docs](https://zensical.org/docs/authoring/math/) for further guidance.

## LaTeX braces inside f-strings

In an f-string, `{` and `}` are interpolation syntax, so LaTeX braces need to be doubled:

```python
x = 42

mo.md(rf"""
Wrong:   $\sigma_{x}$      renders as \sigma_42
Right:   $\sigma_{{x}}$    renders as \sigma_x
""")
```

A single `{x}` interpolates the variable rather than producing a LaTeX group, so you usually get valid-but-wrong math rather than an error.

## Interactive elements don't get exported

As of version 0.10.0, `marimo-md-export` runs the HTML export with `MARIMO_NO_JS=true`, so marimo renders outputs as it would for a viewer with no JavaScript.
This change was made so that `mo.md` cells behave better, emitting markdown in almost all cases rather than HTML that needed to be handled separately in common cases like f-strings.

The problem with this is that if your static docs page includes a link to the export HTML notebook, you might want that to contain the dynamic components.
If this affects you, feel free to open an issue.

