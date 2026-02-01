from collections.abc import Callable
from typing import Any, TypedDict

import wadler_lindig as wl

type CustomCallable = Callable[[Any], wl.AbstractDoc | None]


class WadlerLindigOptions(TypedDict, total=False):
    custom: CustomCallable
    hide_defaults: bool
    indent: int
    respect_pdoc: bool
    short_arrays: bool
    show_dataclass_module: bool
    show_type_module: bool
    width: int
