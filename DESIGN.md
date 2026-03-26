# Design

## Overview

`dogcrud` is a Python CLI tool that saves and restores Datadog resources (dashboards, monitors, SLOs, etc.) as JSON files on disk. Resources are fetched from the Datadog REST API and written locally with sorted keys and pretty-printing so they diff cleanly in version control. The reverse operation (restore) reads a local file and PUTs it back to Datadog.

---

## Code Structure

```
src/dogcrud/
├── cli/          # Click commands (user-facing)
│   ├── main.py   # CLI entry point, global options, context setup
│   ├── save.py   # dogcrud save <resource-type> <id|all>
│   ├── restore.py# dogcrud restore <filename>
│   ├── list.py   # dogcrud list <resource-type>
│   └── open.py   # dogcrud open <filename>
└── core/         # Business logic
    ├── resource_type.py          # ResourceType Protocol (the central interface)
    ├── standard_resource_type.py # Default implementation for most resources
    ├── resource_type_registry.py # Registry of all known resource types
    ├── pagination.py             # Pagination strategy implementations
    ├── rest.py                   # Low-level Datadog HTTP client
    ├── context.py                # ConfigContext and AsyncRunContext (contextvars)
    ├── data.py                   # JSON formatting and file utilities
    └── transformers.py           # GET-to-PUT data transformers
```

### ResourceType Protocol

`resource_type.py` defines `ResourceType`, a structural typing `Protocol` that all resource type implementations must satisfy. It covers the full lifecycle: listing all IDs, fetching and writing individual resources, transforming GET responses into PUT payloads, resolving local file paths, and building Datadog web UI URLs.

`StandardResourceType` is the concrete base class that covers most Datadog resources. When a resource needs non-standard behavior (a different HTTP method, compound IDs, a non-standard list endpoint, etc.) it subclasses `StandardResourceType` or implements `ResourceType` directly.

### Registry and Dynamic CLI Generation

`resource_type_registry.py` contains a single `resource_types()` function that returns all registered resource type instances. The CLI commands in `save.py` and `list.py` iterate this registry at startup and dynamically create a Click sub-command for each resource type — adding a resource to the registry automatically makes it available as a CLI command.

### Context System

Two context variables bridge Click's synchronous world to the async core:

- **`ConfigContext`** — set synchronously by the CLI entry point. Holds credentials, the data directory, concurrency limits, and feature flags.
- **`AsyncRunContext`** — created inside `asyncio.run()`. Holds the shared `aiohttp.ClientSession` and the global `BoundedSemaphore`.

`config_context().run_in_context(coro)` is the entry point from every CLI command into async execution.

### Data Pipeline

JSON is kept as raw `bytes` throughout the pipeline to avoid unnecessary parsing:

1. **Save**: `rest.get_json()` returns `bytes` → `orjson` parses and re-serializes with sorted keys and 2-space indent → written to disk with `aiofiles`
2. **Restore**: `aiofiles` reads the file as `bytes` → `transform_get_to_put()` reshapes if needed → `rest.put_json()` sends the bytes directly

The sorted-key formatting (`OPT_SORT_KEYS`) makes diffs predictable regardless of how Datadog orders fields in its API responses.

---

## Concurrency Model

The codebase uses pure `asyncio` — no threads, no multiprocessing.

### Fan-Out with TaskGroup

The `save all` and `list all` commands use `asyncio.TaskGroup` for structured concurrency at two levels:

1. One task per resource type (all types run concurrently)
2. Within each type, one task per resource ID (all IDs for that type run concurrently)

If any task raises an unhandled exception, `TaskGroup` cancels all siblings and surfaces the error.

### Two-Tier Semaphore Throttling

Without throttling, thousands of concurrent requests would overwhelm the Datadog API. Two semaphore layers prevent this:

