# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

from collections.abc import Sequence
from functools import partial

from dogcrud.core.metric_metadata_resource_type import MetricMetadataResourceType
from dogcrud.core.metric_resource_type import MetricResourceType
from dogcrud.core.pagination import (
    IDOffsetPagination,
    ItemOffsetPagination,
    NoPagination,
)
from dogcrud.core.reference_table_resource_type import ReferenceTableResourceType
from dogcrud.core.resource_type import ResourceType
from dogcrud.core.standard_resource_type import StandardResourceType
from dogcrud.core.transformers import data_at_key


def resource_types() -> Sequence[ResourceType]:
    """
    The Datadog Resource type definitions that are used to provide common CLI
    implementations for each type.

    https://docs.datadoghq.com/api/latest/
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
        StandardResourceType(
            rest_base_path="v1/slo",
            webpage_base_path="slo",
            max_concurrency=100,
            pagination_strategy=ItemOffsetPagination(offset_query_param="offset", items_key="data"),
            webpage_suffix="/edit",
            get_to_put_transformer=partial(data_at_key, "data"),
        ),
        StandardResourceType(
            rest_base_path="v2/logs/config/metrics",
            webpage_base_path="logs/pipelines/generate-metrics",
            max_concurrency=100,
            pagination_strategy=NoPagination(items_key="data"),
        ),
        StandardResourceType(
            rest_base_path="v2/workflows",
            webpage_base_path="workflow",
            max_concurrency=100,
            pagination_strategy=NoPagination(items_key="data"),
            disabled=True,
        ),
        ReferenceTableResourceType(
            max_concurrency=100,
        ),
        MetricMetadataResourceType(
            max_concurrency=100,
        ),
        MetricResourceType(
            max_concurrency=100,
        ),
    )
