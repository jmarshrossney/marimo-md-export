from .cli import app as _app
from .version import __version__

__all__ = ["__version__", "main"]


def main() -> None:
    _app()
