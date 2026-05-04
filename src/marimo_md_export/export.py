import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path


def _strip_header_key(frontmatter: str) -> str | None:
    """Remove the 'header:' key (with its multiline value) from a YAML frontmatter block.

    Returns None if the header key was not found. Handles YAML block scalars
    (|-, |, >-, >) and plain multiline values (indented continuation lines).
    """
    lines = frontmatter.split("\n")
    result_lines: list[str] = []
    i = 0
    found = False
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped.startswith("header:"):
            result_lines.append(line)
            i += 1
            continue

        found = True
        value_part = line[len("header:"):].strip()
        # Detect block scalar indicators: |, |-, >, >-
        is_block = value_part in ("|", "|-", ">", ">-")
        if is_block:
            # Skip indented continuation lines
            i += 1
            while i < len(lines) and lines[i].startswith(("  ", "\t")):
                i += 1
        else:
            # Plain value (possibly none after the colon)
            i += 1

    if not found:
        return None

    return "\n".join(result_lines)


def _run_with_visible_output(
    cmd: list[str], *, env: dict[str, str], timeout: float | None
) -> subprocess.CompletedProcess[str]:
    """Run *cmd* with stdout inherited (visible) and stderr captured."""
    stderr_lines: list[str] = []

    def _reader(pipe: subprocess.Popen) -> None:
        assert pipe.stderr is not None
        for line in pipe.stderr:
            sys.stderr.write(line)
            stderr_lines.append(line)

    with subprocess.Popen(
        cmd, stdout=None, stderr=subprocess.PIPE, text=True, env=env
    ) as process:
        t = threading.Thread(target=_reader, args=(process,), daemon=True)
        t.start()
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            raise
        t.join(timeout=5)
        return subprocess.CompletedProcess(
            cmd, returncode, stdout="", stderr="".join(stderr_lines)
        )


def export_html(
    notebook: Path,
    extra_args: list[str] | None = None,
    sandbox: bool = False,
    timeout: float | None = 120,
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
            "--force",
        ]
        if sandbox:
            cmd.append("--sandbox")
        if extra_args:
            cmd.append("--")
            cmd.extend(extra_args)
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        env["MARIMO_MANAGE_SCRIPT_METADATA"] = "true"
        try:
            result = _run_with_visible_output(cmd, env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"marimo export html timed out after {timeout}s.\n"
                "Try passing --sandbox to run in an isolated environment."
            )
        if result.returncode != 0:
            raise RuntimeError(f"marimo export html failed:\n{result.stderr}")
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)


def export_md(
    notebook: Path,
    sandbox: bool = False,
    timeout: float | None = 120,
) -> str:
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        tmp = Path(f.name)
    try:
        cmd = ["marimo", "export", "md", str(notebook), "-o", str(tmp), "--force"]
        if sandbox:
            cmd.append("--sandbox")
        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        env["MARIMO_MANAGE_SCRIPT_METADATA"] = "true"
        try:
            result = _run_with_visible_output(cmd, env=env, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"marimo export md timed out after {timeout}s.\n"
                "Try passing --sandbox to run in an isolated environment."
            )
        if result.returncode != 0:
            raise RuntimeError(f"marimo export md failed:\n{result.stderr}")
        return tmp.read_text(encoding="utf-8")
    finally:
        tmp.unlink(missing_ok=True)


def strip_header_from_frontmatter(md: str) -> str:
    """Remove the 'header:' key from YAML frontmatter if present.

    Parses the frontmatter line-by-line, removes the header key (including
    any multiline block-scalar or indented continuation lines), then
    reconstructs the frontmatter. If only a title key remains, it is
    preserved cleanly. If the frontmatter is empty after removal, it is
    dropped entirely.
    """
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

    stripped = _strip_header_key(frontmatter)
    if stripped is None:
        return md

    inner_start = len("---\n")
    inner_end = stripped.rfind("\n---")
    inner = stripped[inner_start:inner_end]

    if not inner.strip():
        return rest.lstrip("\n")

    return stripped + rest
