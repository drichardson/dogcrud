# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import webbrowser

import click

from dogcrud.core.data import (
    ResourceWithId,
    model_validate_json_file,
    resource_type_for_filename,
)


@click.command(name="open")
@click.argument("filename", type=click.Path(exists=True))
def open_in_browser(filename: str) -> None:
    """
    Open Datadog web page corresponding to FILENAME.
    """
    rt = resource_type_for_filename(filename)
    resource = model_validate_json_file(ResourceWithId, filename)
    webbrowser.open_new_tab(rt.webpage_url(resource.id))
