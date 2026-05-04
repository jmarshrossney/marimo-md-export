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


def _data_cell(code: str, mime_type: str, value: str) -> dict:
    return {
        "code_hash": _md5(code.strip()),
        "id": "zzz",
        "console": [],
        "outputs": [{"type": "data", "data": {mime_type: value}}],
    }


def _json_cell(code: str, obj: object) -> dict:
    return {
        "code_hash": _md5(code.strip()),
        "id": "eee",
        "console": [],
        "outputs": [{"type": "data", "data": {"application/json": json.dumps(obj)}}],
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
    code = "fig"
    html = _make_html([_figure_cell(code)])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "figure"
    assert _PNG_DATA in out.raw_html


def test_table_extraction():
    code = "df"
    rows = [{"col": "a"}, {"col": "b"}]
    html = _make_html([_table_cell(code, rows, ["col"])])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "table"
    assert "<table" in out.raw_html


def test_text_extraction():
    code = "print('hi')"
    html = _make_html([_text_cell(code, "hello")])
    results = extract_outputs(html)
    assert len(results) == 1
    assert results[_md5(code.strip())].output_type == "text"


def test_multiple_cells():
    code1 = "fig1"
    code2 = "fig2"
    html = _make_html([_figure_cell(code1), _figure_cell(code2)])
    results = extract_outputs(html)
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
    results = extract_outputs(html)
    assert results == {}


def test_console_stdout_extracted():
    code = "print('hello')"
    html = _make_html([_console_cell(code, "hello\n")])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert "<pre>hello\n</pre>" == out.console_html
    assert out.raw_html == ""


def test_console_and_cell_output_combined():
    code = "print('hi')\nfig"
    bundle = json.dumps({"image/png": _PNG_DATA})
    cell = _console_cell(
        code,
        "hi\n",
        outputs=[
            {"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}
        ],
    )
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert "<pre>hi\n</pre>" == out.console_html
    assert out.output_type == "figure"
    assert _PNG_DATA in out.raw_html


def test_stderr_captured():
    code = "import sys; print('bad', file=sys.stderr)"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "eee",
        "console": [{"name": "stderr", "text": "bad\n"}],
        "outputs": [],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert "bad" in out.stderr_html
    assert 'class="stderr"' in out.stderr_html


def test_stream_media_image():
    code = "print_image"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "mmm",
        "console": [
            {"type": "streamMedia", "name": "media", "data": _PNG_DATA, "mimetype": "image/png"}
        ],
        "outputs": [],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert _PNG_DATA in out.media_html
    assert "<img" in out.media_html
    assert out.raw_html == ""


def test_stream_media_with_stdout():
    code = "print('hi')\nprint_image"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "nnn",
        "console": [
            {"name": "stdout", "text": "hi\n", "type": "stream", "mimetype": "text/plain"},
            {"type": "streamMedia", "name": "media", "data": _PNG_DATA, "mimetype": "image/png"},
        ],
        "outputs": [],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert "<pre>hi\n</pre>" == out.console_html
    assert "<img" in out.media_html


def test_unsupported_vega_type():
    code = "altair_chart"
    cell = _data_cell(code, "application/vnd.vegalite.v5+json", '{"mark": "bar"}')
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "unsupported"
    assert "vegalite" in out.raw_html
    assert "<!--" in out.raw_html


def test_unsupported_markdown_type():
    code = "mo_md_cell"
    cell = _data_cell(code, "text/markdown", "<span>heading</span>")
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "unsupported"
    assert "text/markdown" in out.raw_html


def test_latex_display_math():
    code = "latex_display"
    cell = _data_cell(code, "text/latex", r"\int_0^1 x^2 dx")
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "latex"
    assert "$$" in out.raw_html
    assert r"\int" in out.raw_html


def test_latex_already_delimited():
    code = "latex_delimited"
    cell = _data_cell(code, "text/latex", "$$E=mc^2$$")
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "latex"
    assert out.raw_html == "$$E=mc^2$$"


def test_latex_inline_delimited():
    code = "latex_inline"
    cell = _data_cell(code, "text/latex", "$x^2$")
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "latex"
    assert out.raw_html == "$x^2$"


def test_csv_output():
    code = "csv_out"
    csv_data = "name,age\nAlice,30\nBob,25"
    cell = _data_cell(code, "text/csv", csv_data)
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "csv"
    assert "Alice,30" in out.raw_html
    assert "<pre><code>" in out.raw_html


def test_table_data_json_decode_error():
    code = "df"
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
    results = extract_outputs(html)
    # Should fall back to original HTML
    assert len(results) == 1


def test_field_types_json_decode_error():
    code = "df"
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
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "table"
    # When field-types fails, it falls back to rows[0].keys() and builds HTML table
    assert "<table" in out.raw_html


def test_nan_in_string_value_not_replaced():
    code = "df"
    # A string column value "NaN handling" should NOT have its NaN replaced
    # with null — only bare NaN tokens (word boundaries) should be replaced.
    # Build data-data manually: use NaN as bare values where appropriate
    data_inner = '[{"col": "NaN handling"}, {"col": NaN}]'
    data_data = json.dumps(data_inner)
    marimo_table = (
        f"<marimo-ui-element>"
        f'<marimo-table data-data=\'{data_data}\' data-field-types=\'[["col", ["string", "str"]]]\'>'
        f"</marimo-table></marimo-ui-element>"
    )
    import html as html_module

    escaped = html_module.escape(marimo_table, quote=False)
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "kkk",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": escaped}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "table"
    # "NaN handling" should be preserved, not turned into "null handling"
    assert "NaN handling" in out.raw_html


def test_marimo_mimebundle_json_decode_error():
    code = "fig"
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
    results = extract_outputs(html)
    # Should not crash; bundle becomes {} and no figure is extracted
    assert results == {}


def test_generic_html_table():
    code = "df"
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
    results = extract_outputs(html)
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
    results = extract_outputs(html_bytes)
    assert results == {}


def test_brackets_inside_string_values():
    # A code_hash containing brackets — the old bracket-counting parser
    # would mis-parse this, but raw_decode handles it correctly.
    fake_hash = "ab[c]de"
    cell = {
        "code_hash": fake_hash,
        "id": "zzz",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/plain": "hello"}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert fake_hash in results
    assert results[fake_hash].output_type == "text"


def test_brackets_in_output_data():
    code = "x"
    # Cell output data containing brackets inside a JSON string value,
    # e.g. a text/plain value like "arr[0]". The old bracket-counting
    # parser would break here.
    cell = _text_cell(code, "arr[0] = 42")
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    assert "arr[0]" in results[_md5(code.strip())].raw_html


def test_cell_id_extracted():
    code = "fig"
    html = _make_html([_figure_cell(code)])
    results = extract_outputs(html)
    assert len(results) == 1
    out = list(results.values())[0]
    assert out.cell_id == "aaa"


def test_table_html_from_marimo_table_no_marimo_table():
    from marimo_md_export.parse_html import _table_html_from_marimo_table

    # HTML that doesn't contain <marimo-table> element
    result = _table_html_from_marimo_table("<div>not a table</div>")
    assert result == "<div>not a table</div>"


def test_json_dict_extraction():
    code = "my_dict"
    html = _make_html([_json_cell(code, {"name": "Alice", "age": 30})])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "json"
    assert "<pre><code>" in out.raw_html
    assert "&quot;name&quot;" in out.raw_html or '"name"' in out.raw_html
    assert "Alice" in out.raw_html


def test_json_list_extraction():
    code = "my_list"
    html = _make_html([_json_cell(code, [1, 2, 3])])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "json"
    assert "1" in out.raw_html


def test_json_nested_extraction():
    code = "nested"
    obj = {"key": [1, {"inner": True}]}
    html = _make_html([_json_cell(code, obj)])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert out.output_type == "json"
    assert "inner" in out.raw_html


def test_json_invalid_fallback():
    code = "bad_json"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "zzz",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"application/json": "not valid json {["}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "json"
    assert "not valid json" in out.raw_html


def test_json_priority_over_html():
    code = "obj_with_both"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "zzz",
        "console": [],
        "outputs": [
            {
                "type": "data",
                "data": {
                    "application/json": json.dumps({"key": "val"}),
                    "text/html": "<p>html content</p>",
                },
            }
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert out.output_type == "json"


def test_json_combined_with_console():
    code = "print('hi')\nmy_dict"
    cell = _console_cell(
        code,
        "hi\n",
        outputs=[
            {"type": "data", "data": {"application/json": json.dumps({"a": 1})}},
        ],
    )
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert out.console_html == "<pre>hi\n</pre>"
    assert out.output_type == "json"


def test_error_output_extraction():
    code = "1 / 0"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "err1",
        "console": [],
        "outputs": [
            {
                "type": "error",
                "ename": "ZeroDivisionError",
                "evalue": "division by zero",
                "traceback": [
                    "Traceback (most recent call last):",
                    '  File "<stdin>", line 1, in <module>',
                    "ZeroDivisionError: division by zero",
                ],
            }
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "error"
    assert "<strong>ZeroDivisionError</strong>" in out.raw_html
    assert "division by zero" in out.raw_html
    assert "<pre>" in out.raw_html


def test_error_without_traceback():
    code = "raise ValueError"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "err2",
        "console": [],
        "outputs": [
            {
                "type": "error",
                "ename": "ValueError",
                "evalue": "bad value",
                "traceback": [],
            }
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "error"
    assert "<strong>ValueError</strong>" in out.raw_html
    assert "<pre>" not in out.raw_html


def test_error_takes_priority_over_data():
    code = "bad_cell"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "err3",
        "console": [],
        "outputs": [
            {
                "type": "error",
                "ename": "RuntimeError",
                "evalue": "failed",
                "traceback": ["line 1"],
            },
            {"type": "data", "data": {"text/plain": "should not appear"}},
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert out.output_type == "error"
    assert "RuntimeError" in out.raw_html
    assert "should not appear" not in out.raw_html


def test_error_with_console_output():
    code = "print('before')\n1/0"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "err4",
        "console": [{"name": "stdout", "text": "before\n"}],
        "outputs": [
            {
                "type": "error",
                "ename": "ZeroDivisionError",
                "evalue": "division by zero",
                "traceback": ["traceback line"],
            }
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert out.console_html == "<pre>before\n</pre>"
    assert out.output_type == "error"


def test_stdout_and_stderr_both_captured():
    code = "print('out')\nprint('err', file=sys.stderr)"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "fff",
        "console": [
            {"name": "stdout", "text": "out\n"},
            {"name": "stderr", "text": "err\n"},
        ],
        "outputs": [],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert "<pre>out\n</pre>" == out.console_html
    assert "err" in out.stderr_html
    assert 'class="stderr"' in out.stderr_html
    assert out.raw_html == ""


def test_stderr_only_captured():
    code = "import logging; logging.warning('watch out')"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "ggg",
        "console": [{"name": "stderr", "text": "WARNING:root:watch out\n"}],
        "outputs": [],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    out = results[_md5(code.strip())]
    assert out.console_html == ""
    assert "WARNING:root:watch out" in out.stderr_html


def test_mimebundle_svg_fallback():
    code = "svg_fig"
    svg_data = "data:image/svg+xml,...svgcontent..."
    bundle = json.dumps({"image/svg+xml": svg_data})
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "aaa",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "figure"
    assert "image/svg+xml" in out.raw_html


def test_mimebundle_html_fallback():
    code = "html_output"
    bundle = json.dumps({"text/html": "<p>Hello</p>"})
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "bbb",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "html"
    assert "<p>Hello</p>" in out.raw_html


def test_mimebundle_text_fallback():
    code = "text_output"
    bundle = json.dumps({"text/plain": "simple text"})
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "ccc",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"application/vnd.marimo+mimebundle": bundle}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "text"
    assert "simple text" in out.raw_html


def test_standalone_image_png():
    code = "img_png"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "ddd",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"image/png": _PNG_DATA}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "figure"
    assert _PNG_DATA in out.raw_html


def test_standalone_image_jpeg():
    code = "img_jpeg"
    jpeg_data = "data:image/jpeg;base64,/9j/4AAQ..."
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "eee",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"image/jpeg": jpeg_data}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "figure"
    assert "jpeg" in out.raw_html


def test_standalone_image_svg():
    code = "img_svg"
    svg_data = "data:image/svg+xml,...svgcontent..."
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "fff",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"image/svg+xml": svg_data}}
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "figure"
    assert "svg+xml" in out.raw_html


def test_generic_html_output_type():
    code = "html_out"
    import html as html_module
    html_val = html_module.escape("<div>some generic html</div>", quote=False)
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "ggg",
        "console": [],
        "outputs": [{"type": "data", "data": {"text/html": html_val}}],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert out.output_type == "html"

def test_multiple_outputs_per_cell():
    code = "multi_output"
    cell = {
        "code_hash": _md5(code.strip()),
        "id": "ooo",
        "console": [],
        "outputs": [
            {"type": "data", "data": {"text/plain": "result text"}},
            {"type": "data", "data": {"text/html": "<p>extra</p>"}},
        ],
    }
    html = _make_html([cell])
    results = extract_outputs(html)
    assert len(results) == 1
    out = results[_md5(code.strip())]
    assert "result text" in out.raw_html
    assert "<p>extra</p>" in out.raw_html

