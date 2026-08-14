from pathlib import Path
from typing import NamedTuple

import pytest
from typer.testing import CliRunner
from unittest.mock import patch

from marimo_md_export import __version__
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

    assert "data:image/png;base64," not in md, "figures should not be embedded"
    assert "![png](output_assets/figure-1.png)" in md
    assert "|" in md or "<table" in md, "table should be present as GFM or HTML"
    assert "<pre" in md, "text output should be wrapped in a pre block"

    assert "Figures" in md

    assets = tmp_path / "output_assets"
    assert assets.is_dir()
    assert (assets / "notebook.html").is_file()
    pngs = sorted(p for p in assets.iterdir() if p.suffix == ".png")
    assert len(pngs) >= 2, f"expected matplotlib PNGs, got {list(assets.iterdir())}"
    assert all(p.stat().st_size > 0 for p in pngs)

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


def test_keep_html_default_writes_notebook_html(tmp_path):
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
                    result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 0, result.output
    html_path = tmp_path / "output_assets" / "notebook.html"
    assert html_path.is_file()
    assert html_path.read_bytes() == b"<html></html>"


def test_no_keep_html_discards_html(tmp_path):
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
                        app, [str(notebook), str(output), "--no-keep-html"]
                    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "output_assets").is_dir()
    assert not (tmp_path / "output_assets" / "notebook.html").exists()


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
    assert "notebook.html" in result.output


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


def test_version_flag():
    # --version is eager, so it prints and exits before the required
    # notebook/output arguments are validated.
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0, result.output
    assert result.output.strip() == __version__


def test_default_externalizes_figures(tmp_path):
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
                        [str(notebook), str(output), "-v"],
                    )
    assert result.exit_code == 0, result.output
    assert "Wrote 1 figure(s)" in result.output

    written = output.read_text()
    assert "![png](output_assets/figure-1.png)" in written
    assert "data:image/png;base64," not in written
    assert (tmp_path / "output_assets" / "figure-1.png").is_file()
    assert (tmp_path / "output_assets" / "notebook.html").is_file()


def test_self_contained_keeps_embedding(tmp_path):
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
                        app, [str(notebook), str(output), "--self-contained"]
                    )
    assert result.exit_code == 0, result.output
    assert "data:image/png;base64," in output.read_text()
    assert (tmp_path / "output_assets" / "notebook.html").is_file()
    assert not (tmp_path / "output_assets" / "figure-1.png").exists()


def test_no_keep_html_self_contained_no_assets_dir(tmp_path):
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
                        [
                            str(notebook),
                            str(output),
                            "--no-keep-html",
                            "--self-contained",
                        ],
                    )
    assert result.exit_code == 0, result.output
    assert "data:image/png;base64," in output.read_text()
    assert not (tmp_path / "output_assets").exists()


def test_assets_dir_custom(tmp_path):
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
                        [str(notebook), str(output), "--assets-dir", "custom"],
                    )
    assert result.exit_code == 0, result.output
    assert "![png](custom/figure-1.png)" in output.read_text()
    assert (tmp_path / "custom" / "figure-1.png").is_file()
    assert (tmp_path / "custom" / "notebook.html").is_file()


class _AssetsExport(NamedTuple):
    output: Path
    assets_dir: Path
    cli_output: str


@pytest.fixture(scope="session")
def assets_export(tmp_path_factory, example_notebook) -> _AssetsExport:
    """Export the example notebook once with default assets behaviour.

    Session-scoped because this shells out to marimo twice; the tests below
    only read the result.
    """
    directory = tmp_path_factory.mktemp("assets_export")
    output = directory / "output.md"

    result = runner.invoke(app, [str(example_notebook), str(output)])
    assert result.exit_code == 0, result.output

    return _AssetsExport(output, directory / "output_assets", result.output)


def test_full_pipeline_with_assets_dir(assets_export):
    md = assets_export.output.read_text()
    assert "data:image" not in md, "no figure should remain embedded"
    assert "![png](output_assets/figure-1.png)" in md

    figures = sorted(
        p for p in assets_export.assets_dir.iterdir() if p.suffix in {".png", ".svg"}
    )
    pngs = [p for p in figures if p.suffix == ".png"]
    assert len(pngs) >= 2, f"expected the matplotlib PNGs, got {figures}"
    assert {p.suffix for p in figures} <= {".png", ".svg"}
    assert all(p.stat().st_size > 0 for p in figures)
    assert (assets_export.assets_dir / "notebook.html").is_file()

    assert "WARNING" not in assets_export.cli_output


@pytest.mark.requires_graphviz
def test_full_pipeline_with_assets_dir_writes_svg(assets_export):
    """The notebook's graphviz output must keep its native .svg extension."""
    svgs = [p for p in assets_export.assets_dir.iterdir() if p.suffix == ".svg"]
    assert len(svgs) == 1, f"expected one graphviz SVG, got {svgs}"
    assert "<svg" in svgs[0].read_text()
    assert f"![svg](output_assets/{svgs[0].name})" in assets_export.output.read_text()


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

    result = runner.invoke(app, [str(notebook), str(output), "--no-keep-html"])
    assert result.exit_code == 0, result.output
    assert "No solution found" not in result.stderr
    assert "hello" in output.read_text()
