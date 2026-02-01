import functools
import types
from collections.abc import Generator
from typing import Self

import attrs
from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.highlighter import Highlighter, ReprHighlighter
from rich.panel import Panel
from rich.text import Text

from liblaf.grapes import pretty

from ._options import RichTracebackOptions
from ._stack import RichStackSummary


@attrs.define
class RichExceptionSummary:
    exc_type: type[BaseException]
    exc_value: BaseException
    traceback: types.TracebackType | None
    highlighter: Highlighter = attrs.field(
        repr=False, init=False, factory=ReprHighlighter
    )
    _seen: set[int] = attrs.field(factory=set, repr=False, alias="_seen")

    def __attrs_post_init__(self) -> None:
        self._seen.add(id(self.exc_value))

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from self.render()

    @functools.cached_property
    def cause(self) -> Self | None:
        cause: BaseException | None = self.exc_value.__cause__
        if cause is not None and id(cause) not in self._seen:
            return type(self)(type(cause), cause, cause.__traceback__, _seen=self._seen)
        return None

    @functools.cached_property
    def context(self) -> Self | None:
        context: BaseException | None = self.exc_value.__context__
        if (
            context is not None
            and not self.exc_value.__suppress_context__
            and id(context) not in self._seen
        ):
            return type(self)(
                type(context), context, context.__traceback__, _seen=self._seen
            )
        return None

    @functools.cached_property
    def exceptions(self) -> list[Self]:
        if not isinstance(self.exc_value, (BaseExceptionGroup, ExceptionGroup)):
            return []
        exceptions: list[Self] = []
        for exception in self.exc_value.exceptions:
            if id(exception) in self._seen:
                continue
            exceptions.append(
                type(self)(
                    type(exception),
                    exception,
                    exception.__traceback__,
                    _seen=self._seen,
                )
            )
        return exceptions

    @functools.cached_property
    def exc_type_str(self) -> str:
        module: str = self.exc_type.__module__
        qualname: str = self.exc_type.__qualname__
        if module in ("__main__", "builtins"):
            return qualname
        return f"{module}.{qualname}"

    @functools.cached_property
    def stack(self) -> RichStackSummary:
        return RichStackSummary(self.traceback)

    def render(
        self, options: RichTracebackOptions | None = None
    ) -> Generator[RenderableType]:
        if options is None:
            options = RichTracebackOptions()
        if self.cause is not None:
            yield from self.cause.render(options)
            yield Text(
                "\nThe above exception was the direct cause of the following exception:\n",
                style="italic",
            )
        if self.context is not None:
            yield from self.context.render(options)
            yield Text(
                "\nDuring handling of the above exception, another exception occurred:\n",
                style="italic",
            )
        yield from self.stack.render(options)
        yield from self._render_exception_only(options)
        if self.exceptions:
            yield from self._render_subexceptions(options)

    def _render_exception_only(
        self, _options: RichTracebackOptions
    ) -> Generator[RenderableType]:
        exc_value: str = str(self.exc_value)
        if exc_value:
            exc_value_text: Text
            if pretty.has_ansi(exc_value):
                exc_value_text = Text.from_ansi(exc_value, style="traceback.exc_value")
            else:
                exc_value_text = Text(exc_value, style="traceback.exc_value")
                exc_value_text = self.highlighter(exc_value_text)
            yield Text.assemble(
                (f"{self.exc_type_str}:", "traceback.exc_type"), " ", exc_value_text
            )
        else:
            yield Text(self.exc_type_str, style="traceback.exc_type")
        for note in getattr(self.exc_value, "__notes__", ()):
            yield Text.assemble(("[NOTE]", "traceback.note"), " ", note)

    def _render_subexceptions(
        self, options: RichTracebackOptions
    ) -> Generator[RenderableType]:
        for i, exception in enumerate(self.exceptions, start=1):
            panel = Panel(
                Group(*exception.render(options)),
                title=f"Sub-exception #{i}",
                expand=False,
                border_style="traceback.group.border",
            )
            yield panel
