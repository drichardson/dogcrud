# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Protocol

type IDType = int | str


class ResourceType(Protocol):
    """
    A Datadog resource type that can have multiple instances, like dashboards,
    monitors, and metrics.
    """

    def rest_path(self, resource_id: IDType | None = None) -> str: ...
    def local_path(self, resource_id: IDType | None = None) -> Path: ...
    async def get(self, resource_id: IDType) -> bytes: ...
    async def put(self, resource_id: IDType, data: bytes) -> None: ...
    def list_ids(self) -> AsyncGenerator[IDType]: ...
    async def read_local_json(self, resource_id: IDType) -> bytes: ...
    def webpage_url(self, resource_id: IDType) -> str: ...
