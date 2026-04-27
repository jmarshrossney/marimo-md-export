"""Unit tests for parse_html using fixture HTML strings.

Fixtures mimic the structure produced by marimo 0.23.3 without requiring
marimo to be installed or run.
"""

import hashlib
import json

import pytest

from marimo_docs_exporter.parse_html import extract_outputs


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def _make_html(cells: list[dict]) -> bytes:
    """Build a minimal marimo-like HTML with session.cells embedded as JSON."""
    cells_json = json.dumps(cells)
    script = f"""
    Object.defineProperty(window, "__MARIMO_MOUNT_CONFIG__", {{
        value: Object.freeze({{
            "session": {{"cells": {cells_json}}}
        }})
    }});
    """
    html = f"""<!DOCTYPE html><html><head></head><body>
    <script data-marimo="true">{script}</script>
    </body></html>"""
    return html.encode("utf-8")


_PNG_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def _figure_cell(code: str) -> dict:
    bundle = json.dumps({"image/png": _PNG_DATA})
    return {
        "code_hash": _md5(code.strip()),
        "id": "aaa",
        "console": [],
        "outputs": [{"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}],
    }


def _table_cell(code: str, rows: list[dict], columns: list[str]) -> dict:
    field_types_json = json.dumps([[col, ["string", "str"]] for col in columns])
    # NaN in table data needs to be a literal (not valid JSON)
    data_inner = json.dumps(rows).replace('"__NaN__"', "NaN")
    data_data = json.dumps(data_inner)  # double-encode as JSON string
    marimo_table = (
        f"<marimo-ui-element>"
        f"<marimo-table data-data='{data_data}' data-field-types='{field_types_json}'>"
        f"</marimo-table></marimo-ui-element>"
    )
    import html as html_module
    escaped = html_module.escape(marimo_table, quote=False)
    return {
        "code_hash": _md5(code.strip()),
        "id": "bbb",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": escaped}}],
    }


def _text_cell(code: str, text: str) -> dict:
    return {
        "code_hash": _md5(code.strip()),
        "id": "ccc",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/plain": text}}],
    }


# ---------------------------------------------------------------------------


def test_figure_extraction():
    code = "# @output: fig\nfig"
    html = _make_html([_figure_cell(code)])
    results = extract_outputs(html, {_md5(code.strip())})
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "figure"
    assert _PNG_DATA in out.raw_html


def test_table_extraction():
    code = "# @output: tbl\ndf"
    rows = [{"col": "a"}, {"col": "b"}]
    html = _make_html([_table_cell(code, rows, ["col"])])
    results = extract_outputs(html, {_md5(code.strip())})
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "table"
    assert "<table" in out.raw_html


def test_text_extraction():
    code = "# @output: txt\nprint('hi')"
    html = _make_html([_text_cell(code, "hello")])
    results = extract_outputs(html, {_md5(code.strip())})
    assert len(results) == 1
    assert results[_md5(code.strip())].output_type == "text"


def test_unmatched_hash_ignored():
    code = "x = 1"
    html = _make_html([_figure_cell(code)])
    results = extract_outputs(html, {"deadbeef" * 4})  # different hash
    assert results == {}


def test_multiple_cells():
    code1 = "# @output: a\nfig1"
    code2 = "# @output: b\nfig2"
    html = _make_html([_figure_cell(code1), _figure_cell(code2)])
    hashes = {_md5(code1.strip()), _md5(code2.strip())}
    results = extract_outputs(html, hashes)
    assert len(results) == 2


def test_no_output_cell_skipped():
    code = "x = 1"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "zzz",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/plain": ""}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    assert results == {}
