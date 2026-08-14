import ast
import hashlib
import re

from .models import Cell

# Match a fence of 3+ backticks and require the closing fence to be the same
# width (\1). (see #23) The closing \1 is preceded by \n to anchor it to the
# start of a line.
_BLOCK_RE = re.compile(r"(`{3,})python \{\.marimo[^}]*\}\n(.*?\n)\1", re.DOTALL)
_SUPPRESS_RE = re.compile(r"#\s*@suppress")
_SCROLL_RE = re.compile(r"#\s*@scroll")
_WRAP_RE = re.compile(r"#\s*@wrap")
# The literal `hide_code="true"` is pinned to marimo's current export format
# (observed on 0.23.x). A future bare or differently-quoted attribute would
# silently no-op this detection.
_HIDE_CODE_RE = re.compile(r'hide_code="true"')


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()


def _is_mo_md_call(node: ast.expr) -> bool:
    """True if *node* is a call to ``mo.md(...)``."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "md"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "mo"
    )


def _is_mo_md(source: str) -> bool:
    """True if the cell's output comes from a bare ``mo.md(...)`` call.

    Only the *last* statement is examined, since that is the one whose value
    marimo renders as the cell output; earlier statements may compute the
    values an f-string interpolates. A trailing bare name is resolved back to
    its assignment in the same cell, so ``md = mo.md(...)`` then ``md`` counts.

    Cells that reach ``mo.md`` only indirectly -- nested inside a layout
    helper like ``mo.hstack``, say -- deliberately do not match: their output
    is HTML, so it must not be passed through verbatim.
    """
    try:
        tree = ast.parse(source.strip())
    except SyntaxError:
        return False
    if not tree.body or not isinstance(tree.body[-1], ast.Expr):
        return False

    value = tree.body[-1].value
    if isinstance(value, ast.Name):
        # Resolve to the last assignment of that name within the cell.
        for stmt in reversed(tree.body[:-1]):
            if isinstance(stmt, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == value.id for t in stmt.targets
            ):
                return _is_mo_md_call(stmt.value)
        return False

    return _is_mo_md_call(value)


def collect_cells(md: str) -> list[Cell]:
    """Return one Cell for each fenced code block in the markdown."""
    results: list[Cell] = []

    for block_match in _BLOCK_RE.finditer(md):
        block_text = block_match.group(0)
        source = block_match.group(2)

        suppressed = _SUPPRESS_RE.search(source) is not None

        # Only inspect the fence header line, not the whole block: a cell whose
        # source contains the literal string would otherwise be a false positive.
        fence_line = block_text.split("\n", 1)[0]
        hide_code = _HIDE_CODE_RE.search(fence_line) is not None

        overflow: str | None = None
        last_pos = -1
        for m in _WRAP_RE.finditer(source):
            if m.start() > last_pos:
                last_pos = m.start()
                overflow = "wrap"
        for m in _SCROLL_RE.finditer(source):
            if m.start() > last_pos:
                last_pos = m.start()
                overflow = "scroll"

        results.append(
            Cell(
                source=source,
                source_hash=_md5(source.strip()),
                block_text=block_text,
                suppressed=suppressed,
                hide_code=hide_code,
                overflow=overflow,
                is_mo_md=_is_mo_md(source),
            )
        )

    return results
