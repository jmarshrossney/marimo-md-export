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
#       .type     — "data" or "error"
#       .data     — dict of MIME type → value (for type "data")
#       .ename    — exception class name (for type "error")
#       .evalue   — exception message (for type "error")
#       .traceback — list of traceback lines (for type "error")
#     .console[]
#       .name     — "stdout" or "stderr"
#       .text     — console text content
#
# Supported MIME types:
#   application/vnd.marimo+mimebundle  — JSON string; may contain image/png, image/svg+xml, text/html, text/plain
#   image/*                             — standalone image outputs (png, jpeg, svg+xml, etc.)
#   application/json                    — pretty-printed JSON (dicts, lists, etc.)
#   text/latex                          — LaTeX math (wrapped in $$ delimiters)
#   text/csv                            — CSV data (rendered as code block)
#   text/html                           — may contain <marimo-table> web component
#   text/markdown                       — rendered markdown (text/html output from mo.md)
#   text/plain                          — plain text
#   Unsupported types (vega, jupyter widgets, etc.) produce a placeholder comment.
#
# Tables are stored as <marimo-table data-data='...'> web components.
# `data-data` is a JSON-quoted string of row objects; NaN appears literally.

import ast
import json
import pprint
import re
from html import escape, unescape
from urllib.parse import quote as _url_quote

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

    data_data_attr = elem.get("data-data")
    if not isinstance(data_data_attr, str):
        return marimo_table_html
    data_data = data_data_attr

    field_types_raw_attr = elem.get("data-field-types")
    if isinstance(field_types_raw_attr, str):
        field_types_raw = field_types_raw_attr
    else:
        field_types_raw = "[]"

    try:
        inner = json.loads(data_data)
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


def _html_to_plain_text(html_str: str) -> str:
    """Strip HTML markup from a string, leaving only plain text.

    Used to clean Pygments-highlighted traceback output that marimo includes
    in error-cell stderr entries.
    """
    text = unescape(html_str)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text)


def _format_error(output: dict) -> str:
    """Format an error output as plain text in a <pre> block.

    Error outputs have: ename, evalue, traceback fields.
    The traceback may be None when marimo truncates it.
    """
    ename = output.get("ename", "Error") or "Error"
    evalue = output.get("evalue", "") or ""
    traceback_lines = output.get("traceback") or []
    traceback_text = "\n".join(traceback_lines)
    if traceback_text.strip():
        traceback_text = _html_to_plain_text(traceback_text)
        combined = f"{traceback_text}\n{ename}: {evalue}"
    else:
        combined = f"{ename}: {evalue}"
    return f"<pre>{escape(combined)}</pre>"


_MARIMO_TYPE_RE = re.compile(r"^text/plain(?:\+(\w+))?:(.*)$", re.DOTALL)


