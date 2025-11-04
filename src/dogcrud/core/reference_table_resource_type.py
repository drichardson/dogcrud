# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import logging
import pathlib
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

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        saved_file = pathlib.Path(f"saved/{self.rest_base_path}/{resource_id}.json")
        data = orjson.loads(saved_file.read_bytes())
        table_name = data["data"]["attributes"]["table_name"]
        return f"https://app.datadoghq.com/{self.webpage_base_path}/{table_name}"
