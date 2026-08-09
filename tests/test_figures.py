import base64
from pathlib import Path
from urllib.parse import quote

from marimo_md_export.figures import externalize_figures

_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)
_PNG_DATA = "data:image/png;base64," + base64.b64encode(_PNG_BYTES).decode()

_SVG_MARKUP = '<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>'
_SVG_DATA = f"data:image/svg+xml,{quote(_SVG_MARKUP, safe='')}"


def _img(src: str, alt: str = "png") -> str:
    return f'<img src="{src}" alt="{alt}">'


def test_png_written_and_linked(tmp_path):
    output = tmp_path / "example.md"
    md = f"# Title\n\n{_img(_PNG_DATA)}\n"

    result, written, warnings = externalize_figures(md, output, Path("figures"))

    assert warnings == []
    assert written == [tmp_path / "figures" / "example-1.png"]
    assert written[0].read_bytes() == _PNG_BYTES
    assert "![png](figures/example-1.png)" in result
    assert "data:" not in result


def test_raw_svg_written_as_svg_file(tmp_path):
    output = tmp_path / "example.md"
    md = f"{_img(_SVG_DATA, alt='svg+xml')}\n"

    result, written, warnings = externalize_figures(md, output, Path("figures"))

    assert warnings == []
    assert written == [tmp_path / "figures" / "example-1.svg"]
    assert written[0].read_text() == _SVG_MARKUP
    assert "![svg](figures/example-1.svg)" in result


def test_relative_dir_resolved_against_output_parent(tmp_path):
    output = tmp_path / "docs" / "page.md"
    output.parent.mkdir()
    md = f"{_img(_PNG_DATA)}\n"

    result, written, _ = externalize_figures(md, output, Path("assets/img"))

    assert written == [tmp_path / "docs" / "assets" / "img" / "page-1.png"]
    assert written[0].is_file()
    assert "![png](assets/img/page-1.png)" in result


def test_absolute_dir_gives_absolute_link(tmp_path):
    output = tmp_path / "example.md"
    figures_dir = tmp_path / "elsewhere" / "assets"
    md = f"{_img(_PNG_DATA)}\n"

    result, written, _ = externalize_figures(md, output, figures_dir)

    assert written == [figures_dir / "example-1.png"]
    assert f"![png]({figures_dir.as_posix()}/example-1.png)" in result


def test_nested_img_keeps_tag_and_repoints_src(tmp_path):
    output = tmp_path / "example.md"
    md = f"<table><tr><td>{_img(_PNG_DATA)}</td></tr></table>\n"

    result, written, _ = externalize_figures(md, output, Path("figures"))

    assert len(written) == 1
    assert '<img src="figures/example-1.png" alt="png">' in result
    assert "<table><tr><td>" in result
    assert "![png]" not in result
    assert "data:" not in result


def test_multiple_figures_numbered_in_document_order(tmp_path):
    output = tmp_path / "example.md"
    md = "\n\n".join([_img(_PNG_DATA), _img(_SVG_DATA, alt="svg+xml"), _img(_PNG_DATA)])

    result, written, _ = externalize_figures(md, output, Path("figures"))

    assert [p.name for p in written] == [
        "example-1.png",
        "example-2.svg",
        "example-3.png",
    ]
    assert result.index("example-1.png") < result.index("example-2.svg")
    assert result.index("example-2.svg") < result.index("example-3.png")


def test_malformed_base64_left_embedded_with_warning(tmp_path):
    output = tmp_path / "example.md"
    md = f"{_img('data:image/png;base64,!!!not-base64!!!')}\n"

    result, written, warnings = externalize_figures(md, output, Path("figures"))

    assert written == []
    assert len(warnings) == 1
    assert "could not decode" in warnings[0]
    assert "data:image/png;base64,!!!not-base64!!!" in result
    assert not (tmp_path / "figures").exists()


def test_malformed_data_uri_left_embedded_with_warning(tmp_path):
    output = tmp_path / "example.md"
    md = f"{_img('data:image/,nosubtype')}\n"

    result, written, warnings = externalize_figures(md, output, Path("figures"))

    assert written == []
    assert len(warnings) == 1
    assert "data:image/,nosubtype" in result


def test_no_images_does_not_create_directory(tmp_path):
    output = tmp_path / "example.md"
    md = "# Title\n\nJust text, and a `data:image/png` mention in prose.\n"

    result, written, warnings = externalize_figures(md, output, Path("figures"))

    assert result == md
    assert written == []
    assert warnings == []
    assert not (tmp_path / "figures").exists()


def test_unknown_image_mime_falls_back_to_subtype(tmp_path):
    output = tmp_path / "example.md"
    md = f"{_img('data:image/x-fake;base64,' + base64.b64encode(b'abc').decode())}\n"

    _, written, warnings = externalize_figures(md, output, Path("figures"))

    assert warnings == []
    assert written == [tmp_path / "figures" / "example-1.xfake"]
    assert written[0].read_bytes() == b"abc"


def test_indented_img_still_treated_as_own_line(tmp_path):
    output = tmp_path / "example.md"
    md = f"  {_img(_PNG_DATA)}  \n"

    result, _, _ = externalize_figures(md, output, Path("figures"))

    assert "![png](figures/example-1.png)" in result
