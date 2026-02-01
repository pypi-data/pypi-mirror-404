from logging import LogRecord
from typing import override

import attrs
from pendulum import DateTime
from rich.text import Text

from liblaf.grapes._config import config

from ._abc import RichHandlerColumn


@attrs.define
class RichHandlerColumnTime(RichHandlerColumn):
    fmt: str = attrs.field(factory=config.logging.datefmt.get)
    relative: bool = attrs.field(factory=config.logging.time_relative.get)

    @override
    def render(self, record: LogRecord) -> Text:
        plain: str = (
            self._render_relative(record)
            if self.relative
            else self._render_created(record)
        )
        return Text(plain, "log.time")

    def _render_created(self, record: LogRecord) -> str:
        time: DateTime = DateTime.fromtimestamp(record.created)
        return time.format(self.fmt)

    def _render_relative(self, record: LogRecord) -> str:
        milliseconds: int = round(record.relativeCreated)
        days: int
        days, milliseconds = divmod(milliseconds, 86400000)
        hours: int
        hours, milliseconds = divmod(milliseconds, 3600000)
        minutes: int
        minutes, milliseconds = divmod(milliseconds, 60000)
        seconds: int
        seconds, milliseconds = divmod(milliseconds, 1000)
        text: str = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
        return f"{days}d,{text}" if days > 0 else text
