# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from typing import override

import orjson

from dogcrud.core.pagination import LimitOffsetPagination
from dogcrud.core.resource_type import IDType
from dogcrud.core.standard_resource_type import StandardResourceType

logger = logging.getLogger(__name__)


class ReferenceTableResourceType(StandardResourceType):
    """
    A Datadog reference table resource. This overrides webpage_url to use the table_name
    from the resource attributes instead of the UUID ID.
    """

    def __init__(
        self,
        max_concurrency: int,
    ) -> None:
        super().__init__(
            rest_base_path="v2/reference-tables/tables",
            webpage_base_path="reference-tables",
            max_concurrency=max_concurrency,
            pagination_strategy=LimitOffsetPagination(
                limit=100,
                limit_query_param="page[limit]",
                offset_query_param="page[offset]",
                items_key="data",
            ),
        )
        self._id_to_table_name: dict[IDType, str] = {}

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        # Try to get table_name from cache
        table_name = self._id_to_table_name.get(resource_id)

        if table_name is None:
            # If not in cache, try to read from saved file
            import pathlib
            saved_file = pathlib.Path(f"saved/{self.rest_base_path}/{resource_id}.json")
            if saved_file.exists():
                try:
                    data = orjson.loads(saved_file.read_bytes())
                    table_name = data.get("data", {}).get("attributes", {}).get("table_name")
                    if table_name:
                        self._id_to_table_name[resource_id] = table_name
                except Exception as e:
                    logger.warning(f"Failed to read table_name from {saved_file}: {e}")

        # If we still don't have table_name, fall back to using the ID
        if table_name is None:
            logger.warning(f"Could not find table_name for reference table {resource_id}, using ID in URL")
            table_name = resource_id

        return f"https://app.datadoghq.com/{self.webpage_base_path}/{table_name}"
