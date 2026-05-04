# Marimo HTML export structure (verified against marimo 0.23.3):
#
# The exported HTML is a SPA. Cell outputs are embedded as JSON inside a
# <script> tag that defines `window.__MARIMO_MOUNT_CONFIG__`.  The relevant
# path is:
#
#   __MARIMO_MOUNT_CONFIG__.session.cells[]
#     .code_hash  — MD5 hex digest of cell source (stripped)
#     .id         — marimo's internal cell identifier (e.g. "aaa", "bbb")
#     .outputs[]
#       .type     — "data"
#       .data     — dict of MIME type → value
#
# Supported MIME types:
#   application/vnd.marimo+mimebundle  — JSON string; "image/png" key → figure
#   application/json                   — pretty-printed JSON (dicts, lists, etc.)
#   text/html                          — may contain <marimo-table> web component
#   text/markdown                      — rendered markdown (not captured; already in MD export)
#   text/plain                         — plain text
#
# Tables are stored as <marimo-table data-data='...'> web components.
# `data-data` is a JSON-quoted string of row objects; NaN appears literally.

import json
import re
from html import escape, unescape

from bs4 import BeautifulSoup

from .models import ExtractedOutput

_SESSION_CELLS_RE = re.compile(
    r'"session"\s*:\s*\{"cells"\s*:\s*\[',
)

_decoder = json.JSONDecoder()


def _extract_session_cells_raw(html: bytes) -> str:
    """Return the raw JSON string for session.cells from the HTML.

    Uses json.JSONDecoder.raw_decode to correctly handle brackets inside
    JSON string values.
    """
    text = html.decode("utf-8", errors="replace")
    m = _SESSION_CELLS_RE.search(text)
    if m is None:
        return "[]"

    start = m.end() - 1  # position of the opening '['
    try:
        _, end = _decoder.raw_decode(text, idx=start)
    except json.JSONDecodeError:
        return "[]"

    return text[start:end]


def _table_html_from_marimo_table(marimo_table_html: str) -> str:
    """Convert a <marimo-table> web component to a plain HTML <table>."""
    soup = BeautifulSoup(marimo_table_html, "lxml")
    elem = soup.find("marimo-table")
    if elem is None:
        return marimo_table_html

    # Variable names follow HTML data-* attribute naming (hyphenated → snake_case)
    data_data_attr = elem.get("data-data")
    if not isinstance(data_data_attr, str):
        return marimo_table_html
    data_data = data_data_attr

    field_types_raw_attr = elem.get("data-field-types")
    if isinstance(field_types_raw_attr, str):
        field_types_raw = field_types_raw_attr
    else:
        field_types_raw = "[]"

    # data-data is a JSON-quoted string containing an array of row objects.
    # It may contain literal NaN (not valid JSON). Replace only bare NaN
    # tokens (not inside quoted string values) to avoid clobbering strings
    # like "NaN handling".
    try:
        inner = json.loads(data_data)  # unwrap outer JSON string
        cleaned = re.sub(r'(?<!")\bNaN\b(?!")', "null", inner)
        rows = json.loads(cleaned)
    except (json.JSONDecodeError, AttributeError):
        return marimo_table_html

    try:
        field_types = json.loads(field_types_raw)
        columns = [ft[0] for ft in field_types]
    except (json.JSONDecodeError, IndexError):
        columns = list(rows[0].keys()) if rows else []

    def _cell(v: object) -> str:
        return "" if v is None else escape(str(v))

    header = "".join(f"<th>{escape(str(col))}</th>" for col in columns)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{_cell(row.get(col))}</td>" for col in columns) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{body_rows}</tbody></table>"


def _classify_and_build(data: dict[str, str]) -> tuple[str, str] | None:
    """
    Given the output data dict (MIME → value), return (output_type, raw_html)
    or None if there is nothing renderable.
    """
    # Figure: marimo mimebundle with image/png
    bundle_raw = data.get("application/vnd.marimo+mimebundle")
    if bundle_raw:
        try:
            bundle = json.loads(bundle_raw)
        except json.JSONDecodeError:
            bundle = {}
        src = bundle.get("image/png")
        if src:
            return "figure", f'<img src="{escape(src, quote=True)}" alt="figure">'

    # JSON output (dicts, lists, tuples)
    json_val = data.get("application/json")
    if json_val:
        try:
            parsed = json.loads(json_val)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            formatted = json_val
        return "json", f"<pre><code>{escape(formatted)}</code></pre>"

    # HTML output (may be a marimo-table web component)
    html_val = data.get("text/html")
    if html_val:
        decoded = unescape(html_val)
        if "<marimo-table" in decoded:
            table_html = _table_html_from_marimo_table(decoded)
            return "table", table_html
        # Generic HTML (e.g. styled dataframe rendered as <table>)
        if "<table" in decoded:
            return "table", decoded
        return "unknown", decoded

    plain = data.get("text/plain", "")
    if plain and plain.strip():
        return "text", f"<pre>{escape(plain)}</pre>"

    return None


def extract_outputs(html: bytes) -> dict[str, ExtractedOutput]:
    """Extract rendered outputs from the marimo HTML export.

    Returns a dict mapping source_hash → ExtractedOutput for each cell
    that has a renderable output. The cell_id is populated from marimo's
    internal cell identifier.

    If a cell has multiple outputs, only the first renderable one is used
    (in MIME-type priority order: marimo mimebundle → text/html → text/plain).
    Console output (stdout) is always captured independently.
    """
    cells_raw = _extract_session_cells_raw(html)
    try:
        cells = json.loads(cells_raw)
    except json.JSONDecodeError:
        return {}

    results: dict[str, ExtractedOutput] = {}

    for cell in cells:
        code_hash = cell.get("code_hash")
        cell_id = cell.get("id", "")

        stdout = "".join(
            c.get("text", "")
            for c in cell.get("console", [])
            if c.get("name") == "stdout"
        )
        console_html = f"<pre>{escape(stdout)}</pre>" if stdout.strip() else ""

        raw_html = ""
        output_type = "unknown"
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            classified = _classify_and_build(data)
            if classified is None:
                continue
            output_type, raw_html = classified
            break  # first renderable output per cell wins

        if not console_html and not raw_html:
            continue

        results[code_hash] = ExtractedOutput(
            raw_html=raw_html,
            output_type=output_type,
            cell_id=cell_id,
            console_html=console_html,
        )

    return results
