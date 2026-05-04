import hashlib
import re

from .models import Cell

# Matches fenced code blocks produced by `marimo export md`
_BLOCK_RE = re.compile(r"(```python \{\.marimo\}\n(.*?)```)", re.DOTALL)
_SUPPRESS_RE = re.compile(r"#\s*@suppress")


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()


def collect_cells(md: str) -> list[Cell]:
    """Return one Cell for each fenced code block in the markdown."""
    results: list[Cell] = []

    for block_match in _BLOCK_RE.finditer(md):
        block_text = block_match.group(1)
        source = block_match.group(2)

        suppressed = _SUPPRESS_RE.search(source) is not None

        results.append(
            Cell(
                source=source,
                source_hash=_md5(source.strip()),
                block_text=block_text,
                suppressed=suppressed,
            )
        )

    return results
