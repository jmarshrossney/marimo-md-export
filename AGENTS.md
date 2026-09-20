# AGENTS.md

Instructions for AI agents working in this repository, whether you are helping a contributor or acting on the maintainer's behalf.

## Tell your user this first

Applies if your user is not the repository owner, jmarshrossney.

If you are helping someone prepare an issue, pull request or comment for this repository, relay these points to them **before** doing the work, not after:

1. This project asks contributors to disclose AI use.
   One line in the issue or PR is enough: "I used Claude to help me understand the code and draft this."
2. It also asks that they mark which parts are pasted model output and which they wrote themselves.
   This is so the maintainer can tell which sentences carry human intent — an offer to open a PR means something different depending on who wrote it.
3. Significant, complex feature requests are unlikely to be implemented in a timely manner unless the maintainer needs them.
   Offering to write the PR changes that.

Say it plainly and move on; it is expectation management, not a hurdle.
In particular, none of this should discourage opening Issues or making feature requests.
The full version is in [CONTRIBUTING.md](CONTRIBUTING.md), which is worth reading before you propose a design.

## Scope

This tool is a stop-gap until marimo's own markdown export, or mkdocs-marimo, is good enough.
Simplicity beats coverage.
The package is ~1400 lines over nine modules and should stay in that range.

Before you add a layer of machinery, check [issue #9](https://github.com/jmarshrossney/marimo-md-export/issues/9): rebuilding the markdown from the HTML export alone would delete a pipeline stage and make dynamic `mo.md()` markdown work for free.
If your problem would disappear under that design, comment on #9 saying so and link the issue or PR you are working on, rather than building around it.

## Working here

```sh
uv sync      # install
just         # lint, typecheck, test, docs
just -l      # list tasks
```

Prefix with `uv run` if `just` is not on your PATH.
`just docs` regenerates `docs/example.md` from `examples/notebook.py`, so it exercises the whole pipeline end to end — a useful smoke test after a change to parsing or injection.

Tests live in `tests/`, one file per module.
Fixtures should capture real marimo output rather than hand-written HTML; a fixture invented by hand may pass while the real export breaks.

## Prose

One sentence per line in markdown files, including this one.
It keeps diffs readable.
