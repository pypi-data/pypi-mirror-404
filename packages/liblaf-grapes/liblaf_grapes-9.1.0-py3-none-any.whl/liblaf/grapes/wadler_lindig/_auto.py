import functools
from collections.abc import Callable
from typing import Any, overload

from liblaf.grapes.fieldz import has_fields

from ._pformat import pformat
from .custom import pdoc_fieldz, pdoc_rich_repr


@overload
def auto_pdoc[T: type](
    cls: T, *, pdoc: bool | None = None, repr: bool | None = None
) -> T: ...
@overload
def auto_pdoc[T: type](
    *, pdoc: bool | None = None, repr: bool | None = None
) -> Callable[[T], T]: ...
def auto_pdoc(
    cls: type | None = None,
    *,
    pdoc: bool | None = None,
    repr: bool | None = None,  # noqa: A002
) -> Any:
    if cls is None:
        return functools.partial(auto_pdoc, pdoc=pdoc, repr=repr)
    if pdoc is None:
        pdoc = not hasattr(cls, "__pdoc__")
    if repr is None:
        repr = cls.__repr__ is object.__repr__  # noqa: A001
    if pdoc:
        if hasattr(cls, "__rich_repr__"):
            cls.__pdoc__ = pdoc_rich_repr
        elif has_fields(cls):
            cls.__pdoc__ = pdoc_fieldz
    if repr:
        cls.__repr__ = pformat  # pyright: ignore[reportAttributeAccessIssue]
    return cls
