from unittest.mock import MagicMock, patch

from marimo_md_export.export import export_html


def test_export_html_error_raises():
    mock_result = MagicMock()
    mock_result.did_error = True

    with patch(
        "marimo_md_export.export.run_app_then_export_as_html",
        return_value=mock_result,
    ):
        with patch("marimo_md_export.export.parse_args", return_value=object()):
            import pytest

            with pytest.raises(
                RuntimeError, match="marimo HTML export reported errors"
            ):
                export_html("notebook.py")
