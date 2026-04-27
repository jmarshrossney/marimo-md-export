import subprocess
from pathlib import Path


def export_html(notebook: Path, extra_args: list[str] | None = None) -> bytes:
    result = subprocess.run(
        [
            "marimo",
            "export",
            "html",
            "--no-sandbox",
            *(extra_args or []),
            str(notebook),
        ],
        capture_output=True,
        check=True,
    )
    return result.stdout


def export_md(notebook: Path, extra_args: list[str] | None = None) -> str:
    result = subprocess.run(
        ["marimo", "export", "md", "--no-sandbox", *(extra_args or []), str(notebook)],
        capture_output=True,
        check=True,
    )
    return result.stdout.decode()
