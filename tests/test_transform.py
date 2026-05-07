from marimo_md_export.transform import convert_admonitions


def test_basic_with_title():
    md = "/// note | My Title\nThis is the content.\n///"
    result = convert_admonitions(md)
    assert result == '!!! note "My Title"\n    This is the content.\n'


def test_without_title():
    md = "/// warning\nThis is a warning.\n///"
    result = convert_admonitions(md)
    assert result == "!!! warning\n    This is a warning.\n"


def test_multiline_content():
    md = "/// tip\nLine one\nLine two\nLine three\n///"
    result = convert_admonitions(md)
    expected = "!!! tip\n    Line one\n    Line two\n    Line three\n"
    assert result == expected


def test_multiple_admonitions():
    md = "Text before\n\n/// note | First\nContent one\n///\n\n/// warning | Second\nContent two\n///\n\nText after"
    result = convert_admonitions(md)
    assert '!!! note "First"' in result
    assert '!!! warning "Second"' in result
    assert "    Content one" in result
    assert "    Content two" in result
    assert "Text before" in result
    assert "Text after" in result


def test_various_types():
    for admon_type in (
        "note",
        "warning",
        "danger",
        "tip",
        "info",
        "abstract",
        "example",
    ):
        md = f"/// {admon_type} | Title\nContent\n///"
        result = convert_admonitions(md)
        assert f'!!! {admon_type} "Title"' in result


def test_empty_content():
    md = "/// note | Empty\n///"
    result = convert_admonitions(md)
    assert result == '!!! note "Empty"\n'


def test_empty_content_no_title():
    md = "/// warning\n///"
    result = convert_admonitions(md)
    assert result == "!!! warning\n"


def test_content_with_code_fence():
    md = "/// info | Code example\nSome text\n```python\nx = 1\n```\nMore text\n///"
    result = convert_admonitions(md)
    expected = '!!! info "Code example"\n    Some text\n    ```python\n    x = 1\n    ```\n    More text\n'
    assert result == expected


def test_adjacent_to_code_block():
    md = "```python\nx = 1\n```\n\n/// note\nAfter code.\n///"
    result = convert_admonitions(md)
    assert "```python" in result
    assert "!!! note" in result
    assert "    After code." in result


def test_no_admonitions_passthrough():
    md = "# Heading\n\nSome paragraph with no admonitions.\n\n```python\nx = 1\n```"
    result = convert_admonitions(md)
    assert result == md


def test_triple_slash_in_code_not_converted():
    md = "```python\n# /// some comment\nx = 1\n```\n\n/// note\nReal admonition.\n///"
    result = convert_admonitions(md)
    assert "# /// some comment" in result
    assert "!!! note" in result


def test_title_with_special_characters():
    md = '/// note | A "quoted" title\nContent\n///'
    result = convert_admonitions(md)
    assert '!!! note "A \\"quoted\\" title"' in result


def test_whitespace_in_opening_line():
    md = "///   warning   |   Trimmed title   \nContent\n///"
    result = convert_admonitions(md)
    assert '!!! warning "Trimmed title"' in result
