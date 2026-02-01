import inspect
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import attrs
import wadler_lindig as wl

from liblaf.grapes.wadler_lindig import pformat

from ._utils import get_name


@attrs.define
class PrettyCall:
    func_name: str
    args: Sequence[Any] = ()
    kwargs: Mapping[str, Any] = {}

    def __repr__(self) -> str:
        return pformat(self)

    def __pdoc__(self, **kwargs) -> wl.AbstractDoc:
        params: list[wl.AbstractDoc] = [wl.pdoc(arg, **kwargs) for arg in self.args]
        params += wl.named_objs(self.kwargs.items(), **kwargs)
        return wl.bracketed(
            begin=wl.TextDoc(self.func_name) + wl.TextDoc("("),
            docs=params,
            sep=wl.comma,
            end=wl.TextDoc(")"),
            indent=kwargs["indent"],
        )


def pretty_call(
    func: Callable,
    args: Sequence[Any] = (),
    kwargs: Mapping[str, Any] = {},
    **wl_kwargs,
) -> str:
    """.

    Examples:
        >>> def foo(a: int, b: int, c: int = 3): ...
        >>> print(pretty_call(foo, (1, 2), {"c": 4}))
        foo(1, 2, 4)
    """
    func = inspect.unwrap(func)
    args, kwargs = _bind_safe(func, args, kwargs)
    return pformat(PrettyCall(get_name(func), args, kwargs), **wl_kwargs)


def _bind_safe(
    func: Callable, /, args: Sequence[Any], kwargs: Mapping[str, Any]
) -> tuple[Sequence[Any], Mapping[str, Any]]:
    try:
        signature: inspect.Signature = inspect.signature(func)
        arguments: inspect.BoundArguments = signature.bind(*args, **kwargs)
    except TypeError:
        return args, kwargs
    else:
        return arguments.args, arguments.kwargs
