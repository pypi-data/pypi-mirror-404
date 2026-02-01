import datetime
import functools
from collections.abc import Callable, Iterable, Mapping
from typing import Any, Literal, Protocol, TypedDict, overload

import joblib
import tlz
import wrapt

from liblaf.grapes._config import config

from ._wrapt import wrapt_setattr


class MemorizedFunc[**P, T](Protocol):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T: ...
    @property
    def func(self) -> Callable[P, T]: ...


class Metadata(TypedDict): ...


@overload
def memorize[**P, T](
    func: Callable[P, T],
    /,
    *,
    memory: joblib.Memory | None = ...,
    # memory.cache() params
    ignore: list[str] | None = ...,
    verbose: int | None = ...,
    mmap_mode: Literal["r+", "r", "w+", "c"] | None = ...,
    cache_validation_callback: Callable[[Metadata], bool] | None = ...,
    # memory.reduce_size() params
    bytes_limit: int | str | None = ...,
    items_limit: int | None = ...,
    age_limit: datetime.timedelta | None = ...,
) -> MemorizedFunc[P, T]: ...
@overload
def memorize[**P, T](
    *,
    memory: joblib.Memory | None = None,
    # memory.cache() params
    ignore: list[str] | None = ...,
    verbose: int | None = ...,
    mmap_mode: Literal["r+", "r", "w+", "c"] | None = ...,
    cache_validation_callback: Callable[[Metadata], bool] | None = ...,
    # memory.reduce_size() params
    bytes_limit: int | str | None = ...,
    items_limit: int | None = ...,
    age_limit: datetime.timedelta | None = ...,
) -> Callable[[Callable[P, T]], MemorizedFunc[P, T]]: ...
def memorize(func: Callable | None = None, /, **kwargs: Any) -> Any:
    if func is None:
        return functools.partial(memorize, **kwargs)
    memory: joblib.Memory | None = kwargs.pop("memory", None)
    if memory is None:
        memory = make_memory()
    cache_kwargs: dict[str, Any] = pick(
        {"ignore", "verbose", "mmap_mode", "cache_validation_callback"}, kwargs
    )
    reduce_size_kwargs: dict[str, Any] = pick(
        {"bytes_limit", "items_limit", "age_limit"}, kwargs
    )
    reduce_size_kwargs.setdefault("bytes_limit", config.joblib.memory.bytes_limit.get())

    @wrapt.decorator
    def wrapper[**P, T](
        wrapped: Callable[P, T],
        _instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> T:
        result: Any = wrapped(*args, **kwargs)
        memory.reduce_size(**reduce_size_kwargs)
        return result

    func = memory.cache(func, **cache_kwargs)
    func = wrapper(func)
    wrapt_setattr(func, "memory", memory)
    return func


@functools.cache
def make_memory() -> joblib.Memory:
    return joblib.Memory(location=config.joblib.memory.location.get())


def pick[KT, VT](allowlist: Iterable[KT], dictionary: Mapping[KT, VT]) -> dict[KT, VT]:
    return tlz.keyfilter(lambda k: k in allowlist, dictionary)
