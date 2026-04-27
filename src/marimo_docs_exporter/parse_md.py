import hashlib
import re

from marimo_docs_exporter.models import MarkedCell

# Matches fenced code blocks produced by `marimo export md`
_BLOCK_RE = re.compile(r"(```python \{\.marimo\}\n(.*?)```)", re.DOTALL)
_MARKER_RE = re.compile(r"#\s*@output:\s*(\S+)")


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()


def collect_marked_cells(md: str) -> list[MarkedCell]:
    """Return one MarkedCell for each fenced block that contains an @output marker."""
    seen_labels: dict[str, int] = {}
    results: list[MarkedCell] = []

    for block_match in _BLOCK_RE.finditer(md):
        block_text = block_match.group(1)
        source = block_match.group(2)

        marker = _MARKER_RE.search(source)
        if marker is None:
            continue

        label = marker.group(1)
        if label in seen_labels:
            raise ValueError(
                f"Duplicate @output label {label!r} — each label must be unique"
            )
        seen_labels[label] = 1

        results.append(
            MarkedCell(
                label=label,
                source=source,
                source_hash=_md5(source.strip()),
                block_text=block_text,
            )
        )

    return results
