import shutil
import pytest
from pathlib import Path

_HAVE_GRAPHVIZ = shutil.which("dot") is not None


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "requires_graphviz: needs the graphviz `dot` binary, an optional system "
        "dependency of the example notebook",
    )


def pytest_collection_modifyitems(items):
    """Skip graphviz-dependent tests when the `dot` binary is unavailable.

    The `graphviz` package in the examples group is only the Python wrapper;
    rendering needs the system binary, which CI does not install.
    """
    if _HAVE_GRAPHVIZ:
        return
    skip = pytest.mark.skip(reason="requires the graphviz `dot` binary")
    for item in items:
        if "requires_graphviz" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def example_notebook() -> Path:
    return Path(__file__).parent.parent / "examples" / "notebook.py"
