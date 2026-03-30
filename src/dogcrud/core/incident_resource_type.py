# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import override

import aiofiles
import orjson

from dogcrud.core import context, rest
from dogcrud.core.pagination import LimitOffsetPagination
from dogcrud.core.resource_type import IDType, ResourceType

logger = logging.getLogger(__name__)

_REST_BASE = "v2/incidents"

_PAGINATION = LimitOffsetPagination(
    limit=100,
    limit_query_param="page[size]",
    offset_query_param="page[offset]",
    items_key="data",
)


class IncidentResourceType(ResourceType):
    """
    Datadog Incident resource.

    List:   GET /api/v2/incidents            (page[size] / page[offset] pagination)
    Get:    GET /api/v2/incidents/{id}       (response wrapped in "data" key)
    Update: PATCH /api/v2/incidents/{id}    (PATCH, not PUT)

    The list endpoint returns the same "data" object per incident as the
    individual GET endpoint, so we cache each item from the list pages and
    serve it from get() without issuing a second HTTP request.

    https://docs.datadoghq.com/api/latest/incidents/
    """

    def __init__(self, max_concurrency: int, *, disabled: bool = False) -> None:
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self.disabled = disabled
        # Cache populated by list_ids(); maps incident ID -> raw {"data": ...} bytes
        self._cache: dict[IDType, bytes] = {}

    @override
    def rest_path(self, resource_id: IDType | None = None) -> str:
        match resource_id:
            case None:
                return _REST_BASE
            case _:
                return f"{_REST_BASE}/{resource_id}"

    @override
    def local_path(self, resource_id: IDType | None = None) -> Path:
        data_dir = context.config_context().data_dir
        match resource_id:
            case None:
                return data_dir / _REST_BASE
            case _:
                return data_dir / f"{_REST_BASE}/{resource_id}.json"

    @override
    async def get(self, resource_id: IDType) -> bytes:
        """
        Return the incident JSON. Uses the list-page cache when available
        (populated by list_ids()) so no additional HTTP request is needed.
        Falls back to the individual GET endpoint when called in isolation
        (e.g. ``dogcrud save v2/incidents <id>``).
        """
        if resource_id in self._cache:
            return self._cache.pop(resource_id)

        # Fallback: individual GET (e.g. single-item save)
        async with self.concurrency_semaphore:
            return await rest.get_json(f"api/{self.rest_path(resource_id)}")

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        async with self.concurrency_semaphore:
            await rest.patch_json(f"api/{self.rest_path(resource_id)}", data)

    @override
    def transform_get_to_put(self, data: bytes) -> bytes:
        """
        The GET response has shape {"data": {...}, "included": [...], ...}.
        The PATCH payload expects {"data": {...}}.
        Extract just the "data" key and re-wrap it.
        """
        parsed = orjson.loads(data)
        return orjson.dumps({"data": parsed["data"]})

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        async for page in _PAGINATION.pages(
            f"api/{self.rest_path()}", self.concurrency_semaphore
        ):
            for id_, item in zip(page.ids, page.items):
                # Wrap the item in {"data": ...} to match the individual GET shape
                self._cache[id_] = orjson.dumps({"data": item})
                yield id_

    @override
    async def read_local_json(self, resource_id: IDType) -> bytes:
        async with aiofiles.open(str(self.local_path(resource_id)), "rb") as file:
            return await file.read()

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        return f"https://app.datadoghq.com/incidents/{resource_id}"

    @override
    def resource_id(self, filename: str) -> IDType:
        return Path(filename).stem
