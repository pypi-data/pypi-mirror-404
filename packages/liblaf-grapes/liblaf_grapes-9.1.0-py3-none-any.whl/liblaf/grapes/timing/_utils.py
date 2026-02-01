from typing import Any, overload

import liblaf.grapes.functools as ft
from liblaf.grapes.sentinel import MISSING

from ._base import BaseTimer


@overload
def get_timer(wrapper: Any) -> BaseTimer: ...
@overload
def get_timer[T](wrapper: Any, default: T) -> BaseTimer | T: ...
def get_timer(wrapper: Any, default: Any = MISSING) -> Any:
    if default is MISSING:
        return ft.wrapt_getattr(wrapper, "timer")
    return ft.wrapt_getattr(wrapper, "timer", default)


def set_timer(wrapper: Any, timer: BaseTimer) -> None:
    ft.wrapt_setattr(wrapper, "timer", timer)
