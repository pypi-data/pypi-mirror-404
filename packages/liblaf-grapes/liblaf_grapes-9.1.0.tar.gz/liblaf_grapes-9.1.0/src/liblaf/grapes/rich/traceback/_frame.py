import functools
import itertools
import linecache
import types
from collections.abc import Generator
from typing import Any

import attrs
import tlz
from rich.console import Console, ConsoleOptions, RenderableType, RenderResult
from rich.scope import render_scope
from rich.syntax import Syntax
from rich.text import Text

from liblaf.grapes import magic
from liblaf.grapes._config import config

from ._options import RichTracebackOptions


@attrs.define
class RichFrameSummary:
    frame: types.FrameType
    lineno: int
    lasti: int

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield from self.render()

    @functools.cached_property
    def filename(self) -> str:
        return self.frame.f_code.co_filename

    @functools.cached_property
    def hidden(self) -> bool:
        return magic.hidden_from_traceback(self.frame)

    @functools.cached_property
    def locals(self) -> dict[str, Any]:
        return self.frame.f_locals

    @functools.cached_property
    def name(self) -> str:
        return self.frame.f_code.co_name

    @functools.cached_property
    def position(self) -> tuple[int | None, int | None, int | None, int | None]:
        return _get_code_position(self.frame.f_code, self.lasti)

    @functools.cached_property
    def qualname(self) -> str:
        return self.frame.f_code.co_qualname

    @property
    def start_line(self) -> int | None:
        return self.position[0]

    @property
    def end_line(self) -> int | None:
        return self.position[1]

    @property
    def start_column(self) -> int | None:
        return self.position[2]

    @property
    def end_column(self) -> int | None:
        return self.position[3]

    def render(
        self, options: RichTracebackOptions | None = None
    ) -> Generator[RenderableType]:
        if options is None:
            options = RichTracebackOptions()
        yield from self._render_location(options)
        if not self.hidden:
            yield from self._render_syntax(options)
            if options.show_locals:
                yield from self._render_locals(options)

    def _render_location(
        self, _options: RichTracebackOptions
    ) -> Generator[RenderableType]:
        filename: str = magic.abbr_path(self.filename)
        qualname: str = self.qualname
        if qualname != "<module>":
            qualname += "()"
        if self.hidden:
            # ? I don't know why, but adding "white" looks better on Ghostty.
            text: Text = Text.assemble(
                (filename, "repr.filename"),
                (":", "white"),
                (str(self.lineno), "repr.number"),
                (" in ", "white"),
                (qualname, "repr.call"),
                (" --- hidden", "white"),
                style="dim",
            )
            yield text
        else:
            yield Text.assemble(
                (filename, "repr.filename"),
                ":",
                (str(self.lineno), "repr.number"),
                " in ",
                (qualname, "repr.call"),
            )

    def _render_syntax(
        self, options: RichTracebackOptions
    ) -> Generator[RenderableType]:
        lines: list[str] = linecache.getlines(self.filename, self.frame.f_globals)
        code: str = "".join(lines)
        lexer: str = Syntax.guess_lexer(self.filename, code)
        syntax = Syntax(
            code,
            lexer,
            theme=options.theme,
            line_numbers=True,
            line_range=(self.start_line, self.end_line),
            indent_guides=True,
        )
        if all(v is not None for v in self.position):
            # ref: <https://github.com/Textualize/rich/blob/4d6d631a3d2deddf8405522d4b8c976a6d35726c/rich/traceback.py#L841C25-L859>
            # Stylize a line at a time
            # So that indentation isn't underlined (which looks bad)
            for lineno, start_col, end_col in _iter_syntax_lines(*self.position):  # pyright: ignore[reportArgumentType]
                if start_col == 0:
                    line: str = lines[lineno - 1]
                    stripped: str = line.lstrip()
                    start_col: int = len(line) - len(stripped)  # noqa: PLW2901
                if end_col == -1:
                    end_col: int = len(lines[lineno - 1])  # noqa: PLW2901
                syntax.stylize_range(
                    "traceback.error_range", (lineno, start_col), (lineno, end_col)
                )
        yield syntax

    def _render_locals(
        self, options: RichTracebackOptions
    ) -> Generator[RenderableType]:
        locals_: dict[str, Any] = self.locals
        if options.locals_hide_dunder:
            locals_ = tlz.keyfilter(_not_dunder, locals_)
        if options.locals_hide_sunder:
            locals_ = tlz.keyfilter(_not_sunder, locals_)
        if not locals_:
            return
        with config.pretty.indent.overrides(4):
            yield render_scope(
                locals_,
                title="locals",
                indent_guides=options.indent_guide,
                max_length=options.locals_max_length,
                max_string=options.locals_max_string,
            )


def _not_dunder(key: str) -> bool:
    return not key.startswith("__")


def _not_sunder(key: str) -> bool:
    return not key.startswith("_") or key.startswith("__")


def _get_code_position(
    code: types.CodeType, instruction_index: int
) -> tuple[int | None, int | None, int | None, int | None]:
    # ref: <https://github.com/python/cpython/blob/4885ecfbda4cc792691e5d488ef6cb09727eb417/Lib/traceback.py#L431-L435>
    if instruction_index < 0:
        return (None, None, None, None)
    return next(itertools.islice(code.co_positions(), instruction_index // 2, None))


def _iter_syntax_lines(
    start_line: int, end_line: int, start_column: int, end_column: int
) -> Generator[tuple[int, int, int]]:
    # ref: <https://github.com/Textualize/rich/blob/4d6d631a3d2deddf8405522d4b8c976a6d35726c/rich/traceback.py#L55-L80>
    if start_line == end_line:
        yield start_line, start_column, end_column
    else:
        yield start_line, start_column, -1
        for line in range(start_line + 1, end_line):
            yield line, 0, -1
        yield end_line, 0, end_column
