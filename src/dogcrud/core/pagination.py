# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Protocol, override

import orjson

from dogcrud.core.resource_type import IDType
from dogcrud.core.rest import get_json

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Page:
    ids: Sequence[IDType]


class PaginationStrategy(Protocol):
    def pages(self, url: str, concurrency_semaphore: asyncio.Semaphore) -> AsyncIterator[Page]: ...


async def _get_page(url: str, items_key: str | None) -> Page:
    json = await get_json(url)
    parsed_json = orjson.loads(json)

    match (parsed_json, items_key):
        case list(), None:
            items = parsed_json
        case dict(), items_key if items_key is not None:
            items = parsed_json[items_key]
        case _, _:
            msg = f"Invalid combination of page response type {type(parsed_json)} and items key '{items_key}'"
            raise RuntimeError(msg)

    ids = [item["id"] for item in items]
    return Page(ids=ids)


@dataclass(frozen=True)
class ItemOffsetPagination(PaginationStrategy):
    """
    A pagination strategy based on offsets.

    Attributes:
        offset_query_param: The name of the query parameter for the offset.
        items_key: If the page response is an object, this is the key to the list of items. Use None if the response is already a list.
    """

    offset_query_param: str
    items_key: str | None = None

    @override
    async def pages(self, url: str, concurrency_semaphore: asyncio.Semaphore) -> AsyncIterator[Page]:
        offset = 0
        seen_ids: set[IDType] = set()
        while True:
            async with concurrency_semaphore:
                page = await _get_page(f"{url}?{self.offset_query_param}={offset}", self.items_key)
            if not page.ids:
                return
            yield page
            offset += len(page.ids)
            new_ids = set(page.ids)
            if already_seen_ids := new_ids & seen_ids:
                logger.warning(
                    f"Duplicate IDs seen while paging. If transient okay to ignore cause it might be someone else mutating the list of items. already_seen_ids={already_seen_ids}. If not transient, this could be a misconfiguration of the pagination_strategy."
                )
            seen_ids |= new_ids


@dataclass(frozen=True)
class IDOffsetPagination(PaginationStrategy):
    """
    A pagination strategy based on last seen ID.

    Attributes:
        offset_query_param: The name of the query parameter for the offset.
        items_key: If the page response is an object, this is the key to the list of items. Use None if the response is already a list.
    """

    offset_query_param: str
    items_key: str | None = None

    @override
    async def pages(self, url: str, concurrency_semaphore: asyncio.Semaphore) -> AsyncIterator[Page]:
        id_offset: IDType = "0"
        offset = 0
        seen_ids: set[IDType] = set()
        while True:
            async with concurrency_semaphore:
                page = await _get_page(f"{url}?{self.offset_query_param}={id_offset}", self.items_key)
            if not page.ids:
                return
            yield page
            id_offset = page.ids[-1]
            offset += len(page.ids)
            new_ids = set(page.ids)
            if already_seen_ids := new_ids & seen_ids:
                logger.warning(
                    f"Duplicate IDs seen while paging. If transient okay to ignore cause it might be someone else mutating the list of items. already_seen_ids={already_seen_ids}. If not transient, this could be a misconfiguration of the pagination_strategy."
                )
            seen_ids |= new_ids


@dataclass(frozen=True)
class NoPagination(PaginationStrategy):
    """
    A pagination strategy that fetches everything in one go.

    Attributes:
        items_key: If the page response is an object, this is the key to the list of items. Use None if the response is already a list.
    """

    items_key: str | None = None

    @override
    async def pages(self, url: str, concurrency_semaphore: asyncio.Semaphore) -> AsyncIterator[Page]:
        async with concurrency_semaphore:
            page = await _get_page(url, self.items_key)
        yield page
