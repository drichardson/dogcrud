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
- `hatch fmt` - lint and format code


### Example session

```console
$ hatch shell
$ dogcrud
Usage: dogcrud [OPTIONS] COMMAND [ARGS]...
```

## Publishing

To publish a release to [PyPI](https://pypi.org/project/dogcrud/):

1. Create a PR to bump the version. Run `hatch version` and then `hatch version NEW_VERSION` to bump.
2. Merge the PR to main
3. Go to [releases](https://github.com/drichardson/dogcrud/releases).
4. Draft a new release.
5. Create a new tag that matches the hatch version.
6. Press _Generate release notes_.
7. Publish release
