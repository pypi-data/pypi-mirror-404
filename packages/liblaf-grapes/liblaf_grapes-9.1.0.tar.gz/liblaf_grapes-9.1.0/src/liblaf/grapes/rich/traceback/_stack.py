import functools
import types
from collections.abc import Generator

import attrs
import rich
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.panel import Panel
from rich.text import Text

from ._frame import RichFrameSummary
from ._options import RichTracebackOptions


@attrs.define
class RichStackSummary:
    traceback: types.TracebackType | None

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from self.render()

    @functools.cached_property
    def frames(self) -> list[RichFrameSummary]:
        frames: list[RichFrameSummary] = []
        traceback: types.TracebackType | None = self.traceback
        while traceback is not None:
            frames.append(
                RichFrameSummary(
                    traceback.tb_frame, traceback.tb_lineno, traceback.tb_lasti
                )
            )
            traceback = traceback.tb_next
        return frames

    def render(
        self, options: RichTracebackOptions | None = None
    ) -> Generator[RenderableType]:
        if options is None:
            options = RichTracebackOptions()
        if not self.frames:
            return
        panel = Panel(
            self._render_frames(options),
            title=Text.assemble(
                "Traceback ",
                ("(most recent call last)", "dim"),
                style="traceback.title",
            ),
            expand=False,
            style=options.theme.get_background_style(),
            border_style="traceback.border",
        )
        yield panel

    @rich.console.group()
    def _render_frames(self, options: RichTracebackOptions) -> RenderResult:
        for frame in self.frames:
            yield from frame.render(options)
