"""Markdown-to-markdown transformations for exported notebooks.

Functions in this module take the markdown produced by ``marimo export md``
and transform it for compatibility with downstream renderers like MkDocs
or Zensical.
"""

import re

_ADN_RE = re.compile(
    r"^///\s+(\w+)(?:\s*\|\s*(.*?))?\s*$\n(.*?)^///\s*$",
    re.MULTILINE | re.DOTALL,
)


def _convert_one(match: re.Match) -> str:
    admon_type = match.group(1)
    title = match.group(2)
    content = match.group(3)

    if title is not None:
        title = title.strip().replace('"', '\\"')
        header = f'!!! {admon_type} "{title}"'
    else:
        header = f"!!! {admon_type}"

    if not content.strip():
        return header + "\n"

    indented = "\n".join("    " + line for line in content.splitlines())
    return f"{header}\n{indented}\n"


def convert_admonitions(md: str) -> str:
    """Convert marimo-style admonitions to MkDocs/Zensical format.

    Transforms ``/// type | Title ... ///`` blocks into
    ``!!! type "Title"`` with 4-space-indented content.
    Omits the title (and quotes) when no title is provided.
    """
    return _ADN_RE.sub(_convert_one, md)
