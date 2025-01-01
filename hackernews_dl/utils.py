from typing import Any


def remove_keys(d: dict, remove_keys: list[Any]):
    for key in remove_keys:
        d.pop(key, None)
    return d
