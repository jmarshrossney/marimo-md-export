import subprocess
from unittest.mock import patch

import pytest

from marimo_md_export.export import export_html, export_md


def _failed_result(stderr: str = "error") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["marimo"], returncode=1, stdout="", stderr=stderr
    )


def test_export_html_error_raises():
    with patch(
        "marimo_md_export.export._run_with_visible_output",
        return_value=_failed_result("something went wrong"),
    ):
        with pytest.raises(RuntimeError, match="marimo export html failed:"):
            export_html("notebook.py")


def test_export_md_error_raises():
    with patch(
        "marimo_md_export.export._run_with_visible_output",
        return_value=_failed_result("md fail"),
    ):
        with pytest.raises(RuntimeError, match="marimo export md failed:"):
            export_md("notebook.py")


def test_export_html_timeout_raises():
    with patch(
        "marimo_md_export.export._run_with_visible_output",
        side_effect=subprocess.TimeoutExpired(cmd="marimo", timeout=10),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            export_html("notebook.py", timeout=10)


def test_export_md_timeout_raises():
    with patch(
        "marimo_md_export.export._run_with_visible_output",
        side_effect=subprocess.TimeoutExpired(cmd="marimo", timeout=10),
    ):
        with pytest.raises(RuntimeError, match="timed out"):
            export_md("notebook.py", timeout=10)