from pathlib import Path

import typer
from rich.console import Console

from .export import export_html, export_md, strip_header_from_frontmatter
from .figures import externalize_figures
from .inject import (
    _PRE_STYLE_SCROLL,
    _PRE_STYLE_WRAP,
    inject_outputs,
)
from .parse_html import extract_outputs
from .parse_md import collect_cells
from .transform import convert_admonitions
from .version import __version__

_err_console = Console(stderr=True)

app = typer.Typer(
    help="Export a marimo (.py) notebook to markdown (.md) with rendered outputs embedded inline.",
    context_settings={"help_option_names": ["-h", "--help"]},
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


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
    keep_html: bool = typer.Option(
        True,
        "--keep-html/--no-keep-html",
        help="Write the intermediate HTML export to {assets-dir}/notebook.html "
        "(default: keep). Use --no-keep-html to discard it.",
    ),
    self_contained: bool = typer.Option(
        False,
        "--self-contained/--no-self-contained",
        help="Embed figures as base64 data URIs in the markdown instead of "
        "writing them as files under the assets directory.",
    ),
    assets_dir: Path | None = typer.Option(
        None,
        "--assets-dir",
        metavar="PATH",
        help="Directory for sidecar assets (figures and/or notebook.html). "
        "Defaults to {output_stem}_assets/ beside the markdown file. "
        "Relative paths are resolved against the output file's directory.",
    ),
    marimo_args: str = typer.Option(
        "",
        "--marimo-args",
        metavar="TEXT",
        help="Extra arguments forwarded to marimo export (space-separated)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Print progress to stdout"
    ),
    sandbox: bool = typer.Option(
        False,
        "--sandbox/--no-sandbox",
        help="Run marimo export in an isolated uv environment. "
        "Without this flag, marimo's own sandbox prompt is suppressed.",
    ),
    timeout: int | None = typer.Option(
        None,
        "--timeout",
        metavar="SECONDS",
        help="Maximum seconds to wait for each marimo export subprocess "
        "(default: no timeout).",
    ),
    overflow: str = typer.Option(
        "wrap",
        "--overflow",
        metavar="MODE",
        help="Default overflow behavior for long output lines: 'wrap' (default) or 'scroll'. "
        "Can be overridden per cell with # @scroll or # @wrap.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Print the version and exit.",
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

    md = convert_admonitions(md)
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

    if overflow == "scroll":
        pre_style = _PRE_STYLE_SCROLL
    elif overflow == "wrap":
        pre_style = _PRE_STYLE_WRAP
    else:
        typer.echo(
            f"Invalid overflow value: {overflow!r}. Must be 'wrap' or 'scroll'.",
            err=True,
        )
        raise typer.Exit(2)

    outputs = extract_outputs(html)
    result, warnings = inject_outputs(md, cells, outputs, default_pre_style=pre_style)

    for warning in warnings:
        _err_console.print(f"WARNING: {warning}", style="bold yellow")

    result = strip_header_from_frontmatter(result)

    resolved_assets = (
        assets_dir if assets_dir is not None else Path(f"{output.stem}_assets")
    )
    assets_path = (
        resolved_assets
        if resolved_assets.is_absolute()
        else output.parent / resolved_assets
    )
    if keep_html or not self_contained:
        assets_path.mkdir(parents=True, exist_ok=True)

    if keep_html:
        html_path = assets_path / "notebook.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_bytes(html)
        if verbose:
            typer.echo(f"Wrote {html_path}")

    if not self_contained:
        result, figures, fig_warnings = externalize_figures(
            result, output, resolved_assets
        )
        for warning in fig_warnings:
            _err_console.print(f"WARNING: {warning}", style="bold yellow")
        if verbose:
            typer.echo(f"Wrote {len(figures)} figure(s)")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")

    if verbose:
        typer.echo(f"Wrote {output}")
