from collections.abc import Generator, Iterable

import wrapt

from ._base import BaseTimer
from ._utils import get_timer, set_timer


class TimedIterable[T](wrapt.ObjectProxy):
    def __init__(self, wrapped: Iterable[T], timer: BaseTimer) -> None:
        super().__init__(wrapped)
        if timer.label is None:
            timer.label = "Iterable"
        set_timer(self, timer)

    def __iter__(self) -> Generator[T]:
        _logging_hide = True
        timer: BaseTimer = get_timer(self)
        timer.start()
        try:
            for item in self.__wrapped__:
                yield item
                timer.stop()
                timer.start()
        finally:
            # When the `for` loop is exhausted, it does not re-enter the loop
            # body. Therefore, the `start()` call after the *last* item is
            # redundant. However, since `timer._start_time` is not used anywhere
            # else, we can safely leave it out.
            timer.finish()
