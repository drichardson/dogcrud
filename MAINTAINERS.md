# Maintainers Guide

This package is developed using [uv](https://docs.astral.sh/uv/) and
[Task](https://taskfile.dev). Install both:

```sh
brew install uv go-task  # macOS
```

## Common tasks

Use `task` for day-to-day development (defined in `Taskfile.dist.yaml`):

```sh
task test                        # run tests (with coverage)
task typecheck                   # type checking
task lint                        # check formatting and lint
task format                      # auto-format code
task check                       # run all checks (lint + typecheck + test)
task install-git-hooks           # install pre-push hook (recommended for new contributors)
task version-bump -- patch       # bump patch version (e.g. 1.10.0 -> 1.10.1)
task version-bump -- minor       # bump minor version (e.g. 1.10.0 -> 1.11.0)
task version-bump -- major       # bump major version (e.g. 1.10.0 -> 2.0.0)
```

You can create a local `Taskfile.yaml` to override or extend tasks for your
own environment — it is gitignored.

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

## Updating `pyproject.toml`

When changing dependencies in `pyproject.toml`, run `uv lock` afterward to keep
`uv.lock` in sync. Commit both files together.

```sh
uv lock
git add pyproject.toml uv.lock
```

To bump the package version use `task version-bump` — it updates both files in one step:

```sh
task version-bump -- minor
git add pyproject.toml uv.lock
```

## Publishing

To publish a release to [PyPI](https://pypi.org/project/dogcrud/):

1. Create a PR to bump the version using `task version-bump -- minor` (or `patch`/`major`).
   Commit both `pyproject.toml` and `uv.lock` together.
2. Merge the PR to main
3. Go to [releases](https://github.com/drichardson/dogcrud/releases).
4. Draft a new release.
5. Create a new tag that matches the version in `pyproject.toml`.
6. Press _Generate release notes_.
7. Publish release
