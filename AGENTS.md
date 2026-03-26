# Agents Guide

Read `DESIGN.md` first for an understanding of the codebase structure, concurrency model, and how to add new Datadog REST resources.

## Development Commands

```sh
uv run pytest                          # run tests
uv run mypy src                        # type checking
uv run ruff format && uv run ruff check  # format and lint
```

## Conventions

- **Python 3.12+** — use modern syntax: `type` aliases, `match` statements, `asyncio.TaskGroup`.
- **Async-first** — all network and file I/O must be non-blocking. Use `aiohttp` for HTTP, `aiofiles` for file I/O, and `asyncio.to_thread` for CPU-bound work.
- **Raw bytes pipeline** — keep JSON as `bytes` throughout. Don't decode to a `dict` unless the logic genuinely requires it.
- **`orjson` not `json`** — use `orjson` for all JSON serialization and deserialization.
- **Structural typing** — prefer `Protocol` over inheritance for interfaces.
- **No new top-level CLI options without discussion** — global options in `cli/main.py` affect all commands and concurrency behavior.

## Adding a New Resource Type

See the _Adding a New Datadog REST Resource_ section in `DESIGN.md` for the full walkthrough. The short version:

1. Pick a pagination strategy from `pagination.py` (`NoPagination`, `ItemOffsetPagination`, `LimitOffsetPagination`, `IDOffsetPagination`, or `CursorPagination`).
2. Add a `StandardResourceType(...)` entry to the tuple in `resource_type_registry.py`. For non-standard APIs, subclass `StandardResourceType` or implement `ResourceType` directly.
3. If the GET response shape differs from what PUT expects, supply a `get_to_put_transformer`.
4. Verify with `uv run dogcrud list <rest-path>` and `uv run dogcrud save <rest-path> all`.

## When making changes always use Pull Requests

1. Create a branch
2. Push to a PR.

Don't push to main. You can make several commits but never push them to main, always to a branch.
