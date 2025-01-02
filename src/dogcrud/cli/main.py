# SPDX-FileCopyrightText: 2025-present Doug Richardson <git@rekt.email>
# SPDX-License-Identifier: MIT

import logging
import pathlib
import resource

import click

from dogcrud.cli.open import open_in_browser
from dogcrud.cli.restore import restore
from dogcrud.cli.save import save
from dogcrud.core import context
from dogcrud.core.logging import setup_logger


@click.group()
@click.version_option()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(list(logging.getLevelNamesMapping().keys()), case_sensitive=False),
)
@click.option(
    "--dd-api-key",
    type=str,
    envvar="DD_API_KEY",
    show_envvar=True,
    required=True,
    help="Datadog API key.",
)
@click.option(
    "--dd-app-key",
    type=str,
    envvar="DD_APP_KEY",
    show_envvar=True,
    required=True,
    help="Datadog application key.",
)
@click.option(
    "--max-concurrent-requests",
    type=int,
    default=100,
    help="Max concurrent requests to Datadog.",
)
@click.option(
    "--data-dir",
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=pathlib.Path),
    default="saved",
)
@click.option(
    "--min-open-files-limit",
    type=int,
    default=4096,
    help="Try to raise the ulimit if it's below this number. This tool opens lots of concurrent file handles.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    log_level: str,
    dd_api_key: str,
    dd_app_key: str,
    max_concurrent_requests: int,
    data_dir: pathlib.Path,
    min_open_files_limit: int,
):
    """
    Utility for working with Datadog CRUD resources.

    For a full list of CRUD resources, see https://docs.datadoghq.com/api/latest/.

    Note, only a subset of those resources are currently supported by this tool.
    """
    root_logger = logging.getLogger()
    setup_logger(root_logger, log_level)

    # This tool opens a lot of file handles concurrently, so need to up limits.
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(
        resource.RLIMIT_NOFILE,
        (max(soft, min_open_files_limit), max(hard, min_open_files_limit)),
    )

    ctx.with_resource(
        context.set_config_context(
            context.ConfigContext(
                dd_api_key=dd_api_key,
                dd_app_key=dd_app_key,
                max_concurrent_requests=max_concurrent_requests,
                data_dir=data_dir,
            )
        )
    )


cli.add_command(save)
cli.add_command(restore)
cli.add_command(open_in_browser)

cli.main()
