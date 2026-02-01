import functools
from collections.abc import Callable
from typing import Any, overload

from liblaf.grapes.fieldz import has_fields

from ._fieldz import rich_repr_fieldz


@overload
def auto_rich_repr[T: type](cls: T, *, rich_repr: bool | None = None) -> T: ...
@overload
def auto_rich_repr[T: type](*, rich_repr: bool | None = None) -> Callable[[T], T]: ...
def auto_rich_repr(cls: type | None = None, *, rich_repr: bool | None = None) -> Any:
    if cls is None:
        return functools.partial(auto_rich_repr, rich_repr=rich_repr)
    if rich_repr is None:
        rich_repr = not hasattr(cls, "__rich_repr__")
    if rich_repr and has_fields(cls):
        cls.__rich_repr__ = rich_repr_fieldz
    return cls
