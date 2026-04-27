import asyncio
from pathlib import Path

from marimo._cli.parse_args import parse_args
from marimo._server.export import export_as_md, run_app_then_export_as_html
from marimo._utils.marimo_path import MarimoPath


def export_html(notebook: Path, extra_args: list[str] | None = None) -> bytes:
    argv = list(extra_args or [])
    result = asyncio.run(
        run_app_then_export_as_html(
            MarimoPath(notebook),
            include_code=True,
            cli_args=parse_args(tuple(argv)),
            argv=argv,
        )
    )
    if result.did_error:
        raise RuntimeError("marimo HTML export reported errors")
    return result.bytez


def export_md(notebook: Path) -> str:
    result = export_as_md(MarimoPath(notebook))
    return result.text
