from __future__ import annotations

import functools
import types
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Unpack, overload

import wadler_lindig as wl

from liblaf.grapes.wadler_lindig._typing import CustomCallable, WadlerLindigOptions

from ._array import pdoc_array
from ._fieldz import pdoc_fieldz
from ._rich_repr import pdoc_rich_repr

if TYPE_CHECKING:
    from functools import _RegType, _SingleDispatchCallable


class PdocCustomDispatcher:
    _dispatcher: _SingleDispatchCallable[wl.AbstractDoc | None]
    _registry: list[CustomCallable]

    def __init__(self) -> None:
        @functools.singledispatch
        def dispatcher(
            obj: Any, **kwargs: Unpack[WadlerLindigOptions]
        ) -> wl.AbstractDoc | None:
            return self._fallback(obj, **kwargs)

        self._dispatcher = dispatcher
        self._registry = []
        self.register(pdoc_array)
        self.register(pdoc_fieldz)
        self.register(pdoc_rich_repr)

    def __call__(
        self, obj: Any, **kwargs: Unpack[WadlerLindigOptions]
    ) -> wl.AbstractDoc | None:
        respect_pdoc: bool = kwargs.get("respect_pdoc", True)
        if respect_pdoc and hasattr(obj, "__pdoc__"):
            return None
        return self._dispatcher(obj, **kwargs)

    @overload
    def register[C: Callable](self, cls: _RegType, /) -> Callable[[C], C]: ...
    @overload
    def register[C: Callable](self, cls: _RegType, /, func: C) -> C: ...
    @overload
    def register[C: Callable](self, func: C, /) -> C: ...
    def register(
        self, cls_or_func: _RegType | Callable, /, func: Callable | None = None
    ) -> Callable:
        if isinstance(cls_or_func, (type, types.UnionType)):
            return self._dispatcher.register(cls_or_func, func)
        self._registry.append(cls_or_func)
        return cls_or_func

    def _fallback(self, obj: Any, **kwargs: Any) -> wl.AbstractDoc | None:
        for func in self._registry:
            doc: wl.AbstractDoc | None = func(obj, **kwargs)
            if doc is not None:
                return doc
        return None


pdoc_custom: PdocCustomDispatcher = PdocCustomDispatcher()
