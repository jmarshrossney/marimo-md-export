import re
import subprocess
import tempfile
from pathlib import Path

_HEADER_KEY_RE = re.compile(r"^header:.*\n(?:[ \t].*\n)*", re.MULTILINE)


def export_html(
    notebook: Path,
    extra_args: list[str] | None = None,
    sandbox: bool = False,
) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        tmp = Path(f.name)
    try:
        cmd = [
            "marimo",
            "export",
            "html",
            str(notebook),
            "-o",
            str(tmp),
            "--include-code",
        ]
        if sandbox:
            cmd.append("--sandbox")
        if extra_args:
            cmd.append("--")
            cmd.extend(extra_args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"marimo export html failed:\n{result.stderr}")
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)


def export_md(notebook: Path, sandbox: bool = False) -> str:
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        tmp = Path(f.name)
    try:
        cmd = ["marimo", "export", "md", str(notebook), "-o", str(tmp)]
        if sandbox:
            cmd.append("--sandbox")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"marimo export md failed:\n{result.stderr}")
        return tmp.read_text(encoding="utf-8")
    finally:
        tmp.unlink(missing_ok=True)


def strip_header_from_frontmatter(md: str) -> str:
    """Remove the 'header:' key from YAML frontmatter if present."""
    if not md.startswith("---"):
        return md

    close_marker = md.find("\n---", 3)
    if close_marker == -1:
        return md

    after_close = close_marker + 4
    if after_close < len(md) and md[after_close] == "\n":
        after_close += 1

    frontmatter = md[:after_close]
    rest = md[after_close:]

    stripped = _HEADER_KEY_RE.sub("", frontmatter)
    if stripped == frontmatter:
        return md

    inner = stripped[len("---\n") : stripped.rfind("\n---")]
    if not inner.strip():
        return rest.lstrip("\n")

    return stripped + rest
