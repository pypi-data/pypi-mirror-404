from collections.abc import Callable
from typing import Any

import wadler_lindig as wl


def chain_custom(
    *custom: Callable[..., wl.AbstractDoc | None] | None,
) -> Callable[[Any], wl.AbstractDoc | None]:
    custom = tuple(func for func in custom if func is not None)

    def wrapper(*args, **kwargs) -> wl.AbstractDoc | None:
        for func in custom:
            doc: wl.AbstractDoc | None = func(*args, **kwargs)
            if doc is not None:
                return doc
        return None

    return wrapper
