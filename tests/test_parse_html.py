"""Unit tests for parse_html using fixture HTML strings.

Fixtures mimic the structure produced by marimo 0.23.3 without requiring
marimo to be installed or run.
"""

import hashlib
import json

from marimo_md_export.parse_html import extract_outputs


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
        "outputs": [
            {"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}
        ],
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


def _console_cell(code: str, stdout: str, outputs: list | None = None) -> dict:
    return {
        "code_hash": _md5(code.strip()),
        "id": "ddd",
        "console": [{"name": "stdout", "text": stdout}],
        "outputs": outputs or [],
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


def test_console_stdout_extracted():
    code = "# @output: con\nprint('hello')"
    html = _make_html([_console_cell(code, "hello\n")])
    results = extract_outputs(html, {_md5(code.strip())})
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert "<pre>hello\n</pre>" == out.console_html
    assert out.raw_html == ""


def test_console_and_cell_output_combined():
    code = "# @output: both\nprint('hi')\nfig"
    bundle = json.dumps({"image/png": _PNG_DATA})
    cell = _console_cell(
        code,
        "hi\n",
        outputs=[
            {"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}
        ],
    )
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    out = results[_md5(code.strip())]
    assert "<pre>hi\n</pre>" == out.console_html
    assert out.output_type == "figure"
    assert _PNG_DATA in out.raw_html


def test_stderr_ignored():
    code = "# @output: err\nimport sys; print('bad', file=sys.stderr)"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "eee",
        "console": [{"name": "stderr", "text": "bad\n"}],
        "outputs": [],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    assert results == {}


def test_no_session_cells_match():
    html = b"<html><body>no script here</body></html>"
    results = extract_outputs(html, {"deadbeef" * 4})
    assert results == {}


def test_bracket_counting_falls_off_end():
    # Malformed HTML where bracket counting never reaches depth 0
    html = b'<script>{"session": {"cells": [{"code_hash": "abc"}</script>'
    results = extract_outputs(html, {"deadbeef" * 4})
    assert results == {}


def test_marimo_table_not_found():
    code = "# @output: tbl\ndf"
    # HTML that has <marimo-ui-element> but no <marimo-table>
    html_val = "<marimo-ui-element>not a table</marimo-ui-element>"
    import html as html_module

    escaped = html_module.escape(html_val, quote=False)
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "fff",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": escaped}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    # Should return the original HTML unchanged (not classified as table)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "unknown"


def test_table_data_json_decode_error():
    code = "# @output: tbl\ndf"
    # Invalid JSON in data-data
    marimo_table = (
        "<marimo-ui-element>"
        '<marimo-table data-data="invalid json" data-field-types="[]">'
        "</marimo-table></marimo-ui-element>"
    )
    import html as html_module

    escaped = html_module.escape(marimo_table, quote=False)
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "ggg",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": escaped}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    # Should fall back to original HTML
    assert len(results) == 1


def test_field_types_json_decode_error():
    code = "# @output: tbl\ndf"
    rows = [{"col": "a"}]
    data_inner = json.dumps(rows).replace('"__NaN__"', "NaN")
    data_data = json.dumps(data_inner)
    # Invalid field types JSON - should fall back to rows[0].keys()
    # Use single quotes for HTML attributes to match original fixture pattern
    marimo_table = (
        f"<marimo-ui-element>"
        f"<marimo-table data-data='{data_data}' data-field-types='invalid'>"
        f"</marimo-table></marimo-ui-element>"
    )
    import html as html_module

    escaped = html_module.escape(marimo_table, quote=False)
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "hhh",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": escaped}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "table"
    # When field-types fails, it falls back to rows[0].keys() and builds HTML table
    assert "<table" in out.raw_html


def test_marimo_mimebundle_json_decode_error():
    code = "# @output: fig\nfig"
    # Invalid JSON in marimo mimebundle
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "iii",
        "console": [],
        "outputs": [
            {
                "type": "data",
                "data": {"application/vnd.marimo+mimebundle": "invalid json"},
            }
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    # Should not crash; bundle becomes {} and no figure is extracted
    assert results == {}


def test_generic_html_table():
    code = "# @output: tbl\ndf"
    html_val = "<table><tr><th>A</th></tr><tr><td>1</td></tr></table>"
    import html as html_module

    escaped = html_module.escape(html_val, quote=False)
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "jjj",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": escaped}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html, {_md5(code.strip())})
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "table"
    assert "<table" in out.raw_html


def test_cells_json_decode_error():
    # Valid bracket structure but invalid JSON content (trailing comma)
    cells_json = '[{"code_hash": "abc",}]'
    script = f"""
    Object.defineProperty(window, "__MARIMO_MOUNT_CONFIG__", {{
        value: Object.freeze({{
            "session": {{"cells": {cells_json}}}
        }})
    }});
    """
    html_bytes = f"""<!DOCTYPE html><html><head></head><body>
    <script data-marimo="true">{script}</script>
    </body></html>""".encode("utf-8")
    results = extract_outputs(html_bytes, {"deadbeef" * 4})
    assert results == {}


def test_table_html_from_marimo_table_no_marimo_table():
    from marimo_md_export.parse_html import _table_html_from_marimo_table

    # HTML that doesn't contain <marimo-table> element
    result = _table_html_from_marimo_table("<div>not a table</div>")
    assert result == "<div>not a table</div>"