| Layer | Semaphore | Default | Location |
|---|---|---|---|
| Global | `AsyncRunContext.concurrent_requests_semaphore` | 100 | Acquired inside every `rest.*_json()` call |
| Per-resource-type | `StandardResourceType.concurrency_semaphore` | Varies | Acquired inside `get()`, `put()`, and `list_ids()` |

Every API call passes through both semaphores. Per-type limits can be tuned independently — dashboards use `max_concurrency=20` because the dashboard API is more sensitive to bursts; most other types use 100.

### Rate Limit and Retry Handling

`rest.get_json()` handles transient API failures automatically:

- **HTTP 429**: sleeps for the duration specified in the `X-RateLimit-Reset` response header, then retries
- **HTTP 5xx**: retries up to 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s)
- **HTTP 400**: raises `DatadogAPIBadRequestError` (preserves the error body) immediately — no retry

### Non-Blocking I/O

- HTTP requests: `aiohttp` with a single shared `ClientSession`
- File reads/writes: `aiofiles`
- JSON formatting (CPU-bound): offloaded via `asyncio.to_thread` so it does not block the event loop

The CLI also raises the OS file descriptor limit to at least 4096 at startup to accommodate the large number of concurrent connections and open files.

---

## Adding a New Datadog REST Resource

### Step 1: Choose an implementation path

**Standard path** — use `StandardResourceType` directly if the resource follows a conventional REST pattern (list, GET by ID, PUT by ID):

```python
# In resource_type_registry.py, add to the tuple in resource_types():
StandardResourceType(
    rest_base_path="v2/my-resource",
    webpage_base_path="my-resource",
    max_concurrency=100,
    pagination_strategy=NoPagination(items_key="data"),
),
```

**Custom path** — subclass `StandardResourceType` or implement `ResourceType` directly when the resource needs non-standard behavior (e.g., compound IDs, a different HTTP method for updates, a non-standard list endpoint).

### Step 2: Choose a pagination strategy

| Strategy | Use when | Key parameters |
|---|---|---|
| `NoPagination` | The API returns all items in a single response | `items_key` — key in the response dict that holds the list (omit if the response is already a list) |
| `ItemOffsetPagination` | The API accepts a single offset parameter that advances by item count | `offset_query_param` — the query param name (e.g. `"start"`, `"offset"`); `items_key` |
| `LimitOffsetPagination` | The API accepts separate limit and offset parameters | `limit` (default 100); `limit_query_param`; `offset_query_param`; `items_key` |
| `IDOffsetPagination` | The API accepts the last-seen resource ID as the page cursor | `offset_query_param` — the query param name (e.g. `"id_offset"`); `items_key` |
| `CursorPagination` | The API returns a `links.next` URL in each response | `query_params` — any additional static query string to append to the first request |

`ItemOffsetPagination`, `LimitOffsetPagination`, and `IDOffsetPagination` all detect duplicate IDs across pages and log a warning — helpful during development to confirm the pagination parameters are correct.

`CursorPagination` returns `CursorPageModel` (a Pydantic model) rather than the `Page` dataclass used by the other strategies, so it requires a custom `list_ids()` implementation rather than the default one in `StandardResourceType`.

### Step 3: Handle GET-to-PUT shape differences (if needed)

Some Datadog APIs return a different JSON structure from GET than they accept for PUT. Supply a `get_to_put_transformer` to `StandardResourceType`:

- `transformers.identity` (default) — GET and PUT shapes are the same; pass bytes through unchanged
- `partial(data_at_key, "data")` — the GET response wraps the payload under a `"data"` key but PUT expects the unwrapped object (used by SLOs)

For more complex transformations, implement `transform_get_to_put(self, data: bytes) -> bytes` directly on a custom class.

### Step 4: Verify

After adding the resource to `resource_types()`, the save and list CLI commands are available immediately:

```sh
dogcrud list v2/my-resource
dogcrud save v2/my-resource all
dogcrud restore saved/v2/my-resource/<id>.json
```
