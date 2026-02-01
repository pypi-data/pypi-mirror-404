import functools
from collections.abc import Callable


class LazyRepr[**P]:
    func: Callable[P, str]
    # Pyright doesn't support this annotation
    # args: P.args

    def __init__(
        self, func: Callable[P, str], /, *args: P.args, **kwargs: P.kwargs
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __repr__(self) -> str:
        return self.value

    @functools.cached_property
    def value(self) -> str:
        return self.func(*self.args, **self.kwargs)


class LazyStr[**P]:
    func: Callable[P, str]

    def __init__(
        self, func: Callable[P, str], /, *args: P.args, **kwargs: P.kwargs
    ) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __str__(self) -> str:
        return self.value

    @functools.cached_property
    def value(self) -> str:
        return self.func(*self.args, **self.kwargs)
