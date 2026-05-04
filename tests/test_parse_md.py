import hashlib

from marimo_md_export.parse_md import collect_cells


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def _block(source: str) -> str:
    return f"```python {{.marimo}}\n{source}\n```"


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
