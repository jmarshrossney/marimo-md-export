from dataclasses import dataclass, field


@dataclass
class Cell:
    """A fenced code block in the markdown export."""

    source: str
    source_hash: str
    block_text: str
    suppressed: bool = False
    overflow: str | None = None


@dataclass
class ExtractedOutput:
    """The rendered output scraped from the HTML export for one cell."""

    raw_html: str
    output_type: str
    cell_id: str = ""
    console_html: str = field(default="")
    stderr_html: str = field(default="")
    media_html: str = field(default="")
