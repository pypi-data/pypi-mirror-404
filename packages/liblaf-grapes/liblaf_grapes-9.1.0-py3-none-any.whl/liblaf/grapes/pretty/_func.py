from collections.abc import Callable

from ._utils import get_name


def pretty_func(func: Callable, /) -> str:
    name: str = get_name(func)
    return f"{name}()"
