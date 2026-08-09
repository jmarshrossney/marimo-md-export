from pathlib import Path
from typing import NamedTuple

import pytest
from typer.testing import CliRunner
from unittest.mock import patch

from marimo_md_export.cli import app

runner = CliRunner()

_PNG_DATA = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


def test_full_pipeline(tmp_path, example_notebook):
    notebook = example_notebook
    output = tmp_path / "output.md"

    result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 0, result.output

    md = output.read_text()

    assert "```python" in md, "markdown code blocks should be present"
    assert md.count("<!-- @output:") >= 3, "at least 3 outputs should be injected"

    assert "data:image/png;base64," in md, "figure should be embedded as base64 PNG"
    assert "|" in md or "<table" in md, "table should be present as GFM or HTML"
    assert "<pre" in md, "text output should be wrapped in a pre block"

    assert "Figures" in md

    # Issue #23: an f-string mo.md() cell that interpolates a value inside a
    # fenced code block forces marimo to widen the outer fence past three
    # backticks. The interpolated value must be rendered, not the raw
    # placeholder, and the block must not be garbled.
    interp_line = next(
        (line for line in md.splitlines() if "n_points" in line and "300" in line),
        None,
    )
    assert interp_line is not None, "interpolated code block should be rendered"
    assert "300" in interp_line, "interpolated value (len(x) == 300) should appear"
    assert "{len(x)}" not in interp_line, "placeholder must be interpolated"

    assert "WARNING" not in result.output


def test_export_md_failure(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    with patch("marimo_md_export.cli.export_md", side_effect=RuntimeError("md failed")):
        result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 1
    assert "marimo export md failed:" in result.stderr
    assert "md failed" in result.stderr


def test_export_html_failure(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md = "```python {.marimo}\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch(
            "marimo_md_export.cli.export_html", side_effect=RuntimeError("html failed")
        ):
            result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 1
    assert "marimo export html failed:" in result.stderr
    assert "html failed" in result.stderr


def test_html_output_writes_file(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    html_output = tmp_path / "output.html"
    md = "```python {.marimo}\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs",
                    return_value=(md, []),
                ):
                    _ = runner.invoke(
                        app,
                        [str(notebook), str(output), "--html-output", str(html_output)],
                    )
    assert html_output.exists()
    assert html_output.read_bytes() == b"<html></html>"


def test_verbose_flag(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md = "```python {.marimo}\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs",
                    return_value=(md, []),
                ):
                    result = runner.invoke(app, [str(notebook), str(output), "-v"])
    assert "Exporting markdown:" in result.output
    assert "Found 1 cell(s), 0 suppressed" in result.output
    assert "Exporting HTML:" in result.output
    assert "Wrote" in result.output


def test_html_output_verbose(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    html_output = tmp_path / "output.html"
    md = "```python {.marimo}\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs",
                    return_value=(md, []),
                ):
                    result = runner.invoke(
                        app,
                        [
                            str(notebook),
                            str(output),
                            "--html-output",
                            str(html_output),
                            "-v",
                        ],
                    )
    assert "Wrote" in result.output


def test_overflow_scroll(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md = "```python {.marimo}\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs",
                    return_value=(md, []),
                ):
                    result = runner.invoke(
                        app,
                        [str(notebook), str(output), "--overflow", "scroll"],
                    )
    assert result.exit_code == 0


def test_overflow_invalid(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md = "```python {.marimo}\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            result = runner.invoke(
                app,
                [str(notebook), str(output), "--overflow", "invalid"],
            )
    assert result.exit_code == 2
    assert (
        "Invalid overflow value" in result.output
        or "Invalid overflow value" in result.stderr
    )


def test_figures_dir_writes_files(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md = "```python {.marimo}\nfig\n```"
    injected = md + '\n\n<img src="' + _PNG_DATA + '" alt="png">\n'
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs",
                    return_value=(injected, []),
                ):
                    result = runner.invoke(
                        app,
                        [str(notebook), str(output), "--figures-dir", "figures", "-v"],
                    )
    assert result.exit_code == 0, result.output
    assert "Wrote 1 figure(s)" in result.output

    written = output.read_text()
    assert "![png](figures/output-1.png)" in written
    assert "data:image/png;base64," not in written
    assert (tmp_path / "figures" / "output-1.png").is_file()


def test_figures_dir_omitted_keeps_embedding(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md = "```python {.marimo}\nfig\n```"
    injected = md + '\n\n<img src="' + _PNG_DATA + '" alt="png">\n'
    with patch("marimo_md_export.cli.export_md", return_value=md):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs",
                    return_value=(injected, []),
                ):
                    result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 0, result.output
    assert "data:image/png;base64," in output.read_text()


class _FiguresExport(NamedTuple):
    output: Path
    figures_dir: Path
    cli_output: str


@pytest.fixture(scope="session")
def figures_export(tmp_path_factory, example_notebook) -> _FiguresExport:
    """Export the example notebook once with --figures-dir.

    Session-scoped because this shells out to marimo twice; the tests below
    only read the result.
    """
    directory = tmp_path_factory.mktemp("figures_export")
    output = directory / "output.md"

    result = runner.invoke(
        app, [str(example_notebook), str(output), "--figures-dir", "figures"]
    )
    assert result.exit_code == 0, result.output

    return _FiguresExport(output, directory / "figures", result.output)


def test_full_pipeline_with_figures_dir(figures_export):
    md = figures_export.output.read_text()
    assert "data:image" not in md, "no figure should remain embedded"
    assert "![png](figures/output-1.png)" in md

    figures = sorted(figures_export.figures_dir.iterdir())
    pngs = [p for p in figures if p.suffix == ".png"]
    assert len(pngs) >= 2, f"expected the matplotlib PNGs, got {figures}"
    assert {p.suffix for p in figures} <= {".png", ".svg"}
    assert all(p.stat().st_size > 0 for p in figures)

    assert "WARNING" not in figures_export.cli_output


@pytest.mark.requires_graphviz
def test_full_pipeline_with_figures_dir_writes_svg(figures_export):
    """The notebook's graphviz output must keep its native .svg extension."""
    svgs = [p for p in figures_export.figures_dir.iterdir() if p.suffix == ".svg"]
    assert len(svgs) == 1, f"expected one graphviz SVG, got {svgs}"
    assert "<svg" in svgs[0].read_text()
    assert f"![svg](figures/{svgs[0].name})" in figures_export.output.read_text()


def test_no_manage_script_metadata(tmp_path):
    notebook = tmp_path / "test_bad_dep.py"
    notebook.write_text(
        "# /// script\n"
        '# requires-python = ">=3.12"\n'
        '# dependencies = ["this-package-does-not-exist==99.0.0", "marimo"]\n'
        "# ///\n"
        "\n"
        "import marimo\n"
        "\n"
        "app = marimo.App()\n"
        "\n"
        "\n"
        "@app.cell\n"
        "def __():\n"
        '    print("hello")\n'
        "    return\n"
    )
    output = tmp_path / "output.md"

    result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 0, result.output
    assert "No solution found" not in result.stderr
    assert "hello" in output.read_text()
