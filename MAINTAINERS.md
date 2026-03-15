# Maintainers Guide

This package is developed using [uv](https://docs.astral.sh/uv/). You'll
need to install uv (e.g. `brew install uv` on macos).

## Some `uv` commands you will use

- `uv build` - build source and wheel distributions
- `uv run pytest` - run tests
- `uv run nvim` - open NeoVim in the development environment without activating a shell
- To clear out your environment, `rm -rf .venv`
- `uv run ruff format && uv run ruff check` - format and lint code


### Example session

```console
$ uv run dogcrud
Usage: dogcrud [OPTIONS] COMMAND [ARGS]...
```

## Publishing

To publish a release to [PyPI](https://pypi.org/project/dogcrud/):

1. Create a PR to bump the version. Edit `version` in `pyproject.toml`.
2. Merge the PR to main
3. Go to [releases](https://github.com/drichardson/dogcrud/releases).
4. Draft a new release.
5. Create a new tag that matches the version in `pyproject.toml`.
6. Press _Generate release notes_.
7. Publish release
