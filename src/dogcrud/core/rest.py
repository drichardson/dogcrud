# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import asyncio
import logging
import time

from dogcrud.core.context import async_run_context

logger = logging.getLogger(__name__)


async def get_json(path: str) -> bytes:
    """
    Get a Datadog JSON resource. This function is used instead of
    https://datadog-api-client.readthedocs.io/ when we need to download a lot
    of objects and the datadog-api-client API is too slow (the slowness seems
    to be related to the OpenApi parsing on each response). For many cases
    (like backups) we just want to download the RAW json, so no parsing is
    necessary.

    path is the part of the Datadog API URL after https://api.datadoghq.com/.
    For example, to make a request to get all dashboards using
    https://api.datadoghq.com/api/v1/dashboard you'd pass in
    path="v1/dashboard".

    If the request is rate limited with an HTTP 429, this function will sleep
    for X-RateLimit-Reset (a datadog response header) seconds before trying
    again.

    Documentation for Datadog APIs can be found at
    https://docs.datadoghq.com/api/latest/.
    """
    url = path if path.startswith("https://") else f"https://api.datadoghq.com/{path}"
    headers = {"accept": "application/json"}
    ratelimit_reset = 0.0

    retry = 0
    while True:
        async with async_run_context().concurrent_requests_semaphore:
            t0 = time.perf_counter()
            async with async_run_context().datadog_session.get(url, headers=headers) as resp:
                duration = time.perf_counter() - t0
                logger.debug(f"get_json: url={url}, status={resp.status}, duration={duration:.3f}s, retry={retry}")
                match resp.status:
                    case 200:
                        return await resp.read()
                    case 429:
                        # https://docs.datadoghq.com/api/latest/rate-limits/
                        ratelimit_reset = float(resp.headers["X-RateLimit-Reset"])
                    case _:
                        resp.raise_for_status()
                        # above will raise for most HTTP error, but if we get
                        # an unexpected HTTP success code, we will raise
                        # RuntimeError.
                        msg = "Unexpected status code {resp.status} for {url}"
                        raise RuntimeError(msg)

        logger.info(f"Sleeping until rate limit reset in {ratelimit_reset} seconds for {url}")
        await asyncio.sleep(float(ratelimit_reset))
        retry += 1


async def put_json(path: str, body: bytes) -> None:
    url = f"https://api.datadoghq.com/{path}"
    headers = {"content-type": "application/json"}

    async with async_run_context().concurrent_requests_semaphore:
        t0 = time.perf_counter()
        async with async_run_context().datadog_session.put(url, data=body, headers=headers) as resp:
            duration = time.perf_counter() - t0
            logger.debug(f"put_json: url={url}, body={len(body)} bytes, status={resp.status}, duration={duration:.3f}s")
            resp.raise_for_status()
