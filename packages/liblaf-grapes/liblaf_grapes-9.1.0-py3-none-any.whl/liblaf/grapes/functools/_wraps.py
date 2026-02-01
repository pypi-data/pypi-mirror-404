import functools
from collections.abc import Callable, Iterable
from typing import Any, overload


@overload
def wraps[C: Callable](  # pyright: ignore[reportInconsistentOverload]
    wrapped: C,
    assigned: Iterable[str] = functools.WRAPPER_ASSIGNMENTS,
    updated: Iterable[str] = functools.WRAPPER_UPDATES,
) -> Callable[[Any], C]: ...
def wraps[C: Callable](wrapped: C, *args, **kwargs) -> Callable[[Any], C]:
    return functools.wraps(wrapped, *args, **kwargs)  # pyright: ignore[reportReturnType]
