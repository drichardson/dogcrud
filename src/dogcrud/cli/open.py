# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import webbrowser

import click

from dogcrud.core.context import config_context
from dogcrud.core.data import resource_type_for_filename


@click.command(name="open")
@click.argument("filename", type=click.Path(exists=True))
def open_in_browser(filename: str) -> None:
    """
    Open Datadog web page corresponding to FILENAME.
    """
    config_context().run_in_context(async_open(filename))


async def async_open(filename: str) -> None:
    rt = resource_type_for_filename(filename)
    resource_id = rt.resource_id(filename)
    webbrowser.open_new_tab(rt.webpage_url(resource_id))
