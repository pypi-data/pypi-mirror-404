from collections.abc import Callable, Iterable, Sequence
from typing import Any, overload

from ._clock import ClockName
from ._timer import Timer
from ._timings import Callback


@overload
def timer(
    *,
    label: str | None = ...,
    clocks: Sequence[ClockName] = ...,
    cb_finish: Callback | None = ...,
    cb_start: Callback | None = ...,
    cb_stop: Callback | None = ...,
) -> Timer: ...
@overload
def timer[C: Callable](
    callable: C,
    /,
    *,
    label: str | None = ...,
    clocks: Sequence[ClockName] = ...,
    cb_start: Callback | None = ...,
    cb_stop: Callback | None = ...,
    cb_finish: Callback | None = ...,
) -> C: ...
@overload
def timer[I: Iterable](
    iterable: I,
    /,
    *,
    label: str | None = ...,
    clocks: Sequence[ClockName] = ...,
    cb_start: Callback | None = ...,
    cb_stop: Callback | None = ...,
    cb_finish: Callback | None = ...,
) -> I: ...
def timer(func_or_iterable: Callable | Iterable | None = None, /, **kwargs) -> Any:
    timer = Timer(**kwargs)
    if func_or_iterable is None:
        return timer
    return timer(func_or_iterable)
