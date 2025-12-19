# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging

import click
import orjson

from dogcrud.core.context import config_context
from dogcrud.core.metric_metadata_resource_type import MetricMetadataResourceType
from dogcrud.core.metric_resource_type import MetricResourceType
from dogcrud.core.resource_type import ResourceType
from dogcrud.core.resource_type_registry import resource_types
from dogcrud.core.standard_resource_type import StandardResourceType

logger = logging.getLogger(__name__)


@click.group(name="list")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json"], case_sensitive=False),
    default="table",
    help="Output format.",
)
@click.pass_context
def list_resources(ctx: click.Context, output: str) -> None:
    """
    List datadog resources without saving them.
    """
    ctx.ensure_object(dict)
    ctx.obj["output_format"] = output


def create_list_command(rt: ResourceType):
    @list_resources.command(
        name=rt.rest_path(),
        help=f"""
    List {rt.rest_path()} resources.
    """,
    )
    @click.pass_context
    def list_resource_command(ctx: click.Context):
        output_format = ctx.obj["output_format"]
        coro = list_all_resources_of_type(rt, output_format)
        config_context().run_in_context(coro)


for rt in resource_types():
    create_list_command(rt)


@list_resources.command(
    name="all",
    help=f"""
List all datadog resources supported by this tool.

Includes: {", ".join(rt.rest_path() for rt in resource_types())}

Note: Disabled resource types are excluded by default. Use --include-disabled to include them.
""",
)
@click.pass_context
def list_all(ctx: click.Context) -> None:
    """
    List all datadog resources.
    """
    output_format = ctx.obj["output_format"]
    config_context().run_in_context(list_all_resource_types(output_format))


async def list_all_resource_types(output_format: str):
    include_disabled = config_context().include_disabled
    async with asyncio.TaskGroup() as tg:
        for resource_type in resource_types():
            if resource_type.disabled and not include_disabled:
                continue
            tg.create_task(list_all_resources_of_type(resource_type, output_format))


async def list_all_resources_of_type(resource_type: ResourceType, output_format: str) -> None:
    prefix = f"list all {resource_type.rest_path()}"
    logger.debug(f"{prefix}: Starting")

    items = []

    # Match specific resource types - order matters!
    match resource_type:
        case MetricMetadataResourceType() | MetricResourceType():
            # Metric types override list_ids and don't support standard pagination
            items = [{"id": resource_id} async for resource_id in resource_type.list_ids()]
        case StandardResourceType():
            # StandardResourceType has pagination_strategy which provides richer item details
            async for page in resource_type.pagination_strategy.pages(
                f"api/{resource_type.rest_path()}", resource_type.concurrency_semaphore
            ):
                items.extend(page.items)
        case _:
            # Fallback for any other resource types
            items = [{"id": resource_id} async for resource_id in resource_type.list_ids()]

    match output_format:
        case "json":
            output_json(resource_type, items)
        case _:
            output_table(resource_type, items)

    logger.debug(f"{prefix}: Listed {len(items)} items.")


def output_json(resource_type: ResourceType, items: list) -> None:
    """Output items as JSON."""
    output = {
        "resource_type": resource_type.rest_path(),
        "items": items,
        "count": len(items),
    }
    click.echo(orjson.dumps(output, option=orjson.OPT_INDENT_2).decode())


def output_table(resource_type: ResourceType, items: list) -> None:
    """Output items as a simple text list."""
    click.echo(f"{resource_type.rest_path()} ({len(items)} resources)")
    for item in items:
        item_id = item.get("id", "N/A")
        # Try to find a human-readable name/title field
        name = (
            item.get("name")
            or item.get("title")
            or item.get("attributes", {}).get("name")
            or item.get("attributes", {}).get("table_name")
        )

        if name:
            click.echo(f"{item_id} {name}")
        else:
            click.echo(f"{item_id}")
