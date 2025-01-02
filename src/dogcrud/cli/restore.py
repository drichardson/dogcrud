# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import logging

import aiofiles
import click

from dogcrud.core.context import config_context
from dogcrud.core.data import resource_type_for_filename

logger = logging.getLogger(__name__)


@click.command()
@click.argument("filename", type=click.Path(exists=True))
def restore(filename: str) -> None:
    """
    Restore a datadog resource from a JSON file in the file system.

    FILENAME is the name of the file to restore.
    """
    config_context().run_in_context(async_restore(filename))


async def async_restore(filename: str) -> None:
    rt = resource_type_for_filename(filename)
    resource_id = rt.resource_id(filename)
    async with aiofiles.open(filename, "rb") as file:
        get_data = await file.read()
    put_data = rt.transform_get_to_put(get_data)
    resource_path = rt.rest_path(resource_id)
    logger.info(f"Restoring {resource_path} from {filename}")
    await rt.put(resource_id, put_data)
    logger.info(f"Restored {resource_path}")
