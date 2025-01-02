# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import logging

import aiofiles
import click

from dogcrud.core.context import config_context
from dogcrud.core.data import (
    ResourceWithId,
    model_validate_json_file,
    resource_type_for_filename,
)

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
    resource = model_validate_json_file(ResourceWithId, filename)
    async with aiofiles.open(filename, "rb") as file:
        data = file.read()
    resource_path = rt.rest_path(resource.id)
    logger.info(f"Restoring {resource_path} from {filename}")
    await rt.put(resource.id, data)
    logger.info(f"Restored {resource_path}")
