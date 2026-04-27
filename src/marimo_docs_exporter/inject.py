import re
import sys
import warnings

from bs4 import BeautifulSoup

from marimo_docs_exporter.models import ExtractedOutput, MarkedCell
from marimo_docs_exporter.parse_md import collect_marked_cells


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
    sep = ["---"] * len(header)

    def _row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    lines = [_row(header), _row(sep), *(_row(r) for r in body)]
    return "\n".join(lines)


def _format_output(output: ExtractedOutput) -> str:
    comment = f"<!-- @output:{output.label} -->"
    if output.output_type == "figure":
        return f"{comment}\n\n{output.raw_html}"
    if output.output_type == "table":
        gfm = _table_to_gfm(output.raw_html)
        if gfm is not None:
            return f"{comment}\n\n{gfm}"
        return f"{comment}\n\n{output.raw_html}"
    if output.output_type == "text":
        return f"{comment}\n\n{output.raw_html}"
    return f"{comment}\n\n{output.raw_html}"


def inject_outputs(
    md: str,
    outputs: dict[str, ExtractedOutput],
) -> str:
    """Inject rendered outputs into the markdown after each marked code block.

    `outputs` maps source_hash → ExtractedOutput (label field will be updated
    to the human-readable label from the @output marker).
    """
    marked_cells: list[MarkedCell] = collect_marked_cells(md)

    result = md
    for cell in marked_cells:
        matched = outputs.get(cell.source_hash)
        if matched is None:
            warnings.warn(
                f"WARNING: no output found for @output:{cell.label} "
                f"(hash {cell.source_hash[:8]})",
                stacklevel=2,
            )
            print(
                f"WARNING: no output found for @output:{cell.label}",
                file=sys.stderr,
            )
            continue

        matched.label = cell.label
        formatted = _format_output(matched)
        result = result.replace(cell.block_text, cell.block_text + "\n\n" + formatted, 1)

    return result
