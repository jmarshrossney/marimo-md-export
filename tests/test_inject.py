from marimo_md_export.inject import inject_outputs
from marimo_md_export.models import ExtractedOutput
from marimo_md_export.parse_md import collect_cells


def _block(source: str) -> str:
    return f"```python {{.marimo}}\n{source}\n```"


def _md_with_block(source: str) -> str:
    return _block(source) + "\n\nsome other text"


def _figure_output(cell_id: str) -> ExtractedOutput:
    return ExtractedOutput(
        raw_html='<img src="data:image/png;base64,abc123" alt="figure">',
        output_type="figure",
        cell_id=cell_id,
    )


def _table_output(cell_id: str, html: str) -> ExtractedOutput:
    return ExtractedOutput(raw_html=html, output_type="table", cell_id=cell_id)


def _text_output(cell_id: str) -> ExtractedOutput:
    return ExtractedOutput(
        raw_html="<pre>hello</pre>", output_type="text", cell_id=cell_id
    )


def _build_outputs(md: str, overrides: dict | None = None) -> dict:
    cells = collect_cells(md)
    outputs = {}
    for idx, cell in enumerate(cells):
        cell_id = chr(ord("a") + idx) * 3  # "aaa", "bbb", ...
        outputs[cell.source_hash] = _figure_output(cell_id)
    if overrides:
        outputs.update(overrides)
    return outputs


def _inject(md: str, outputs: dict) -> tuple[str, list[str]]:
    return inject_outputs(md, collect_cells(md), outputs)


# ---------------------------------------------------------------------------


def test_figure_injected_after_block():
    source = "fig"
    md = _md_with_block(source)
    outputs = _build_outputs(md)
    result, warnings = _inject(md, outputs)
    block = _block(source)
    assert block in result
    img_pos = result.index('<img src="data:image/png')
    block_end = result.index(block) + len(block)
    assert img_pos > block_end
    assert warnings == []


def test_table_converted_to_gfm():
    source = "df"
    md = _md_with_block(source)
    cells = collect_cells(md)
    simple_table = (
        "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
        "<tbody><tr><td>1</td><td>2</td></tr></tbody></table>"
    )
    outputs = {cells[0].source_hash: _table_output("aaa", simple_table)}
    result, warnings = _inject(md, outputs)
    assert "| A | B |" in result
    assert "| 1 | 2 |" in result
    assert warnings == []


def test_table_falls_back_to_html():
    source = "df"
    md = _md_with_block(source)
    cells = collect_cells(md)
    merged_table = (
        "<table><thead><tr><th colspan='2'>Header</th></tr></thead>"
        "<tbody><tr><td>a</td><td>b</td></tr></tbody></table>"
    )
    outputs = {cells[0].source_hash: _table_output("aaa", merged_table)}
    result, warnings = _inject(md, outputs)
    assert "<table" in result


def test_table_falls_back_to_html_on_uneven_rows():
    source = "df"
    md = _md_with_block(source)
    cells = collect_cells(md)
    uneven_table = (
        "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
        "<tbody><tr><td>1</td></tr></tbody></table>"
    )
    outputs = {cells[0].source_hash: _table_output("aaa", uneven_table)}
    result, warnings = _inject(md, outputs)
    assert "<table" in result


def test_cell_without_output_unchanged():
    source = "x = 1"
    md = _md_with_block(source)
    result, warnings = _inject(md, {})
    assert _block(source) in result
    block_end_idx = result.index(_block(source)) + len(_block(source))
    tail = result[block_end_idx:]
    assert "<!-- @output:" not in tail
    assert warnings == []


def test_suppressed_cell_skipped():
    source = "# @suppress\nfig"
    md = _md_with_block(source)
    outputs = _build_outputs(md)
    result, warnings = _inject(md, outputs)
    assert _block(source) in result
    assert "<!-- @output:" not in result
    assert warnings == []


def test_auto_label_from_cell_id():
    source = "fig"
    md = _md_with_block(source)
    cells = collect_cells(md)
    outputs = {cells[0].source_hash: _figure_output("xyz")}
    result, warnings = _inject(md, outputs)
    assert "<!-- @output:xyz -->" in result
    assert warnings == []


def test_output_comment_injected():
    source = "fig"
    md = _md_with_block(source)
    outputs = _build_outputs(md)
    result, warnings = _inject(md, outputs)
    assert "<!-- @output:aaa -->" in result
    assert warnings == []


def test_table_to_gfm_no_table():
    from marimo_md_export.inject import _table_to_gfm

    result = _table_to_gfm("<div>not a table</div>")
    assert result is None


def test_table_to_gfm_empty_table():
    from marimo_md_export.inject import _table_to_gfm

    result = _table_to_gfm("<table></table>")
    assert result is None


def test_table_to_gfm_uneven_rows():
    from marimo_md_export.inject import _table_to_gfm

    html = (
        "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
        "<tbody><tr><td>only one</td></tr></tbody></table>"
    )
    result = _table_to_gfm(html)
    assert result is None


def test_table_to_gfm_pipe_escaped():
    from marimo_md_export.inject import _table_to_gfm

    html = (
        "<table><thead><tr><th>Expr</th><th>Result</th></tr></thead>"
        "<tbody><tr><td>a | b</td><td>x || y</td></tr></tbody></table>"
    )
    result = _table_to_gfm(html)
    assert result is not None
    assert r"\|" in result
    assert "| a \\| b |" in result
