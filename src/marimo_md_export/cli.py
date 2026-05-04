from pathlib import Path

import typer
from rich.console import Console

from .export import export_html, export_md, strip_header_from_frontmatter
from .inject import inject_outputs
from .parse_html import extract_outputs
from .parse_md import collect_cells

_err_console = Console(stderr=True)

app = typer.Typer(
    help="Export a marimo (.py) notebook to markdown (.md) with rendered outputs embedded inline.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


@app.command()
def main(
    notebook: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the marimo notebook (.py)",
    ),
    output: Path = typer.Argument(
        ...,
        writable=True,
        help="Where to write the resulting markdown file",
    ),
    html_output: Path = typer.Option(
        None,
        "--html-output",
        writable=True,
        help="If provided, also save the intermediate HTML export to this path",
    ),
    marimo_args: str = typer.Option(
        "",
        "--marimo-args",
        help="Extra arguments forwarded to marimo export (space-separated)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    sandbox: bool = typer.Option(
        False,
        "--sandbox/--no-sandbox",
        help="Run marimo export in an isolated uv environment. "
        "Without this flag, marimo's own sandbox prompt is suppressed.",
    ),
    timeout: int = typer.Option(
        120,
        "--timeout",
        help="Maximum seconds to wait for each marimo export subprocess "
        "(set to 0 to disable).",
    ),
) -> None:
    """Export a marimo notebook to markdown with rendered outputs injected.

    marimo export is always called with --force to suppress overwrite
    prompts; MPLBACKEND=Agg is set in the subprocess environment to
    prevent matplotlib from hanging. Use --sandbox to run the export
    in an isolated uv environment.
    """
    extra = marimo_args.split() if marimo_args.strip() else []
    timeout_val: int | None = timeout or None

    if verbose:
        typer.echo(f"Exporting markdown: {notebook}")
    try:
        md = export_md(notebook, sandbox=sandbox, timeout=timeout_val)
    except RuntimeError as exc:
        typer.echo(f"marimo export md failed:\n{exc}", err=True)
        raise typer.Exit(1)

    cells = collect_cells(md)

    if verbose:
        n_active = sum(1 for c in cells if not c.suppressed)
        n_suppressed = sum(1 for c in cells if c.suppressed)
        typer.echo(f"Found {n_active} cell(s), {n_suppressed} suppressed")
        typer.echo(f"Exporting HTML: {notebook}")

    try:
        html = export_html(notebook, extra, sandbox=sandbox, timeout=timeout_val)
    except RuntimeError as exc:
        typer.echo(f"marimo export html failed:\n{exc}", err=True)
        raise typer.Exit(1)

    if html_output is not None:
        html_output.parent.mkdir(parents=True, exist_ok=True)
        html_output.write_bytes(html)
        if verbose:
            typer.echo(f"Wrote {html_output}")

    outputs = extract_outputs(html)
    result, warnings = inject_outputs(md, cells, outputs)

    for warning in warnings:
        _err_console.print(f"WARNING: {warning}", style="bold yellow")

    result = strip_header_from_frontmatter(result)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")

    if verbose:
        typer.echo(f"Wrote {output}")
