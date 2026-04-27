import subprocess
from pathlib import Path

import typer

from .export import export_html, export_md
from .inject import inject_outputs
from .parse_html import extract_outputs
from .parse_md import collect_marked_cells

app = typer.Typer(add_completion=False)


@app.command()
def main(
    notebook: Path = typer.Argument(
        ...,
        exists=True,
        help="Path to the marimo notebook (.py)",
    ),
    output: Path = typer.Argument(
        ...,
        help="Where to write the resulting markdown file",
    ),
    marimo_args: str = typer.Option(
        "",
        "--marimo-args",
        help="Extra arguments forwarded to marimo export (space-separated)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Export a marimo notebook to markdown with rendered outputs injected."""
    extra = marimo_args.split() if marimo_args.strip() else []

    # Run both exports
    if verbose:
        typer.echo(f"Exporting markdown: {notebook}")
    try:
        md = export_md(notebook, extra)
    except subprocess.CalledProcessError as exc:
        typer.echo(f"marimo export md failed:\n{exc.stderr.decode()}", err=True)
        raise typer.Exit(1)

    marked = collect_marked_cells(md)
    if not marked:
        typer.echo(
            f"WARNING: no @output markers found in {notebook}. "
            "Did you forget to add '# @output: <label>' comments?",
            err=True,
        )
        raise typer.Exit(2)

    if verbose:
        typer.echo(
            f"Found {len(marked)} @output marker(s): "
            + ", ".join(c.label for c in marked)
        )
        typer.echo(f"Exporting HTML: {notebook}")

    try:
        html = export_html(notebook, extra)
    except subprocess.CalledProcessError as exc:
        typer.echo(f"marimo export html failed:\n{exc.stderr.decode()}", err=True)
        raise typer.Exit(1)

    target_hashes = {c.source_hash for c in marked}
    outputs = extract_outputs(html, target_hashes)

    # Attach labels to outputs
    for cell in marked:
        if cell.source_hash in outputs:
            outputs[cell.source_hash].label = cell.label

    result = inject_outputs(md, outputs)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")

    if verbose:
        typer.echo(f"Wrote {output}")
