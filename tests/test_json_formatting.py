import orjson

from dogcrud.core import data


def test_ends_in_newline():
    assert data.format_json(b'{"one": 123}')[-1] == ord("\n")


def test_keys_sorted():
    json = data.format_json(b'{"b": 1, "z": 1, "a": { "subb": 2, "subz": 3, "suba": 4}}')
    parsed_json = orjson.loads(json)

    # Performing list(d) on a dictionary returns a list of all the keys used in the dictionary, in insertion order
    # https://docs.python.org/3/tutorial/datastructures.html#dictionaries
    assert list(parsed_json) == ["a", "b", "z"]

    assert list(parsed_json["a"]) == ["suba", "subb", "subz"]