def _strip_marimo_type_prefixes(obj: object) -> object:
    """Recursively strip marimo type prefixes from JSON values.

    Marimo encodes typed values as ``"text/plain+float:1.0"`` in
    ``application/json`` output.  This helper converts them back to their
    native Python types so the rendered JSON is clean.
    """
    if isinstance(obj, str):
        m = _MARIMO_TYPE_RE.match(obj)
        if m:
            type_tag, raw = m.group(1), m.group(2)
            if type_tag == "float":
                try:
                    return float(raw)
                except ValueError:
                    return raw
            if type_tag == "int":
                try:
                    return int(raw)
                except ValueError:
                    return raw
            if type_tag == "bool":
                return raw.lower() == "true"
            if type_tag in ("none", "NoneType"):
                return None
            return raw
        return obj
    if isinstance(obj, list):
        return [_strip_marimo_type_prefixes(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _strip_marimo_type_prefixes(v) for k, v in obj.items()}
    return obj


def _classify_and_build(
    data: dict[str, str],
) -> tuple[str, str] | None:
    """Pick one MIME type out of a cell's output and render it.

    ``data`` maps MIME type → value, as marimo stored it in the session JSON.
    A cell can carry several representations of the same result; this walks
    them in a fixed priority order and returns the first that is renderable,
    as ``(output_type, html)``, or ``None`` if none is. The ``output_type`` is
    a label for downstream formatting, not a MIME type. The ``html`` is a
    fragment to write into the markdown, except for ``markdown`` and ``latex``
    where it is the source itself.

    Priority order, first match wins:

    1. ``application/vnd.marimo+mimebundle`` -- marimo's own bundle, holding
       several representations of one object. Its inner keys are searched in
       the order png, svg, html, plain and handled as the standalone types
       below.
    2. ``image/*`` (png, jpeg, gif, svg+xml, tiff, avif, bmp, webp) → an
       ``<img>`` tag. The value is already a data URI, except for a raw SVG,
       which gets wrapped in one. Type ``figure``.
    3. ``application/json`` → pretty-printed with ``pprint`` inside ``<pre>``.
       marimo tags scalars in JSON output as e.g. ``marimo/float:1.5``, so the
       tags are stripped first. Falls back to the raw text if it will not
       parse. Type ``json``.
    4. ``text/latex`` → normalised to a ``$$...$$`` display block, or left as
       inline ``$...$`` if that is how it arrived. Emitted as LaTeX source,
       not HTML. Type ``latex``.
    5. ``text/csv`` → escaped inside ``<pre><code>``. Type ``csv``.
    6. ``text/markdown``, but only when no ``text/html`` accompanies it →
       passed through as markdown source. Under ``MARIMO_NO_JS=true`` a
       ``mo.md()`` cell emits its source here, so taking it ahead of
       ``text/html`` keeps it from being wrapped in ``<pre>``. Type
       ``markdown``.
    7. ``text/html`` → one of three shapes, decided by inspecting the payload:
       a ``<pre>`` wrapper, which marimo uses for a plain value and whose
       content is a Python repr, so the quotes are stripped and the content
       re-escaped (type ``text``); a ``<marimo-table>``, whose JSON payload
       is rebuilt into table markup, or a plain ``<table>`` taken as-is --
       both labelled ``table`` so ``inject`` can turn them into GFM; or
       anything else, passed through verbatim (type ``html``).
    8. ``text/plain`` → escaped inside ``<pre>``, with repr quotes stripped as
       above. Type ``text``.
    9. A known-unrenderable type (vega, vega-lite, jupyter widgets,
       ``text/password``) → an HTML comment naming it, so the gap in the
       document is visible rather than silent. Type ``unsupported``.

    On escaping: marimo stores ``text/html`` and ``text/markdown`` raw, so
    entities in them belong to the payload and must survive to the output.
    The exception is the repr inside a ``<pre>``, which marimo really does
    escape. See the comment on ``decoded`` below.
    """
    bundle_raw = data.get("application/vnd.marimo+mimebundle")
    if bundle_raw:
        if isinstance(bundle_raw, dict):
            bundle = bundle_raw
        else:
            try:
                bundle = json.loads(bundle_raw)
            except json.JSONDecodeError:
                bundle = {}
        for mime_key in ("image/png", "image/svg+xml", "text/html", "text/plain"):
            val = bundle.get(mime_key)
            if val:
                if mime_key.startswith("image/"):
                    if mime_key == "image/svg+xml" and not val.startswith("data:"):
                        val = f"data:image/svg+xml,{_url_quote(val, safe='')}"
                    return (
                        "figure",
                        f'<img src="{escape(val, quote=True)}" alt="{escape(mime_key.split("/")[1], quote=True)}">',
                    )
                if mime_key == "text/html":
                    return "html", val
                if mime_key == "text/plain" and val.strip():
                    return (
                        "text",
                        f"<pre>{escape(val)}</pre>",
                    )

    for mime_type in (
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/svg+xml",
        "image/tiff",
        "image/avif",
        "image/bmp",
        "image/webp",
    ):
        img_val = data.get(mime_type)
        if img_val:
            if mime_type == "image/svg+xml" and not img_val.startswith("data:"):
                img_val = f"data:image/svg+xml,{_url_quote(img_val, safe='')}"
            fmt = mime_type.split("/")[1]
            return (
                "figure",
                f'<img src="{escape(img_val, quote=True)}" alt="{escape(fmt, quote=True)}">',
            )

    json_val = data.get("application/json")
    if json_val:
        try:
            parsed = json.loads(json_val)
            cleaned = _strip_marimo_type_prefixes(parsed)
            formatted = pprint.pformat(cleaned)
        except (json.JSONDecodeError, TypeError):
            formatted = json_val
        return (
            "json",
            f"<pre>{escape(formatted)}</pre>",
        )

    latex_val = data.get("text/latex", "")
    if latex_val and latex_val.strip():
        content = latex_val.strip()
        if content.startswith("$$") and content.endswith("$$"):
            return "latex", content
        if (
            content.startswith("$")
            and content.endswith("$")
            and not content.startswith("$$")
        ):
            return "latex", f"${content[1:-1]}$"
        return "latex", f"$$\n{content}\n$$"

    csv_val = data.get("text/csv", "")
    if csv_val and csv_val.strip():
        return (
            "csv",
            f"<pre><code>{escape(csv_val)}</code></pre>",
        )

    # Because the HTML export runs with MARIMO_NO_JS=true, mo.md() emits its
    # own markdown source here rather than rendered HTML -- including the
    # interpolated values of an f-string. Take it ahead of text/html so it is
    # never wrapped in <pre> or bracket-escaped. Only cells that are genuinely
    # a mo.md() call get passed through verbatim; see inject._format_output.
    md_val = data.get("text/markdown")
    if md_val and not data.get("text/html"):
        return "markdown", md_val

    html_val = data.get("text/html")
    if html_val:
        # marimo stores text/html raw, so any entities in it are the element's
        # own escaping rather than a layer to strip: decoding &#x27; inside a
        # single-quoted attribute closes it early and the rest of the value
        # leaks out of the tag. `decoded` is therefore a view used to classify
        # the payload and to read the content of a <pre>, whose repr marimo
        # really does escape; anything passed through verbatim keeps html_val.
        decoded = unescape(html_val)
        pre_match = re.match(r"<pre[^>]*>(.*?)</pre>", decoded, re.DOTALL)
        if pre_match:
            content = pre_match.group(1)
            if (
                content.startswith(("'", '"'))
                and content.endswith(("'", '"'))
                and len(content) >= 2
            ):
                try:
                    content = ast.literal_eval(content)
                except (ValueError, SyntaxError):
                    pass
                if isinstance(content, str):
                    return (
                        "text",
                        f"<pre>{escape(content)}</pre>",
                    )
            return (
                "text",
                f"<pre>{escape(content)}</pre>",
            )
        if "<marimo-table" in decoded:
            table_html = _table_html_from_marimo_table(decoded)
            return "table", table_html
        if "<table" in decoded:
            return "table", decoded
        return "html", html_val

    plain = data.get("text/plain", "")
    if plain and plain.strip():
        if (
            plain.startswith(("'", '"'))
            and plain.endswith(("'", '"'))
            and len(plain) >= 2
        ):
            try:
                plain = ast.literal_eval(plain)
            except (ValueError, SyntaxError):
                pass
        return (
            "text",
            f"<pre>{escape(plain)}</pre>",
        )

    unsupported = {
        "application/vnd.vega.v5+json",
        "application/vnd.vega.v6+json",
        "application/vnd.vegalite.v5+json",
        "application/vnd.vegalite.v6+json",
        "application/vnd.jupyter.widget-view+json",
        "text/password",
    }
    for mime_type in unsupported:
        if mime_type in data:
            return (
                "unsupported",
                f"<!-- unsupported output type: {escape(mime_type)} -->",
            )

    return None


def extract_outputs(
    html: bytes,
) -> dict[str, ExtractedOutput]:
    """Extract rendered outputs from the marimo HTML export.

    Returns a dict mapping source_hash → ExtractedOutput for each cell
    that has a renderable output. The cell_id is populated from marimo's
    internal cell identifier.

    If a cell has multiple renderable outputs, all are collected and joined
    (in MIME-type priority order). Console output (stdout and stderr) is
    always captured independently.
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

        stderr = "".join(
            c.get("text", "")
            for c in cell.get("console", [])
            if c.get("name") == "stderr"
        )
        stderr = _html_to_plain_text(stderr) if stderr.strip() else ""
        stderr_html = (
            f'<pre class="stderr">{escape(stderr)}</pre>' if stderr.strip() else ""
        )

        media_parts = []
        for c in cell.get("console", []):
            if c.get("type") != "streamMedia":
                continue
            mimetype = c.get("mimetype", "")
            data = c.get("data", "")
            if mimetype.startswith("image/") and data:
                fmt = mimetype.split("/")[1]
                media_parts.append(
                    f'<img src="{escape(data, quote=True)}" alt="{escape(fmt, quote=True)}">'
                )
        media_html = "\n".join(media_parts)

        output_parts: list[tuple[str, str]] = []
        for output in cell.get("outputs", []):
            if output.get("type") == "error":
                error_html = _format_error(output)
                if error_html:
                    output_parts.append(("error", error_html))
                    break
            data = output.get("data", {})
            classified = _classify_and_build(data)
            if classified is None:
                continue
            output_parts.append(classified)

        raw_html = "\n\n".join(html for _, html in output_parts) if output_parts else ""
        output_type = output_parts[0][0] if output_parts else "unknown"

        if not console_html and not stderr_html and not media_html and not raw_html:
            continue

        results[code_hash] = ExtractedOutput(
            raw_html=raw_html,
            output_type=output_type,
            cell_id=cell_id,
            console_html=console_html,
            stderr_html=stderr_html,
            media_html=media_html,
        )

    return results
