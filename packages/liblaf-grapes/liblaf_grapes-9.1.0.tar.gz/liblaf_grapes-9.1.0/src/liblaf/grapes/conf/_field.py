import contextlib
import contextvars
from collections.abc import Callable, Generator
from typing import cast

import attrs
import environs
import wadler_lindig as wl
from rich.repr import RichReprResult

from liblaf.grapes.sentinel import MISSING, MissingType


@attrs.frozen
class Field[T]:
    """.

    Examples:
        >>> from environs import env
        >>> a: Field[int] = Field("a", default=0, getter=env.int)
        >>> a
        Field(name='a', value=0)
        >>> a.name
        'a'
        >>> a.get()
        0
        >>> with a.overrides(1):
        ...     a.get()
        1
        >>> a.get()
        0

        >>> # using default factory
        >>> a: Field[int] = Field("a", factory=lambda: 0, getter=env.int)
        >>> a.get()
        0
    """

    _var: contextvars.ContextVar[T] = attrs.field(repr=False, alias="var")

    def __init__(
        self,
        name: str,
        *,
        default: T | MissingType = MISSING,
        env: str | None = None,
        factory: Callable[[], T] | None = None,
        getter: Callable[[str], T],
    ) -> None:
        value: T | MissingType = _get_value(
            name, default=default, env=env, factory=factory, getter=getter
        )
        var: contextvars.ContextVar[T]
        if value is MISSING:
            var = contextvars.ContextVar(name)
        else:
            value = cast("T", value)
            var = contextvars.ContextVar(name, default=value)
        self.__attrs_init__(var=var)  # pyright: ignore[reportAttributeAccessIssue]

    def __repr__(self) -> str:
        from liblaf.grapes.wadler_lindig import pformat

        return pformat(self)

    def __pdoc__(self, **kwargs) -> wl.AbstractDoc | None:
        from liblaf.grapes.wadler_lindig import pdoc_rich_repr

        return pdoc_rich_repr(self, **kwargs)

    def __rich_repr__(self) -> RichReprResult:
        yield "name", self.name
        yield "value", self.get()

    @property
    def name(self) -> str:
        return self._var.name

    def get(self) -> T:
        return self._var.get()

    def set(self, value: T, /) -> None:
        self._var.set(value)

    @contextlib.contextmanager
    def overrides(self, value: T, /) -> Generator[T]:
        token: contextvars.Token[T] = self._var.set(value)
        try:
            yield value
        finally:
            self._var.reset(token)


def _get_value[T](
    name: str,
    *,
    default: T | MissingType = MISSING,
    env: str | None = None,
    factory: Callable[[], T] | None = None,
    getter: Callable[[str], T],
) -> T | MissingType:
    if env is None:
        env = name.upper().replace(".", "_")
    try:
        return getter(env)
    except environs.EnvError:
        pass
    if default is not MISSING:
        return default
    if factory is not None:
        return factory()
    return MISSING
