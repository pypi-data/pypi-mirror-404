import logging
import types
from collections.abc import Generator, Iterable
from typing import cast

from rich.console import Console, ConsoleRenderable, RenderableType, RichCast
from rich.highlighter import Highlighter, ReprHighlighter
from rich.text import Text

from liblaf.grapes import pretty
from liblaf.grapes.rich._get_console import get_console
from liblaf.grapes.rich.traceback import RichExceptionSummary

from .columns import (
    RichHandlerColumn,
    RichHandlerColumnLevel,
    RichHandlerColumnLocation,
    RichHandlerColumnTime,
)


def _default_columns() -> list[RichHandlerColumn]:
    return [
        RichHandlerColumnTime(),
        RichHandlerColumnLevel(),
        RichHandlerColumnLocation(),
    ]


class RichHandler(logging.Handler):
    columns: list[RichHandlerColumn]
    console: Console
    highlighter: Highlighter

    def __init__(
        self,
        console: Console | None = None,
        *,
        columns: Iterable[RichHandlerColumn] | None = None,
        level: int = logging.NOTSET,
    ) -> None:
        super().__init__(level=level)
        columns = _default_columns() if columns is None else list(columns)
        if console is None:
            console = get_console(stderr=True)
        self.columns = columns
        self.console = console
        self.highlighter = ReprHighlighter()

    def emit(self, record: logging.LogRecord) -> None:
        self.console.print(
            *self._render(record),
            sep="",
            end="",
            overflow="ignore",
            no_wrap=True,
            highlight=False,
            crop=False,
            soft_wrap=False,
        )
        if (exception := self._render_exception(record)) is not None:
            self.console.print(exception)

    def _render(self, record: logging.LogRecord) -> Generator[RenderableType]:
        columns: list[Text] = [
            result
            for column in self.columns
            if (result := column.render(record)) is not None
        ]
        meta: Text = Text(" ").join(columns)
        message: Text = self._render_message(record)
        for line in message.split() or [""]:
            yield meta
            if len(line) > 0:
                yield " "
                yield line
            yield "\n"

    def _render_exception(
        self, record: logging.LogRecord
    ) -> RichExceptionSummary | None:
        if record.exc_info is None:
            return None
        exc_type: type[BaseException] | None
        exc_value: BaseException | None
        traceback: types.TracebackType | None
        exc_type, exc_value, traceback = record.exc_info
        if exc_type is None or exc_value is None:
            return None
        return RichExceptionSummary(exc_type, exc_value, traceback)

    def _render_message(self, record: logging.LogRecord) -> Text:
        if markup := getattr(record, "markup", None):
            if callable(markup):
                markup = cast("str", markup())
            return Text.from_markup(markup, style="log.message")
        if isinstance(record.msg, (ConsoleRenderable, RichCast)):
            with self.console.capture() as capture:
                self.console.print(record.msg)
            return Text.from_ansi(capture.get(), style="log.message")
        message: str = record.getMessage()
        if pretty.has_ansi(message):
            return Text.from_ansi(message, style="log.message")
        text: Text = Text(message, style="log.message")
        return self.highlighter(text)
