from pathlib import Path

from typer.testing import CliRunner

from marimo_md_export.cli import app

runner = CliRunner()


def test_full_pipeline(tmp_path):
    notebook = Path("tests/integration/example.py")
    output = tmp_path / "output.md"

    result = runner.invoke(app, [str(notebook), str(output)])
    assert result.exit_code == 0, result.output

    md = output.read_text()

    assert "```python" in md, "markdown code blocks should be present"

    assert "<!-- @output:fig_wave -->" in md
    assert "data:image/png;base64," in md, "figure should be embedded as base64 PNG"

    assert "<!-- @output:table_summary -->" in md
    assert "|" in md or "<table" in md, "table should be present as GFM or HTML"

    assert "Interpretation" in md

    assert "WARNING" not in result.output

    docs_output = Path("docs/example.md")
    docs_output.parent.mkdir(exist_ok=True)
    docs_output.write_text(md)
