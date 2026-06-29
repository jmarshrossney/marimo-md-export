import hashlib

from marimo_md_export.parse_md import collect_cells


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def _block(source: str, name: str | None = None) -> str:
    attrs = f' name="{name}"' if name else ""
    return f"```python {{.marimo{attrs}}}\n{source}\n```"


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
