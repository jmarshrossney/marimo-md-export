# CLI Reference

::: mkdocs-typer2
    :module: marimo_md_export.cli
    :name: marimo-md-export


## Overwriting existing files

!!! warning "Existing files are overwritten by default."

    `marimo-md-export` invokes `marimo export` as a subprocess.
    To ensure fully non-interactive operation, `--force` is always passed to `marimo export`, suppressing file-overwrite prompts.

## Writing figures to files

By default, figures are embedded directly in the markdown as base64 data URIs, which keeps the page self-contained but makes it large.
Pass `--figures-dir` to write them out as image files instead:

```sh
marimo-md-export examples/notebook.py docs/example.md --figures-dir figures
```

This writes `docs/figures/example-1.png`, `docs/figures/example-2.svg`, and so on, and references them from the markdown with standard image syntax:

```md
![png](figures/example-1.png)
```

Files are named after the output file's stem, so several notebooks can safely share one figures directory.
Each image keeps its native format — matplotlib plots become `.png`, graphviz graphs become `.svg`, and so on; nothing is converted.

The path is interpreted relative to the directory containing the output file, so the links in the markdown are relative too and survive being served from any URL prefix.
Because they are ordinary markdown image links, your site generator resolves them exactly as it would any other relative link in your docs.

Give an absolute path if you'd rather write elsewhere; the links will then be absolute as well.

This project's own docs are built this way — see the `docs` recipe in the [justfile](https://github.com/jmarshrossney/marimo-md-export/blob/main/justfile).
