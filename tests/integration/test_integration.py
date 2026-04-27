import subprocess
from pathlib import Path


def test_full_pipeline(tmp_path):
    notebook = Path("tests/integration/demo_notebook.py")
    output = tmp_path / "output.md"

    result = subprocess.run(
        ["uv", "run", "marimo-md-export", str(notebook), str(output)],
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode()

    md = output.read_text()

    assert "```python" in md, "markdown code blocks should be present"

    assert "<!-- @output:fig_wave -->" in md
    assert "data:image/png;base64," in md, "figure should be embedded as base64 PNG"

    assert "<!-- @output:table_summary -->" in md
    assert "|" in md or "<table" in md, "table should be present as GFM or HTML"

    assert "Interpretation" in md

    assert "WARNING" not in result.stderr.decode()

    docs_output = Path("docs/index.md")
    docs_output.parent.mkdir(exist_ok=True)
    docs_output.write_text(md)
