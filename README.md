# dogcrud

`dogcrud` is a command line tool for working with Datadog CRUD resources, like
dashboards, monitors, and log pipelines.

[![PyPI - Version](https://img.shields.io/pypi/v/dogcrud.svg)](https://pypi.org/project/dogcrud)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dogcrud.svg)](https://pypi.org/project/dogcrud)


## Installation

```console
pip install dogcrud
```

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
