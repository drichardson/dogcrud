import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp.client_exceptions
import pytest

from dogcrud.cli.save import save_resource


def forbidden_resource_type() -> MagicMock:
    resource_type = MagicMock()
    resource_type.rest_path.return_value = "v1/dashboard/abc-123"
    resource_type.get = AsyncMock(
        side_effect=aiohttp.client_exceptions.ClientResponseError(
            request_info=MagicMock(), history=(), status=403, message="Forbidden"
        )
    )
    return resource_type


def test_skips_forbidden():
    resource_type = forbidden_resource_type()
    asyncio.run(save_resource(resource_type, "abc-123", skip_forbidden=True))
    resource_type.local_path.assert_not_called()


def test_raises_forbidden_by_default():
    with pytest.raises(aiohttp.client_exceptions.ClientResponseError):
        asyncio.run(save_resource(forbidden_resource_type(), "abc-123"))
