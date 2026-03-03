# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import override
from urllib.parse import quote

import aiofiles
import orjson

from dogcrud.core import context, rest
from dogcrud.core.resource_type import IDType, ResourceType

logger = logging.getLogger(__name__)

_REST_BASE = "v1/integration/slack/configuration/accounts"


class SlackChannelResourceType(ResourceType):
    """
    Datadog Slack integration channels.

    Channels are nested under Slack account (workspace) names, so the resource
    ID is "{account_name}/{channel_name}" (e.g. "my-workspace/#alerts").

    https://docs.datadoghq.com/api/latest/slack-integration/
    """

    def __init__(self, max_concurrency: int, *, disabled: bool = False) -> None:
        self.concurrency_semaphore = asyncio.BoundedSemaphore(max_concurrency)
        self.disabled = disabled

    @override
    def rest_path(self, resource_id: IDType | None = None) -> str:
        match resource_id:
            case None:
                return _REST_BASE
            case _:
                account, _, channel = str(resource_id).partition("/")
                return f"{_REST_BASE}/{account}/channels/{quote(channel, safe='')}"

    @override
    def local_path(self, resource_id: IDType | None = None) -> Path:
        data_dir = context.config_context().data_dir
        match resource_id:
            case None:
                return data_dir / _REST_BASE
            case _:
                account, _, channel = str(resource_id).partition("/")
                return data_dir / _REST_BASE / account / f"{channel}.json"

    @override
    async def get(self, resource_id: IDType) -> bytes:
        async with self.concurrency_semaphore:
            return await rest.get_json(f"api/{self.rest_path(resource_id)}")

    @override
    async def put(self, resource_id: IDType, data: bytes) -> None:
        async with self.concurrency_semaphore:
            await rest.patch_json(f"api/{self.rest_path(resource_id)}", data)

    @override
    def transform_get_to_put(self, data: bytes) -> bytes:
        return data

    @override
    async def list_ids(self) -> AsyncGenerator[IDType]:
        # GET /api/v1/integration/slack returns the full config with all accounts
        # and channels: {"channels": [{"account": "...", "channel_name": "..."}, ...]}
        async with self.concurrency_semaphore:
            integration_json = await rest.get_json("api/v1/integration/slack")
        integration: dict = orjson.loads(integration_json)
        for channel in integration.get("channels", []):
            yield f"{channel['account']}/{channel['channel_name']}"

    @override
    async def read_local_json(self, resource_id: IDType) -> bytes:
        async with aiofiles.open(str(self.local_path(resource_id)), "rb") as file:
            return await file.read()

    @override
    def webpage_url(self, resource_id: IDType) -> str:
        return "https://app.datadoghq.com/account/settings#integrations/slack"

    @override
    def resource_id(self, filename: str) -> IDType:
        path = Path(filename)
        # path: .../v1/integration/slack/configuration/accounts/{account}/{channel}.json
        channel_name = path.stem
        account_name = path.parent.name
        return f"{account_name}/{channel_name}"
