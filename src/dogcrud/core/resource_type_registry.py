# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

from collections.abc import Sequence

from dogcrud.core.pagination import (
    IDOffsetPagination,
    ItemOffsetPagination,
    NoPagination,
)
from dogcrud.core.resource_type import ResourceType
from dogcrud.core.standard_resource_types import StandardResourceType


def resource_types() -> Sequence[ResourceType]:
    """
    The Datadog Resource type definitions that are used to provide common CLI
    implementations for each type.
    """
    return (
        StandardResourceType(
            rest_base_path="v1/dashboard",
            webpage_base_path="dashboard",
            max_concurrency=20,
            pagination_strategy=ItemOffsetPagination(offset_query_param="start", items_key="dashboards"),
        ),
        StandardResourceType(
            rest_base_path="v1/monitor",
            webpage_base_path="monitors",
            max_concurrency=100,
            pagination_strategy=IDOffsetPagination(offset_query_param="id_offset"),
        ),
        StandardResourceType(
            rest_base_path="v1/logs/config/pipelines",
            webpage_base_path="logs/pipelines/pipeline/edit",
            max_concurrency=100,
            pagination_strategy=NoPagination(),
        ),
    )
