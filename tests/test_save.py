import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import aiohttp.client_exceptions
import pytest

from dogcrud.cli.save import save_resource


def forbidden_resource_type() -> MagicMock:
    rt = MagicMock()
    rt.rest_path.side_effect = lambda resource_id=None: (
        "v1/dashboard" if resource_id is None else f"v1/dashboard/{resource_id}"
    )
    rt.get = AsyncMock(
        side_effect=aiohttp.client_exceptions.ClientResponseError(
            request_info=MagicMock(), history=(), status=403, message="Forbidden"
        )
    )
    return rt


def test_save_resource_skips_forbidden_when_requested(caplog, tmp_path: Path):
    rt = forbidden_resource_type()
    rt.local_path.return_value = tmp_path / "abc-123.json"

    asyncio.run(save_resource(rt, "abc-123", skip_forbidden=True))

    assert not (tmp_path / "abc-123.json").exists()
    assert "Skipping v1/dashboard/abc-123: 403 Forbidden" in caplog.text


def test_save_resource_raises_forbidden_by_default():
    rt = forbidden_resource_type()

    with pytest.raises(aiohttp.client_exceptions.ClientResponseError) as exc_info:
        asyncio.run(save_resource(rt, "abc-123"))

    assert exc_info.value.status == 403
