# Contributing

Contributions are welcome, but before you spend time on something, please read this file, which explains what this project is for and what is likely to be merged.

## What this project is

`marimo-md-export` is a stop-gap solution to the simple problem of wanting to include marimo notebooks in markdown-based (mkdocs, zensical) documentation.
It exists because there is currently no good way to get a marimo notebook's rendered outputs into a markdown page.
When official tooling catches up — [mkdocs-marimo](https://github.com/marimo-team/mkdocs-marimo), or a better markdown exporter from the marimo developers — this tool should become unnecessary, and I would rather it retire than grow.

I maintain it in my limited free time, and add features to serve my own documentation needs.

## Feature requests

Open them.
Genuinely — I want to know what people are hitting.

But **please calibrate your expectations**: a feature that isn't on my own critical path is unlikely to get implemented soon, or at all.
If you can offer to write the pull request yourself, say so in the issue and it becomes far more likely to happen.
If you can't, open the issue anyway; someone else may pick it up.

## Pull requests

Open them against `main`.
Make sure the pre-commit hooks pass and `just` runs clean.

The goal is simplicity.
The package is around 1400 lines across nine small modules, and I want to keep it in that range.
A pull request that adds a lot of machinery for a narrow feature will get a request to slim it down, even if the feature itself is a good idea.
If your change needs a new dependency, new abstraction layer, or a new configuration surface, say why in the PR description.

## Possible HTML-first rewrite

There is a standing idea in [issue #9](https://github.com/jmarshrossney/marimo-md-export/issues/9): stop injecting HTML chunks into `marimo export md`, and instead build the markdown from the HTML export alone.

If you find yourself designing something complicated to support a feature, check whether the rewrite would make it fall out naturally.
If it would, add a comment to issue #9 saying so and link your issue or PR.
Those data points are what will decide whether the rewrite is worth doing.

## Using AI

Contributions which make use of AI are welcome.
I use AI heavily on this project, since it's not my area of programming expertise (or interest) at all.

I ask only that you do these two things:

1. **Disclose it.** One line in the issue, PR or comment is enough: "I used Claude to help me understand the code and draft this."

2. **Mark which parts are copy-pasted from a model and which you wrote yourself.** A short note like "everything below the line is model output" is sufficient.

This is not about deterring AI users or embarrassing anyone, I promise.

I just need to know when a sentence carries human intent behind it.
E.g. "I'm happy to open a PR for this" means something different depending on whether a person typed it or a model generated it, and I can't tell from the text alone.

Thanks.
