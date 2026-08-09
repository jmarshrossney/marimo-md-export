"""Write inline data-URI images out to files and link to them from the markdown.

By default every image reaches the markdown as an `<img src="data:...">` tag,
whether it came from a mimebundle, a standalone `image/*` output, or a console
`streamMedia` chunk (see parse_html).  This module runs as a single pass over
the *finished* markdown, so it catches all of those at once — and any data-URI
image a user embedded by hand in a `mo.md` block — without any of the parsing
code needing to know about it.

It must run after inject, because `_escape_brackets_in_html` would otherwise
mangle the `![alt](path)` markdown we emit.
"""

import base64
import binascii
import re
from html import escape, unescape
from pathlib import Path
from urllib.parse import unquote

# Every <img> tag we generate uses double quotes and passes the src through
# html.escape(quote=True), so a value can never contain a bare double quote.
_IMG_RE = re.compile(r'<img\b[^>]*?\bsrc="(data:image/[^"]*)"[^>]*?>', re.IGNORECASE)

_DATA_URI_RE = re.compile(
    r"data:(?P<mime>image/[\w.+-]+)(?P<params>;[^,]*)?,(?P<payload>.*)",
    re.DOTALL,
)

_EXTENSIONS = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "image/tiff": "tiff",
    "image/avif": "avif",
    "image/bmp": "bmp",
    "image/webp": "webp",
}

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_WHITESPACE_RE = re.compile(r"\s+")


def _extension(mime: str) -> str:
    """Filename extension (no dot) for an image MIME type."""
    known = _EXTENSIONS.get(mime.lower())
    if known is not None:
        return known
    subtype = mime.lower().partition("/")[2]
    return _NON_ALNUM_RE.sub("", subtype) or "img"


def _decode(src: str) -> tuple[str, bytes] | None:
    """Decode a data URI into (mime, payload bytes), or None if malformed."""
    match = _DATA_URI_RE.fullmatch(unescape(src))
    if match is None:
        return None

    mime = match.group("mime")
    payload = match.group("payload")

    if "base64" in (match.group("params") or ""):
        try:
            return mime, base64.b64decode(
                _WHITESPACE_RE.sub("", payload), validate=True
            )
        except (binascii.Error, ValueError):
            return None

    # Not base64: percent-encoded text, which is how raw SVG markup arrives.
    return mime, unquote(payload).encode("utf-8")


def _is_own_line(md: str, start: int, end: int) -> bool:
    """True if md[start:end] is alone on its line, ignoring whitespace."""
    line_start = md.rfind("\n", 0, start) + 1
    line_end = md.find("\n", end)
    if line_end == -1:
        line_end = len(md)
    return not md[line_start:start].strip() and not md[end:line_end].strip()


def externalize_figures(
    md: str,
    output: Path,
    figures_dir: Path,
) -> tuple[str, list[Path], list[str]]:
    """Write inline data-URI images to disk and replace them with file links.

    figures_dir is resolved relative to the output file's directory unless it
    is absolute, in which case the markdown links are absolute too.

    Returns (markdown, written_paths, warnings).
    """
    target_dir = (
        figures_dir if figures_dir.is_absolute() else output.parent / figures_dir
    )
    # The markdown lives in output.parent, so a relative figures_dir is already
    # the correct link prefix; an absolute one links absolutely.
    link_base = figures_dir.as_posix()

    written: list[Path] = []
    warnings: list[str] = []
    pieces: list[str] = []
    cursor = 0

    for match in _IMG_RE.finditer(md):
        decoded = _decode(match.group(1))
        if decoded is None:
            warnings.append(
                f"could not decode inline image (data URI malformed); "
                f"leaving it embedded: {match.group(1)[:60]}..."
            )
            continue

        mime, payload = decoded
        ext = _extension(mime)

        if not written:
            target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{output.stem}-{len(written) + 1}.{ext}"
        path.write_bytes(payload)
        written.append(path)

        link = f"{link_base}/{path.name}"
        if _is_own_line(md, match.start(), match.end()):
            replacement = f"![{ext}]({link})"
        else:
            # Nested inside passthrough HTML, where markdown syntax would not
            # be rendered — keep the tag and just repoint it.
            replacement = (
                match.group(0)[: match.start(1) - match.start()]
                + escape(link, quote=True)
                + match.group(0)[match.end(1) - match.start() :]
            )

        pieces.append(md[cursor : match.start()])
        pieces.append(replacement)
        cursor = match.end()

    pieces.append(md[cursor:])
    return "".join(pieces), written, warnings
