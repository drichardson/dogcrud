# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, override

import aiofiles
from pydantic import BaseModel

from dogcrud.core import context, rest
from dogcrud.core.metrics import list_metrics
from dogcrud.core.resource_type import IDType, ResourceType

if TYPE_CHECKING:
    from dogcrud.core.pagination import CursorDataItemModel

logger = logging.getLogger(__name__)


class MetricTagAggregationModel(BaseModel):
    space: str
    time: str


class MetricTagAttributesModel(BaseModel):
    aggregations: list[MetricTagAggregationModel] | None = None
    exclude_tags_mode: bool | None = None
    include_percentiles: bool | None = None
    metric_type: str | None
    tags: list[str] | None = None


class MetricTagDataModel(BaseModel):
    attributes: MetricTagAttributesModel | None = None
    id: str
    type: str


class MetricTagModel(BaseModel):
    data: MetricTagDataModel


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
        *,
        disabled: bool = False,
    ) -> None:
        self.rest_base_path = "v2/metrics"
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self._id_to_item_index: dict[IDType, CursorDataItemModel] = {}
        self.disabled = disabled

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
                return data_dir / self.rest_base_path
            case _:
                return data_dir / f"{self.rest_base_path}/{resource_id}.json"

    @override
    async def get(self, resource_id: IDType) -> bytes:
        # TODO: load _id_to_index_item if not yet set
        return self._id_to_item_index[resource_id].json().encode("utf-8")

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        url = f"api/v2/metrics/{resource_id}/tags"
        async with self.concurrency_semaphore:
            await rest.patch_json(url, data)

    @override
    def transform_get_to_put(self, data: bytes) -> bytes:
        metric_tag_data = MetricTagDataModel.model_validate_json(data)
        metric_tag = MetricTagModel(data=metric_tag_data)
        return metric_tag.model_dump_json(exclude_none=True).encode()

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        async for metric in list_metrics(self.concurrency_semaphore):
            self._id_to_item_index[metric.id] = metric
            yield metric.id

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
