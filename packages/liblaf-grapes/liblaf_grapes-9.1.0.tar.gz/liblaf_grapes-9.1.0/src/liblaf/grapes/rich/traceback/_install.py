import sys
import types

from rich.console import Console

from liblaf.grapes.rich._get_console import get_console

from ._exception import RichExceptionSummary


def install(*, console: Console | None = None) -> None:
    if console is None:
        console = get_console(stderr=True)

    def excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        traceback: types.TracebackType | None,
    ) -> None:
        exc = RichExceptionSummary(exc_type, exc_value, traceback)
        console.print(exc)

    sys.excepthook = excepthook
