import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

_HEADER_KEY_RE = re.compile(r"^header:.*\n(?:[ \t].*\n)*", re.MULTILINE)


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
