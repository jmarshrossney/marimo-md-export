import re

from bs4 import BeautifulSoup

from .models import ExtractedOutput, MarkedCell


def _table_to_gfm(html: str) -> str | None:
    """Convert a plain HTML <table> to GFM markdown, or return None on failure."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        return None

    # Reject tables with merged cells — fall back to HTML
    if table.find(attrs={"colspan": True}) or table.find(attrs={"rowspan": True}):
        return None

    rows: list[list[str]] = []
    for tr in table.find_all("tr"):
        cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
        rows.append(cells)

    if not rows:
        return None

    header = rows[0]
    body = rows[1:]

    # Reject tables with inconsistent row widths — fall back to HTML
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


def _format_output(output: ExtractedOutput) -> str:
    comment = f"<!-- @output:{output.label} -->"

    parts = []
    if output.console_html:
        parts.append(_escape_brackets_in_pre(output.console_html))
    if output.raw_html:
        if output.output_type == "table":
            gfm = _table_to_gfm(output.raw_html)
            parts.append(
                gfm if gfm is not None else _escape_brackets_in_pre(output.raw_html)
            )
        else:
            parts.append(_escape_brackets_in_pre(output.raw_html))

    return comment + "\n\n" + "\n\n".join(parts)


def inject_outputs(
    md: str,
    marked_cells: list[MarkedCell],
    outputs: dict[str, ExtractedOutput],
) -> tuple[str, list[str]]:
    """Inject rendered outputs into the markdown after each marked code block.

    marked_cells should come from collect_marked_cells(md).  outputs maps
    source_hash → ExtractedOutput.  Labels are set from the corresponding
    MarkedCell during injection.

    Returns (result_markdown, warnings) where warnings is a list of
    human-readable messages for outputs that had no matching rendered data.
    """
    result = md
    warnings: list[str] = []
    for cell in marked_cells:
        matched = outputs.get(cell.source_hash)
        if matched is None:
            warnings.append(
                f"no output found for @output:{cell.label} "
                f"(hash {cell.source_hash[:8]})"
            )
            continue

        matched.label = cell.label
        formatted = _format_output(matched)
        result = result.replace(
            cell.block_text, cell.block_text + "\n\n" + formatted, 1
        )

    return result, warnings
