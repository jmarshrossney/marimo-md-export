from typer.testing import CliRunner
from unittest.mock import patch

from marimo_md_export.cli import app

runner = CliRunner()


def test_full_pipeline(tmp_path, example_notebook):
    notebook = example_notebook
    output = tmp_path / "output.md"

    result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 0, result.output

    md = output.read_text()

    assert "```python" in md, "markdown code blocks should be present"

    assert "<!-- @output:fig_wave -->" in md
    assert "data:image/png;base64," in md, "figure should be embedded as base64 PNG"

    assert "<!-- @output:table_summary -->" in md
    assert "|" in md or "<table" in md, "table should be present as GFM or HTML"

    assert "<!-- @output:text_stats -->" in md
    assert "<pre" in md, "text output should be wrapped in a pre block"

    assert "Figures" in md

    assert "WARNING" not in result.output

    docs_output = tmp_path / "example.md"
    docs_output.write_text(md)


def test_export_md_failure(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    with patch("marimo_md_export.cli.export_md", side_effect=RuntimeError("md failed")):
        result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 1
    assert "marimo export md failed:" in result.stderr
    assert "md failed" in result.stderr


def test_no_output_markers(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    with patch(
        "marimo_md_export.cli.export_md", return_value="markdown without markers"
    ):
        result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 2
    assert "no @output markers found" in result.stderr
    assert "Did you forget to add" in result.stderr


def test_export_html_failure(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    md_with_marker = "```python {.marimo}\n# @output: fig\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md_with_marker):
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
    md_with_marker = "```python {.marimo}\n# @output: fig\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md_with_marker):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs", return_value=md_with_marker
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
    md_with_marker = "```python {.marimo}\n# @output: fig\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md_with_marker):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs", return_value=md_with_marker
                ):
                    result = runner.invoke(app, [str(notebook), str(output), "-v"])
    assert "Exporting markdown:" in result.output
    assert "Found 1 @output marker(s): fig" in result.output
    assert "Exporting HTML:" in result.output
    assert "Wrote" in result.output


def test_html_output_verbose(tmp_path):
    notebook = tmp_path / "test.py"
    notebook.write_text("x = 1")
    output = tmp_path / "output.md"
    html_output = tmp_path / "output.html"
    md_with_marker = "```python {.marimo}\n# @output: fig\nfig\n```"
    with patch("marimo_md_export.cli.export_md", return_value=md_with_marker):
        with patch("marimo_md_export.cli.export_html", return_value=b"<html></html>"):
            with patch("marimo_md_export.cli.extract_outputs", return_value={}):
                with patch(
                    "marimo_md_export.cli.inject_outputs", return_value=md_with_marker
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
