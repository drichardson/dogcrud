# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import override

import aiofiles

from dogcrud.core import context, rest
from dogcrud.core.pagination import LimitOffsetPagination
from dogcrud.core.resource_type import IDType, ResourceType

logger = logging.getLogger(__name__)

_REST_BASE = "v2/incident-attachments"
_INCIDENTS_REST_BASE = "v2/incidents"

_INCIDENT_PAGINATION = LimitOffsetPagination(
    limit=100,
    limit_query_param="page[size]",
    offset_query_param="page[offset]",
    items_key="data",
)


class IncidentAttachmentResourceType(ResourceType):
    """
    Datadog Incident Attachments child resource.

    Attachments are 1:many with incidents. There is no standalone list endpoint;
    instead list_ids() enumerates all incident IDs and get() fetches the
    attachment list for each incident.

    List incidents: GET /api/v2/incidents              (page[size] / page[offset])
    Get:            GET /api/v2/incidents/{id}/attachments  (all attachments, one call)

    Files are saved at:
        saved/v2/incident-attachments/{incident_id}.json

    See "Child Resources (1:Many Relationships)" in DESIGN.md for the convention.

    https://docs.datadoghq.com/api/latest/incidents/#list-incident-attachments
    """

    def __init__(self, max_concurrency: int, *, disabled: bool = False) -> None:
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self.disabled = disabled

    @override
    def rest_path(self, resource_id: IDType | None = None) -> str:
        # rest_path() with no arg is used as the CLI command name and local
        # directory prefix. With an arg it becomes the actual API endpoint.
        match resource_id:
            case None:
                return _REST_BASE
            case _:
                return f"{_INCIDENTS_REST_BASE}/{resource_id}/attachments"

    @override
    def local_path(self, resource_id: IDType | None = None) -> Path:
        data_dir = context.config_context().data_dir
        match resource_id:
            case None:
                return data_dir / _REST_BASE
            case _:
                return data_dir / _REST_BASE / f"{resource_id}.json"

    @override
    async def get(self, resource_id: IDType) -> bytes:
        async with self.concurrency_semaphore:
            return await rest.get_json(f"api/{self.rest_path(resource_id)}")

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        raise NotImplementedError(
            "Incident attachments are read-only; restore is not supported."
        )

    @override
    def transform_get_to_put(self, data: bytes) -> bytes:
        raise NotImplementedError(
            "Incident attachments are read-only; restore is not supported."
        )

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        async for page in _INCIDENT_PAGINATION.pages(
            f"api/{_INCIDENTS_REST_BASE}", self.concurrency_semaphore
        ):
            for id_ in page.ids:
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
