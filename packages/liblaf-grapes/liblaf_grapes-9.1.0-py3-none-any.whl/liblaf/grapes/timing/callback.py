import functools
from collections.abc import Iterable
from typing import Any, overload

import limits

from ._statistics import StatisticName
from ._timings import Callback, Timings


@overload
def log_record(
    timer: Timings,
    /,
    *,
    index: int = ...,
    level: int | str = ...,
    limits: str | limits.RateLimitItem | None = ...,
) -> Any: ...
@overload
def log_record(
    *,
    index: int = ...,
    level: int | str = ...,
    limits: str | limits.RateLimitItem | None = ...,
) -> Callback: ...
def log_record(timer: Timings | None = None, /, **kwargs) -> Any:
    _logging_hide = True
    if timer is None:
        return functools.partial(log_record, **kwargs)
    return timer.log_record(**kwargs)


@overload
def log_summary(
    timer: Timings,
    /,
    *,
    level: int | str = ...,
    stats: Iterable[StatisticName] = ...,
    limits: str | limits.RateLimitItem | None = ...,
) -> None: ...
@overload
def log_summary(
    *,
    level: int | str = ...,
    stats: Iterable[StatisticName] = ...,
    limits: str | limits.RateLimitItem | None = ...,
) -> Callback: ...
def log_summary(timer: Timings | None = None, /, **kwargs) -> Any:
    _logging_hide = True
    if timer is None:
        return functools.partial(log_summary, **kwargs)
    return timer.log_summary(**kwargs)
