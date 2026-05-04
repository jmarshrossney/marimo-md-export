from unittest.mock import patch

from marimo_md_export.export import export_html


def test_export_html_error_raises():
    completed = type("CompletedProcess", (), {"returncode": 1, "stderr": "error"})()
    with patch("marimo_md_export.export.subprocess.run", return_value=completed):
        import pytest

        with pytest.raises(RuntimeError, match="marimo export html failed:"):
            export_html("notebook.py")
