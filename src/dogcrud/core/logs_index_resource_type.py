# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import override

import aiohttp.client_exceptions
import orjson

from dogcrud.core import rest
from dogcrud.core.pagination import NoPagination
from dogcrud.core.resource_type import IDType
from dogcrud.core.standard_resource_type import StandardResourceType


def _strip_read_only_fields(data: bytes) -> bytes:
    """
    Strip read-only fields from the GET response before sending to PUT.

    The `is_rate_limited` and `name` fields are returned by GET but are
    not accepted by PUT.
    """
    parsed = orjson.loads(data)
    parsed.pop("is_rate_limited", None)
    parsed.pop("name", None)
    return orjson.dumps(parsed)


class LogsIndexResourceType(StandardResourceType):
    """
    Resource type for Datadog Log Indexes.

    Log indexes use `name` (a string) as their identifier rather than the
    conventional `id` field, so list_ids() is overridden to extract `name`
    from each item in the list response.

    https://docs.datadoghq.com/api/latest/logs-indexes/
    """

    def __init__(self, max_concurrency: int) -> None:
        super().__init__(
            rest_base_path="v1/logs/config/indexes",
            webpage_base_path="logs/indexes",
            max_concurrency=max_concurrency,
            pagination_strategy=NoPagination(items_key="indexes"),
            get_to_put_transformer=_strip_read_only_fields,
        )

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        async with self.concurrency_semaphore:
            data = await rest.get_json(f"api/{self.rest_path()}")
        parsed = orjson.loads(data)
        for index in parsed["indexes"]:
            yield index["name"]

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        try:
            await super().put(resource_id, data)
        except aiohttp.client_exceptions.ClientResponseError as e:
            if e.status == 409:  # noqa: PLR2004
                msg = (
                    f"Cannot restore log index '{resource_id}': Datadog does not allow "
                    f"reusing a deleted index name. You must create a new index with a "
                    f"different name via the Datadog UI."
                )
                raise RuntimeError(msg) from e
            raise

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        return "https://app.datadoghq.com/logs/indexes"

    @override
    def resource_id(self, filename: str) -> IDType:
        return Path(filename).stem
