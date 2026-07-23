import re

from bs4 import BeautifulSoup

from .models import Cell, ExtractedOutput

_PRE_STYLE_WRAP = "white-space: pre-wrap; overflow-wrap: break-word;"
_PRE_STYLE_SCROLL = "white-space: pre; overflow-x: auto;"

_PRE_STYLE_RE = re.compile(r"<pre\b([^>]*)>")


def _inject_pre_style(html: str, style: str) -> str:
    """Add a style attribute to every <pre> tag in *html*."""
    return _PRE_STYLE_RE.sub(
        lambda m: f'<pre{m.group(1)} style="{style}">',
        html,
    )


def _table_to_gfm(html: str) -> str | None:
    """Convert a plain HTML <table> to GFM markdown, or return None on failure."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return None

    # NOTE: BeautifulSoup 4.15.0's find() overloads have a typing bug: the
    # overload for `find(attrs=dict(...))` is missing a default for `name`,
    # so pyright resolves to the `find(name=None, attrs=None)` overload
    # instead. Remove `# pyright: ignore` once the stubs are fixed upstream.
    if table.find(attrs={"colspan": True}) or table.find(attrs={"rowspan": True}):  # pyright: ignore[reportArgumentType]
        return None

    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        rows.append(cells)

    if not rows:
        return None

    header = rows[0]
    body = rows[1:]

    ncols = len(header)
    if any(len(row) != ncols for row in rows):
        return None

    sep = ["---"] * ncols

    def _row(cells: list[str]) -> str:
        escaped = [c.replace("|", "\\|") for c in cells]
        return "| " + " | ".join(escaped) + " |"

    lines = [_row(header), _row(sep), *(_row(r) for r in body)]
    return "\n".join(lines)


def _escape_brackets(text: str) -> str:
    return text.replace("[", "&#91;").replace("]", "&#93;")


def _escape_brackets_in_pre(html: str) -> str:
    return re.sub(
        r"(<pre[^>]*>)(.*?)(</pre>)",
        lambda m: m.group(1) + _escape_brackets(m.group(2)) + m.group(3),
        html,
        flags=re.DOTALL,
    )


def _escape_brackets_in_html(html: str) -> str:
    return re.sub(
        r">([^<]+)<",
        lambda m: ">" + _escape_brackets(m.group(1)) + "<",
        html,
        flags=re.DOTALL,
    )


def _format_output(output: ExtractedOutput, pre_style: str) -> str:
    comment = f"<!-- @output:{output.cell_id} -->"

    parts = []
    if output.console_html:
        parts.append(
            _escape_brackets_in_pre(_inject_pre_style(output.console_html, pre_style))
        )
    if output.stderr_html:
        parts.append(
            _escape_brackets_in_pre(_inject_pre_style(output.stderr_html, pre_style))
        )
    if output.media_html:
        parts.append(_escape_brackets_in_pre(output.media_html))
    if output.raw_html:
        if output.output_type == "table":
            gfm = _table_to_gfm(output.raw_html)
            parts.append(
                gfm
                if gfm is not None
                else _escape_brackets_in_pre(
                    _inject_pre_style(output.raw_html, pre_style)
                )
            )
        elif output.output_type in ("html", "figure"):
            parts.append(_escape_brackets_in_html(output.raw_html))
        else:
            parts.append(
                _escape_brackets_in_pre(_inject_pre_style(output.raw_html, pre_style))
            )

    return comment + "\n\n" + "\n\n".join(parts)


def inject_outputs(
    md: str,
    cells: list[Cell],
    outputs: dict[str, ExtractedOutput],
    default_pre_style: str = _PRE_STYLE_WRAP,
) -> tuple[str, list[str]]:
    """Inject rendered outputs into the markdown after each code block.

    cells should come from collect_cells(md).  outputs maps
    source_hash → ExtractedOutput.  Cell IDs from the HTML export are used
    as labels in the output anchor comments.

    default_pre_style is applied to all cells unless overridden by a
    cell-level overflow marker (# @scroll / # @wrap).

    Returns (result_markdown, warnings) where warnings is a list of
    human-readable messages.
    """
    result = md
    warnings: list[str] = []
    for cell in cells:
        if cell.suppressed:
            if cell.hide_code:
                result = result.replace(cell.block_text, "", 1)
            continue

        matched = outputs.get(cell.source_hash)
        if matched is None:
            if cell.hide_code:
                # No output matched: the cell either genuinely produces none
                # (e.g. an imports/assignment cell — the common case) or its
                # hash somehow failed to match. Indistinguishable here. A
                # hidden cell with no code and no output is nothing to show, so
                # remove it.
                result = result.replace(cell.block_text, "", 1)
            continue

        pre_style = (
            _PRE_STYLE_SCROLL
            if cell.overflow == "scroll"
            else _PRE_STYLE_WRAP
            if cell.overflow == "wrap"
            else default_pre_style
        )
        formatted = _format_output(matched, pre_style)
        if cell.hide_code:
            result = result.replace(cell.block_text, formatted, 1)
        else:
            result = result.replace(
                cell.block_text, cell.block_text + "\n\n" + formatted, 1
            )

    # Collapse blank-line residue left by removed blocks. Injected output is
    # separated by exactly "\n\n", so this never merges distinct blocks.
    result = re.sub(r"\n{3,}", "\n\n", result)

    return result, warnings
