import hashlib

import pytest

from marimo_md_export.parse_md import collect_marked_cells


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8"), usedforsecurity=False).hexdigest()


def _block(source: str) -> str:
    return f"```python {{.marimo}}\n{source}\n```"


def test_single_marker():
    source = "# @output: my_fig\nfig"
    md = _block(source)
    cells = collect_marked_cells(md)
    assert len(cells) == 1
    assert cells[0].label == "my_fig"
    assert cells[0].source_hash == _md5(source.strip())


def test_multiple_markers():
    blocks = [
        "# @output: first\nx = 1",
        "# @output: second\ny = 2",
        "# @output: third\nz = 3",
    ]
    md = "\n\n".join(_block(b) for b in blocks)
    cells = collect_marked_cells(md)
    assert [c.label for c in cells] == ["first", "second", "third"]


def test_unmarked_blocks_ignored():
    md = _block("x = 1") + "\n\n" + _block("# @output: found\ny = 2")
    cells = collect_marked_cells(md)
    assert len(cells) == 1
    assert cells[0].label == "found"


def test_duplicate_label_raises():
    md = _block("# @output: dup\nx") + "\n\n" + _block("# @output: dup\ny")
    with pytest.raises(ValueError, match="dup"):
        collect_marked_cells(md)


def test_marker_not_on_first_line():
    source = "import os\nimport sys\n# @output: late_marker\nos.getcwd()"
    cells = collect_marked_cells(_block(source))
    assert len(cells) == 1
    assert cells[0].label == "late_marker"


def test_hash_stability():
    source = "# @output: stable\nx = 42"
    h1 = collect_marked_cells(_block(source))[0].source_hash
    h2 = collect_marked_cells(_block(source))[0].source_hash
    assert h1 == h2


def test_empty_notebook():
    assert collect_marked_cells("") == []
    assert collect_marked_cells("# just a comment\n## heading") == []
