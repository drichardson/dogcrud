from collections.abc import Callable

import orjson

type GetToPut = Callable[[bytes], bytes]


def identity(data: bytes) -> bytes:
    """
    Use identity transformer when GET data is same as PUT data.
    """
    return data


def data_at_key(key: str, data: bytes) -> bytes:
    """
    Use data_at_key trasnformer when GET data is a dictionary that contains the PUT data at a key.
    """
    json = orjson.loads(data)
    inner_data = json[key]
    return orjson.dumps(inner_data)
