# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import os

import aiofiles
import orjson

from dogcrud.core.resource_type import ResourceType
from dogcrud.core.resource_type_registry import resource_types


def format_json(json: bytes) -> bytes:
    """
    Pretty print JSON with sorted keys so that JSON files are easier to diff.
    """
    parsed_json = orjson.loads(json)
    return orjson.dumps(parsed_json, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS | orjson.OPT_APPEND_NEWLINE)


async def write_formatted_json(json: bytes, filename: str) -> None:
    """
    Write JSON to a file, formatted with keys sorted to make diffing files
    easier.
    """
    formatted_json = await asyncio.to_thread(format_json, json)

    async with aiofiles.open(filename, "wb") as out:
        await out.write(formatted_json)


def resource_type_for_filename(filename: str) -> ResourceType:
    filename = os.path.abspath(filename)

    for rt in resource_types():
        if str(rt.local_path()) in filename:
            return rt

    msg = f"No resource type found for {filename}"
    raise RuntimeError(msg)
