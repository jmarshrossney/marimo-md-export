import pytest
from pathlib import Path


@pytest.fixture
def example_notebook() -> Path:
    return Path(__file__).parent.parent / "examples" / "notebook.py"
