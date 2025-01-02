# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import override

import aiofiles

from dogcrud.core import context, data, rest
from dogcrud.core.pagination import PaginationStrategy
from dogcrud.core.resource_type import IDType, ResourceType

logger = logging.getLogger(__name__)


class StandardResourceType(ResourceType):
    """
    A Datadog Resource that operates like a standard CRUD object (although we
    only do RU operations).
    """

    def __init__(
        self,
        rest_base_path: str,
        webpage_base_path: str,
        max_concurrency: int,
        pagination_strategy: PaginationStrategy,
    ) -> None:
        self.rest_base_path = rest_base_path
        self.webpage_base_path = webpage_base_path
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self.pagination_strategy = pagination_strategy

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
        async with self.concurrency_semaphore:
            return await rest.get_json(f"api/{self.rest_path(resource_id)}")

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        async with self.concurrency_semaphore:
            await rest.put_json(f"api/{self.rest_path(resource_id)}", data)

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        async for page in self.pagination_strategy.pages(f"api/{self.rest_path()}", self.concurrency_semaphore):
            for id_ in page.ids:
                yield id_

    @override
    async def read_local_json(self, resource_id: IDType) -> bytes:
        resource_dir = context.config_context().data_dir / self.rest_path(resource_id)
        filename = str(resource_dir / f"{resource_id}.json")

        resource = data.model_validate_json_file(data.ResourceWithId, filename)
        if resource_id != resource.id:
            msg = f"ID of file {resource_id} does not match ID inside file {resource.id}"
            raise ValueError(msg)

        async with aiofiles.open(filename, "rb") as file:
            return file.read()

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        return f"https://app.datadoghq.com/{self.webpage_base_path}/{resource_id}"
