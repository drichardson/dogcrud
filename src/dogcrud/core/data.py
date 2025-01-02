# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import os

import aiofiles
from pydantic import BaseModel

from dogcrud.core.resource_type import ResourceType
from dogcrud.core.resource_type_registry import resource_types


class ResourceWithId(BaseModel):
    id: str | int


def model_validate_json_file[T: BaseModel](cls: type[T], filename: str) -> T:
    """
    Load a Pydantic BaseModel sub-class from a JSON filename.

    Raises an exception on failure.
    """
    with open(filename) as file:
        return cls.model_validate_json(file.read())


async def write_formatted_json(json: bytes, filename: str) -> None:
    """
    Write JSON to a file, formatted with keys sorted to make diffing files
    easier.
    """
    async with aiofiles.open(filename, "w") as out:
        process = await asyncio.create_subprocess_exec(
            "jq",
            "--sort-keys",
            ".",
            stdin=asyncio.subprocess.PIPE,
            stdout=out,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate(json)
    if process.returncode != 0:
        msg = f"jq failed with {process.returncode} for {filename}. Error: {stderr.decode()}"
        raise RuntimeError(msg)


def resource_type_for_filename(filename: str) -> ResourceType:
    filename = os.path.abspath(filename)

    for rt in resource_types():
        if str(rt.local_path()) in filename:
            return rt

    msg = f"No resource type found for {filename}"
    raise RuntimeError(msg)