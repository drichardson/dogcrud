# Maintainers Guide

This package is developed using [Hatch](https://hatch.pypa.io/latest/). You'll
need to install hatch (e.g. `brew install hatch` on macos).


## Some `hatch` commands you will use

- `hatch shell` - to setup the environment (if necessary) and enter a
development environment so that you can run `dogcrud` while making changes on
the source. Environments](https://hatch.pypa.io/latest/environment/)
- `hatch build` - to build source and wheel distributions. See [Hatch
Builds](https://hatch.pypa.io/latest/build/)
- `hatch test` - to run tests (at the time of this writing, there are none)
- `hatch run nvim` - open up NeoVim in the same environment you're developing
in. You can also run nvim after `hatch shell`, but if you have a complex
terminal setup, this can interfere.
- If you want to clear out your environment, `exit` and then run `hatch env remove`.


## Example session

```console
$ hatch shell
$ dogcrud
Usage: dogcrud [OPTIONS] COMMAND [ARGS]...
```
