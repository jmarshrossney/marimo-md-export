from bs4 import BeautifulSoup

from .models import Cell, ExtractedOutput


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


def _format_output(output: ExtractedOutput) -> str:
    comment = f"<!-- @output:{output.cell_id} -->"

    parts = []
    if output.console_html:
        parts.append(output.console_html)
    if output.stderr_html:
        parts.append(output.stderr_html)
    if output.raw_html:
        if output.output_type == "table":
            gfm = _table_to_gfm(output.raw_html)
            parts.append(gfm if gfm is not None else output.raw_html)
        elif output.output_type == "error":
            parts.append(f'<div class="error">\n{output.raw_html}\n</div>')
        else:
            parts.append(output.raw_html)

    return comment + "\n\n" + "\n\n".join(parts)


def inject_outputs(
    md: str,
    cells: list[Cell],
    outputs: dict[str, ExtractedOutput],
) -> tuple[str, list[str]]:
    """Inject rendered outputs into the markdown after each code block.

    cells should come from collect_cells(md).  outputs maps
    source_hash → ExtractedOutput.  Cell IDs from the HTML export are used
    as labels in the output anchor comments.

    Returns (result_markdown, warnings) where warnings is a list of
    human-readable messages.
    """
    result = md
    warnings: list[str] = []
    for cell in cells:
        if cell.suppressed:
            continue
        matched = outputs.get(cell.source_hash)
        if matched is None:
            # No renderable output — expected for import/setup cells
            continue

        formatted = _format_output(matched)
        result = result.replace(
            cell.block_text, cell.block_text + "\n\n" + formatted, 1
        )

    return result, warnings
