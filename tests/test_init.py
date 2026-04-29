import sys

import pytest


def test_init_main():
    from marimo_md_export import main

    # Calling main() with --help should exit with code 0
    # We need to mock sys.argv to pass --help
    with pytest.raises(SystemExit) as exc_info:
        import sys

        original_argv = sys.argv
        sys.argv = ["marimo_md_export", "--help"]
        try:
            main()
        finally:
            sys.argv = original_argv
    assert exc_info.value.code == 0


def test_main_module():
    # Use runpy to execute __main__.py with __name__ == "__main__"
    import runpy

    # Patch sys.argv for the --help argument
    original_argv = sys.argv
    sys.argv = ["marimo_md_export", "--help"]
    try:
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("marimo_md_export", run_name="__main__")
        assert exc_info.value.code == 0
    finally:
        sys.argv = original_argv
