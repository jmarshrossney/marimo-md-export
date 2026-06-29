import hashlib
import re

from .models import Cell

_BLOCK_RE = re.compile(r"(```python \{\.marimo[^}]*\}\n(.*?)```)", re.DOTALL)
_SUPPRESS_RE = re.compile(r"#\s*@suppress")
_SCROLL_RE = re.compile(r"#\s*@scroll")
_WRAP_RE = re.compile(r"#\s*@wrap")


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()


def collect_cells(md: str) -> list[Cell]:
    """Return one Cell for each fenced code block in the markdown."""
    results: list[Cell] = []

    for block_match in _BLOCK_RE.finditer(md):
        block_text = block_match.group(1)
        source = block_match.group(2)

        suppressed = _SUPPRESS_RE.search(source) is not None

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
                overflow=overflow,
            )
        )

    return results
