# dogcrud

`dogcrud` is a command line tool for working with Datadog CRUD resources, like
dashboards, monitors, and log pipelines.

[![CI - Test](https://github.com/drichardson/dogcrud/actions/workflows/ci.yaml/badge.svg)](https://github.com/drichardson/dogcrud/actions/workflows/ci.yaml)
[![PyPI - Version](https://img.shields.io/pypi/v/dogcrud.svg)](https://pypi.org/project/dogcrud)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dogcrud.svg)](https://pypi.org/project/dogcrud)


## Installation

The recommended installation is to use [uv](https://docs.astral.sh/uv/guides/tools/), a tool
for installing Python based command line tools like `dogcrud`.

```console
uv tool install dogcrud
```


# Usage

Save all Datadog sources supported by `dogcrud`:

```console
dogcrud save all
```

Run `dogcrud` to see how to restore and open saved JSON files.

# Shell Completion

`dogcrud` supports command line completion.

For `bash`, add this to `~/.bashrc`:

```bash
eval "$(_DOGCRUD_COMPLETE=bash_source dogcrud)"
```

For `zsh`, add this to `~/.zshrc`:

```zsh
eval "$(_DOGCRUD_COMPLETE=zsh_source dogcrud)"
```

For `fish`, add this to `~/.config/fish/completions/dogcrud.fish`:

```fish
_DOGCRUD_COMPLETE=fish_source dogcrud | source
```
