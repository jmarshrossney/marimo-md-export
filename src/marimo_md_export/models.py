from dataclasses import dataclass


@dataclass
class MarkedCell:
    """A fenced code block in the markdown that carries an @output marker."""
    label: str
    source: str
    # MD5 hex digest of source.strip() — matches marimo's code_hash in HTML export
    source_hash: str
    block_text: str


@dataclass
class ExtractedOutput:
    """The rendered output scraped from the HTML export for one cell."""
    label: str
    raw_html: str
    output_type: str  # "figure" | "table" | "text" | "unknown"
