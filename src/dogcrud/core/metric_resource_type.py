# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import override

import aiofiles

from dogcrud.core import context
from dogcrud.core.pagination import CursorDataItemModel, CursorPagination
from dogcrud.core.resource_type import IDType, ResourceType

logger = logging.getLogger(__name__)


class MetricResourceType(ResourceType):
    """
    A Datadog metric resource. This resource doesn't fit in with a StandardResourceType since
    - you have an idea of "active" metrics that the initial list is populated from from a time range
    - you get a list of metrics with a subset of metadata
    - there is no get ID list and get specific resource json like StandardResourceType
    """

    def __init__(
        self,
        max_concurrency: int,
    ) -> None:
        self.rest_base_path = "v2/metrics"
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self._id_to_item_index: dict[IDType, CursorDataItemModel] = {}

    @override
    def rest_path(self, resource_id: IDType | None = None) -> str:
        match resource_id:
            case None:
                return self.rest_base_path
            case _:
                return f"{self.rest_base_path}/{resource_id}"

    @override
    def local_path(self, resource_id: IDType | None = None) -> Path:
        data_dir = context.config_context().data_dir
        match resource_id:
            case None:
                return data_dir / self.rest_path()
            case _:
                return data_dir / f"{self.rest_path(resource_id)}.json"

    @override
    async def get(self, resource_id: IDType) -> bytes:
        # TODO: load _id_to_index_item if not yet set
        return self._id_to_item_index[resource_id].json().encode("utf-8")

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        raise NotImplementedError

    @override
    def transform_get_to_put(self, data: bytes) -> bytes:
        return data

    async def _list_ids(self, cursor_pagination: CursorPagination) -> AsyncGenerator[IDType]:
        async for page in cursor_pagination.pages(f"api/{self.rest_path()}", self.concurrency_semaphore):
            for item in page.data:
                self._id_to_item_index[item.id] = item
                yield item.id

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        # data[i].attributes is only set when filter[configured]=true is set,
        # so do 2 paginations—one with false and one with true—in order to get
        # the attributes.
        for configured in ("false", "true"):
            p = CursorPagination(query_params=f"filter[configured]={configured}")
            async for id_ in self._list_ids(p):
                yield id_

    @override
    async def read_local_json(self, resource_id: IDType) -> bytes:
        resource_dir = context.config_context().data_dir / self.rest_path(resource_id)
        filename = str(resource_dir / f"{resource_id}.json")

        async with aiofiles.open(filename, "rb") as file:
            return await file.read()

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        return f"https://app.datadoghq.com/metric/summary?metric={resource_id}"

    @override
    def resource_id(self, filename: str) -> IDType:
        return Path(filename).stem
