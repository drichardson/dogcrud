# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging

import aiohttp.client_exceptions
import click
import orjson

from dogcrud.core import data
from dogcrud.core.context import config_context
from dogcrud.core.resource_type import ResourceType
from dogcrud.core.resource_type_registry import resource_types
from dogcrud.core.rest import DatadogAPIBadRequestError

logger = logging.getLogger(__name__)


@click.group()
def save() -> None:
    """
    Save a datadog resources to the local file system.
    """


def create_save_command(rt: ResourceType):
    @save.command(
        name=rt.rest_path(),
        help=f"""
    Save {rt.rest_path()} resources.

    If RESOURCE_ID is all, save all {rt.rest_path()}
    resources; otherwise, save a single {rt.rest_path()} resource.
    """,
    )
    @click.argument("resource_id", type=str)
    def save_resource_command(resource_id: str):
        match resource_id:
            case _ if resource_id.lower() == "all":
                coro = save_all_resources_of_type(rt)
            case _:
                coro = save_resource(rt, resource_id)
        config_context().run_in_context(coro)


for rt in resource_types():
    create_save_command(rt)


@save.command(
    name="all",
    help=f"""
Save all datadog resources supported by this tool.

Includes: {", ".join(rt.rest_path() for rt in resource_types())}

Note: Disabled resource types are excluded by default. Use --include-disabled to include them.
""",
)
def save_all() -> None:
    """
    Save all datadog resources.
    """
    config_context().run_in_context(save_all_resources())


async def save_all_resources():
    include_disabled = config_context().include_disabled
    async with asyncio.TaskGroup() as tg:
        for resource_type in resource_types():
            if resource_type.disabled and not include_disabled:
                continue
            tg.create_task(save_all_resources_of_type(resource_type))


async def save_all_resources_of_type(resource_type: ResourceType) -> None:
    prefix = f"save all {resource_type.rest_path()}"
    logger.info(f"{prefix}: Starting")

    num_saved = 0

    async with asyncio.TaskGroup() as tg:
        async for resource_id in resource_type.list_ids():
            tg.create_task(save_resource(resource_type, str(resource_id)))
            num_saved += 1

    logger.info(f"{prefix} Saved {num_saved} items.")


async def save_resource(resource_type: ResourceType, resource_id: str) -> None:
    try:
        json = await resource_type.get(resource_id)
        resource_type.local_path().mkdir(exist_ok=True, parents=True)
        filename = resource_type.local_path(resource_id)
        await data.write_formatted_json(json, str(filename))
        logger.info(f"Saved {filename}")
    except DatadogAPIBadRequestError as e:
        # Some workflow features aren't supported by Datadog's public API
        skip_unsupported = config_context().skip_unsupported_workflows
        if skip_unsupported and resource_type.rest_path() == "v2/workflows":
            error_data = orjson.loads(e.error_body)
            error_detail = error_data.get("errors", [{}])[0].get("detail", "Unknown error")
            logger.warning(f"Skipping {resource_type.rest_path()}/{resource_id}: {error_detail}")
        else:
            raise
    except aiohttp.client_exceptions.ClientResponseError:
        # Re-raise other HTTP errors
        raise
