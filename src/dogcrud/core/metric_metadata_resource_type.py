# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import override

from pydantic import BaseModel

from dogcrud.core.metrics import list_metrics
from dogcrud.core.pagination import CursorDataItemModel, NoPagination
from dogcrud.core.resource_type import IDType
from dogcrud.core.standard_resource_type import StandardResourceType

logger = logging.getLogger(__name__)


class MetricMetadataModel(BaseModel):
    description: str | None
    integration: str | None
    per_unit: str | None
    short_name: str
    statsd_interval: int
    type: str
    unit: str


class MetricMetadataResourceType(StandardResourceType):
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
        super().__init__(
            rest_base_path="v1/metrics",
            webpage_base_path="metric/summary?metric=",
            max_concurrency=max_concurrency,
            pagination_strategy=NoPagination(),
        )
        self.rest_base_path = "v1/metrics"
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self._id_to_item_index: dict[IDType, CursorDataItemModel] = {}

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        async for metric in list_metrics(self.concurrency_semaphore):
            yield metric.id

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        return f"https://app.datadoghq.com/{self.webpage_base_path}{resource_id}"
