import pytest

from marimo_md_export.inject import inject_outputs
from marimo_md_export.models import ExtractedOutput
from marimo_md_export.parse_md import collect_marked_cells


def _block(source: str) -> str:
    return f"```python {{.marimo}}\n{source}\n```"


def _md_with_block(source: str) -> str:
    return _block(source) + "\n\nsome other text"


def _figure_output(label: str) -> ExtractedOutput:
    return ExtractedOutput(
        label=label,
        raw_html='<img src="data:image/png;base64,abc123" alt="figure">',
        output_type="figure",
    )


def _table_output(label: str, html: str) -> ExtractedOutput:
    return ExtractedOutput(label=label, raw_html=html, output_type="table")


def _text_output(label: str) -> ExtractedOutput:
    return ExtractedOutput(label=label, raw_html="<pre>hello</pre>", output_type="text")


def _build_outputs(md: str, overrides: dict | None = None) -> dict:
    cells = collect_marked_cells(md)
    outputs = {}
    for cell in cells:
        outputs[cell.source_hash] = _figure_output(cell.label)
    if overrides:
        outputs.update(overrides)
    return outputs


# ---------------------------------------------------------------------------


def test_figure_injected_after_block():
    source = "# @output: my_fig\nfig"
    md = _md_with_block(source)
    outputs = _build_outputs(md)
    result = inject_outputs(md, outputs)
    block = _block(source)
    assert block in result
    img_pos = result.index('<img src="data:image/png')
    block_end = result.index(block) + len(block)
    assert img_pos > block_end


def test_table_converted_to_gfm():
    source = "# @output: tbl\ndf"
    md = _md_with_block(source)
    cells = collect_marked_cells(md)
    simple_table = (
        "<table><thead><tr><th>A</th><th>B</th></tr></thead>"
        "<tbody><tr><td>1</td><td>2</td></tr></tbody></table>"
    )
    outputs = {cells[0].source_hash: _table_output("tbl", simple_table)}
    result = inject_outputs(md, outputs)
    assert "| A | B |" in result
    assert "| 1 | 2 |" in result


def test_table_falls_back_to_html():
    source = "# @output: merged\ndf"
    md = _md_with_block(source)
    cells = collect_marked_cells(md)
    merged_table = (
        "<table><thead><tr><th colspan='2'>Header</th></tr></thead>"
        "<tbody><tr><td>a</td><td>b</td></tr></tbody></table>"
    )
    outputs = {cells[0].source_hash: _table_output("merged", merged_table)}
    result = inject_outputs(md, outputs)
    assert "<table" in result


def test_missing_output_warns():
    source = "# @output: ghost\nx"
    md = _md_with_block(source)
    with pytest.warns(UserWarning, match="ghost"):
        result = inject_outputs(md, {})
    # block unchanged
    assert _block(source) in result
    # no injection appended after the block
    block_end_idx = result.index(_block(source)) + len(_block(source))
    tail = result[block_end_idx:]
    assert "<!-- @output:" not in tail


def test_unmarked_blocks_unchanged():
    source_marked = "# @output: real\nfig"
    source_plain = "x = 1\ny = 2"
    md = _block(source_plain) + "\n\n" + _block(source_marked)
    outputs = _build_outputs(md)
    result = inject_outputs(md, outputs)
    assert _block(source_plain) in result
    assert "<!-- @output:real -->" in result


def test_output_comment_injected():
    source = "# @output: labelled\nfig"
    md = _md_with_block(source)
    outputs = _build_outputs(md)
    result = inject_outputs(md, outputs)
    assert "<!-- @output:labelled -->" in result
