import hashlib

import pytest

from marimo_md_export.parse_md import collect_cells


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def _block(source: str, name: str | None = None, fence: int = 3) -> str:
    attrs = f' name="{name}"' if name else ""
    ticks = "`" * fence
    return f"{ticks}python {{.marimo{attrs}}}\n{source}\n{ticks}"


def test_all_blocks_collected():
    blocks = [
        "x = 1",
        "y = 2",
        "z = 3",
    ]
    md = "\n\n".join(_block(b) for b in blocks)
    cells = collect_cells(md)
    assert len(cells) == 3
    assert [c.source for c in cells] == [b + "\n" for b in blocks]


def test_suppress_marker():
    source = "# @suppress\nx = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].suppressed is True


def test_no_suppress():
    source = "x = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].suppressed is False


def test_suppress_anywhere_in_cell():
    source = "import os\n# @suppress\nos.getcwd()"
    cells = collect_cells(_block(source))
    assert len(cells) == 1
    assert cells[0].suppressed is True


def test_hash_stability():
    source = "x = 42"
    h1 = collect_cells(_block(source))[0].source_hash
    h2 = collect_cells(_block(source))[0].source_hash
    assert h1 == h2


def test_empty_notebook():
    assert collect_cells("") == []
    assert collect_cells("# just a comment\n## heading") == []


def test_scroll_marker():
    source = "# @scroll\nx = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].overflow == "scroll"


def test_wrap_marker():
    source = "# @wrap\nx = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].overflow == "wrap"


def test_no_overflow_marker():
    source = "x = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].overflow is None


def test_scroll_anywhere_in_cell():
    source = "import os\n# @scroll\nos.getcwd()"
    cells = collect_cells(_block(source))
    assert len(cells) == 1
    assert cells[0].overflow == "scroll"


def test_wrap_anywhere_in_cell():
    source = "import os\n# @wrap\nos.getcwd()"
    cells = collect_cells(_block(source))
    assert len(cells) == 1
    assert cells[0].overflow == "wrap"


def test_scroll_wins_over_wrap_when_both_present():
    source = "# @wrap\n# @scroll\nx = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].overflow == "scroll"


def test_wrap_wins_over_scroll_when_later():
    source = "# @scroll\n# @wrap\nx = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].overflow == "wrap"


def test_suppress_and_scroll():
    source = "# @suppress\n# @scroll\nx = 1"
    md = _block(source)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].suppressed is True
    assert cells[0].overflow == "scroll"


def test_hide_code_detected():
    md = '```python {.marimo hide_code="true"}\nimport marimo as mo\n```'
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].hide_code is True


def test_no_hide_code():
    source = "x = 1"
    cells = collect_cells(_block(source))
    assert len(cells) == 1
    assert cells[0].hide_code is False


def test_hide_code_not_triggered_by_source():
    # A normal cell whose source merely contains the marker string must not
    # be treated as hidden.
    md = "```python {.marimo}\nx = 'hide_code=\"true\"'\n```"
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].hide_code is False


def test_named_cells_are_collected():
    blocks = [
        ("x = 1", None),
        ("y = 2", "my_cell"),
        ("z = 3", None),
    ]
    md = "\n\n".join(_block(src, name=name) for src, name in blocks)
    cells = collect_cells(md)
    assert len(cells) == 3
    assert [c.source for c in cells] == [src + "\n" for src, _ in blocks]


def test_all_cells_named():
    md = "\n\n".join(_block("x = 1", name=f"cell_{i}") for i in range(5))
    cells = collect_cells(md)
    assert len(cells) == 5


# A cell whose source embeds a fenced code block forces marimo to widen the
# outer fence past 3 backticks (issue #23).
_INTERP_SOURCE = 'mo.md(rf"""\n```python\n{code}\n```\n""")'


def test_four_backtick_fence_collected():
    md = _block(_INTERP_SOURCE, fence=4)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].source == _INTERP_SOURCE + "\n"
    assert cells[0].block_text.startswith("````python {.marimo")
    assert cells[0].block_text.endswith("\n````")


def test_inner_triple_backtick_not_treated_as_close():
    # Regression guard: the inner ``` must not terminate the outer 4-tick fence,
    # i.e. the source must survive intact rather than being truncated.
    md = _block(_INTERP_SOURCE, fence=4)
    cells = collect_cells(md)
    assert len(cells) == 1
    assert "```python" in cells[0].source
    assert cells[0].source.count("```") == 2


def test_mixed_fence_widths_collected():
    blocks = [
        _block("x = 1", fence=3),
        _block(_INTERP_SOURCE, fence=4),
        _block("z = 3", fence=3),
    ]
    md = "\n\n".join(blocks)
    cells = collect_cells(md)
    assert len(cells) == 3
    assert [c.source for c in cells] == [
        "x = 1\n",
        _INTERP_SOURCE + "\n",
        "z = 3\n",
    ]
    # All three sources are distinct, so their hashes must be too.
    assert len({c.source_hash for c in cells}) == 3


def test_hide_code_detected_on_wide_fence():
    md = f'````python {{.marimo hide_code="true"}}\n{_INTERP_SOURCE}\n````'
    cells = collect_cells(md)
    assert len(cells) == 1
    assert cells[0].hide_code is True


def _nested_source(depth: int) -> str:
    """A source that embeds a fence one narrower than its own outer fence.

    depth 3 -> a bare fenced block; depth 4 -> one containing a 3-tick block;
    depth 5 -> one containing a 4-tick block containing a 3-tick block; etc.
    marimo widens the outer fence to `depth` backticks to escape it.
    """
    body = "code here"
    for width in range(3, depth):
        ticks = "`" * width
        body = f"{ticks}python\n{body}\n{ticks}"
    return f'mo.md(rf"""\n{body}\n""")'


@pytest.mark.parametrize("fence", [3, 4, 5, 6])
def test_arbitrary_fence_width_collected(fence):
    source = _nested_source(fence)
    md = _block(source, fence=fence)
    cells = collect_cells(md)
    assert len(cells) == 1
    # Source is collected intact, inner fences and all.
    assert cells[0].source == source + "\n"
    assert cells[0].block_text.startswith("`" * fence + "python")
    assert cells[0].block_text.endswith("\n" + "`" * fence)


def test_all_fence_widths_in_one_document():
    widths = [3, 4, 5, 6]
    sources = [_nested_source(w) for w in widths]
    md = "\n\n".join(_block(src, fence=w) for src, w in zip(sources, widths))
    cells = collect_cells(md)
    assert len(cells) == len(widths)
    assert [c.source for c in cells] == [src + "\n" for src in sources]
    assert len({c.source_hash for c in cells}) == len(widths)
