import subprocess
from unittest.mock import patch

import pytest

from marimo_md_export.export import export_html, export_md, strip_header_from_frontmatter


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


class TestStripHeaderFromFrontmatter:
    def _wrap(self, inner: str, *, after: str = "") -> str:
        return f"---\n{inner}\n---\n{after}"

    def test_removes_header_block_scalar(self):
        md = self._wrap(
            "title: My Notebook\nmarimo-version: 0.23.3\nheader: |-\n  # /// script\n  # ///",
            after="Content here",
        )
        result = strip_header_from_frontmatter(md)
        assert "header:" not in result
        assert "title: My Notebook" in result
        assert "marimo-version: 0.23.3" in result
        assert "Content here" in result

    def test_removes_header_folded_scalar(self):
        md = self._wrap(
            "title: Test\nheader: >\n  some long\n  header text",
            after="Body",
        )
        result = strip_header_from_frontmatter(md)
        assert "header:" not in result
        assert "title: Test" in result
        assert "Body" in result

    def test_removes_header_plain_value(self):
        md = self._wrap("title: Test\nheader: some-value", after="Body")
        result = strip_header_from_frontmatter(md)
        assert "header" not in result
        assert "title: Test" in result
        assert "Body" in result

    def test_removes_header_empty_value(self):
        md = self._wrap("title: Test\nheader:", after="Body")
        result = strip_header_from_frontmatter(md)
        assert "header" not in result
        assert "title: Test" in result

    def test_drops_frontmatter_if_only_title_remains(self):
        md = self._wrap("title: Test\nheader: |-\n  line1\n  line2", after="Body")
        result = strip_header_from_frontmatter(md)
        assert result.startswith("---\n")
        assert "title: Test" in result
        assert "header" not in result

    def test_drops_frontmatter_if_empty_after_removal(self):
        md = self._wrap("header: |-\n  line1\n  line2", after="Body")
        result = strip_header_from_frontmatter(md)
        assert not result.startswith("---")
        assert result.startswith("Body")

    def test_no_header_key_returns_unchanged(self):
        md = self._wrap("title: Test\nmarimo-version: 0.1", after="Content")
        result = strip_header_from_frontmatter(md)
        assert result == md

    def test_no_frontmatter_returns_unchanged(self):
        md = "Just content\nNo frontmatter"
        result = strip_header_from_frontmatter(md)
        assert result == md

    def test_unclosed_frontmatter_returns_unchanged(self):
        md = "---\ntitle: Test\nContent without closing"
        result = strip_header_from_frontmatter(md)
        assert result == md