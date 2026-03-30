#!/usr/bin/env python
# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT
"""
Compare the 'data' object returned by the list endpoint (GET /api/v2/incidents)
vs the individual GET endpoint (GET /api/v2/incidents/{id}) to determine
whether the individual GET provides any additional fields.

Fetches the first page of incidents (up to 10) and compares each one.

Usage:
    doppler run -- uv run python scripts/compare_incident_list_vs_get.py
"""

import asyncio
import os
import sys

import aiohttp
import orjson


async def main() -> None:
    dd_api_key = os.environ["DD_API_KEY"]
    dd_app_key = os.environ["DD_APP_KEY"]

    headers = {
        "DD-API-KEY": dd_api_key,
        "DD-APPLICATION-KEY": dd_app_key,
        "accept": "application/json",
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        # Fetch first page (small page size so we don't hammer the API)
        list_url = "https://api.datadoghq.com/api/v2/incidents"
        async with session.get(list_url, params={"page[size]": "10"}) as resp:
            resp.raise_for_status()
            list_body = orjson.loads(await resp.read())

        incidents_from_list: list[dict] = list_body.get("data", [])
        if not incidents_from_list:
            print("No incidents found.")
            return

        print(f"Comparing {len(incidents_from_list)} incidents...\n")

        all_same = True
        for list_item in incidents_from_list:
            incident_id = list_item["id"]

            # Fetch individual GET
            get_url = f"https://api.datadoghq.com/api/v2/incidents/{incident_id}"
            async with session.get(get_url) as resp:
                resp.raise_for_status()
                get_body = orjson.loads(await resp.read())

            get_item = get_body["data"]

            # Normalise both to sorted-key JSON for a clean diff
            list_json = orjson.dumps(
                list_item, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2
            ).decode()
            get_json = orjson.dumps(
                get_item, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2
            ).decode()

            if list_json == get_json:
                print(f"  {incident_id}: IDENTICAL")
            else:
                all_same = False
                print(f"  {incident_id}: DIFFERENT")

                # Show keys present in get but missing from list (or with different values)
                list_keys = set(_leaf_paths(list_item))
                get_keys = set(_leaf_paths(get_item))

                only_in_get = get_keys - list_keys
                only_in_list = list_keys - get_keys
                in_both_but_different = {
                    k
                    for k in list_keys & get_keys
                    if _get_at_path(list_item, k) != _get_at_path(get_item, k)
                }

                if only_in_get:
                    print(f"    Keys only in GET/{incident_id}:")
                    for k in sorted(only_in_get):
                        print(f"      {k} = {_get_at_path(get_item, k)!r}")
                if only_in_list:
                    print("    Keys only in LIST response:")
                    for k in sorted(only_in_list):
                        print(f"      {k} = {_get_at_path(list_item, k)!r}")
                if in_both_but_different:
                    print("    Keys with different values:")
                    for k in sorted(in_both_but_different):
                        print(f"      {k}:")
                        print(f"        list: {_get_at_path(list_item, k)!r}")
                        print(f"        get:  {_get_at_path(get_item, k)!r}")

        print()
        if all_same:
            print(
                "CONCLUSION: Individual GET returns the same data as the list endpoint."
            )
            print("The individual GET call is redundant for backup purposes.")
        else:
            print(
                "CONCLUSION: Individual GET returns DIFFERENT data from the list endpoint."
            )
            print("The individual GET call provides additional information.")

    sys.exit(0 if all_same else 1)


def _leaf_paths(obj: object, prefix: str = "") -> list[str]:
    """Return dotted key paths to all leaf values in a nested dict/list."""
    paths: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            child = f"{prefix}.{k}" if prefix else k
            paths.extend(_leaf_paths(v, child))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            child = f"{prefix}[{i}]"
            paths.extend(_leaf_paths(v, child))
    else:
        paths.append(prefix)
    return paths


def _get_at_path(obj: object, path: str) -> object:
    """Retrieve a value from a nested dict/list using a dotted path."""
    import re

    parts = re.split(r"\.|\[(\d+)\]", path)
    cur = obj
    i = 0
    while i < len(parts):
        part = parts[i]
        if part == "" or part is None:
            i += 1
            continue
        if part.isdigit():
            cur = cur[int(part)]  # type: ignore[index]
        else:
            cur = cur[part]  # type: ignore[index]
        i += 1
    return cur


if __name__ == "__main__":
    asyncio.run(main())
