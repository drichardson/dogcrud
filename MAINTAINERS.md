# Maintainers Guide

This package is developed using [Hatch](https://hatch.pypa.io/latest/). Install
Hatch and then you will use the following command durings development:

- `hatch env create` - see [Hatch
Environments](https://hatch.pypa.io/latest/environment/)
- `hatch shell` and then other commands like `python -m dogcrud.cli`
- `hatch run python -m dogcrud.cli.main`
- `hatch build` - see [Hatch Builds](https://hatch.pypa.io/latest/build/)
- `hatch test`
- `hatch run pip install -e .` to test installed build
