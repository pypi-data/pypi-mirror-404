from __future__ import annotations

import linecache
import types
from typing import TYPE_CHECKING, Any, Self, override

import executing

if TYPE_CHECKING:
    from _typeshed import StrPath


class Source(executing.Source):
    if TYPE_CHECKING:

        @override
        @classmethod
        def for_frame(cls, frame: types.FrameType, use_cache: bool = True) -> Self: ...

    @override
    @classmethod
    def for_filename(
        cls,
        filename: StrPath,
        module_globals: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Self:
        # Intentionally skip linecache.checkcache() to preserve consistent source code.
        # This ensures icecream displays correct source lines and variable names, since
        # we don't support hot reloading and need stable source references.
        filename = str(filename)
        return cls._for_filename_and_lines(
            filename, tuple(linecache.getlines(filename, module_globals))
        )  # pyright: ignore[reportReturnType]
