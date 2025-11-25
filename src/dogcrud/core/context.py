# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import contextlib
import contextvars
import pathlib
from collections.abc import Coroutine, Generator
from dataclasses import dataclass

import aiohttp


class ContextAlreadySetError(Exception):
    def __init__(self, context_var_name: str):
        super().__init__(f"Context {context_var_name} already set.")


@dataclass(frozen=True)
class ConfigContext:
    """
    ConfigContext is set from the top level to setup common context variables
    in the async context. It is used to pass global options to sub-commands
    (like save and restore).

    Since the majority of the sub-command features use asyncio, but click is not
    asyncio compatible, ConfigContext is also used to startup the async sub-commands
    with an async context setup correctly.
    """

    dd_api_key: str
    dd_app_key: str
    max_concurrent_requests: int
    data_dir: pathlib.Path
    skip_unsupported_workflows: bool = False
    include_disabled: bool = False

    def run_in_context(self, main: Coroutine) -> None:
        asyncio.run(self.in_context(main))

    async def in_context(self, main: Coroutine) -> None:
        """
        Run coro with an AsyncRunContext configured.

        Access the context using async_run_context().
        """
        headers = {
            "DD-API-KEY": self.dd_api_key,
            "DD-APPLICATION-KEY": self.dd_app_key,
        }

        async with aiohttp.ClientSession(headers=headers) as datadog_session:
            token = async_run_context_var.set(
                AsyncRunContext(
                    datadog_session=datadog_session,
                    concurrent_requests_semaphore=asyncio.BoundedSemaphore(self.max_concurrent_requests),
                )
            )
            try:
                if token.old_value != contextvars.Token.MISSING:
                    raise ContextAlreadySetError(async_run_context_var.name)
                await main
            finally:
                async_run_context_var.reset(token)


config_context_var = contextvars.ContextVar[ConfigContext]("config_context")


def config_context() -> ConfigContext:
    return config_context_var.get()


@contextlib.contextmanager
def set_config_context(config_context: ConfigContext) -> Generator[None]:
    """
    Used by the top level click command to install the ConfigContext.
    """
    token = config_context_var.set(config_context)
    try:
        if token.old_value != contextvars.Token.MISSING:
            raise ContextAlreadySetError(config_context_var.name)
        yield
    finally:
        config_context_var.reset(token)


@dataclass
class AsyncRunContext:
    """
    AsyncRunContext is availble inside ConfigContext.run_in_context().


    Asyncio click sub-commands get this using async_run_context().
    """

    datadog_session: aiohttp.ClientSession
    concurrent_requests_semaphore: asyncio.BoundedSemaphore


async_run_context_var = contextvars.ContextVar[AsyncRunContext]("async_run_context")


def async_run_context() -> AsyncRunContext:
    return async_run_context_var.get()
