import logging
from typing import override

import attrs
from rich.align import AlignMethod
from rich.text import Text

from ._abc import RichHandlerColumn

_LEVEL_ALIASES: dict[int, dict[str, str]] = {
    1: {"ICECREAM": "M"},
    3: {
        "NOTSET": "NST",
        "TRACE": "TRC",
        "DEBUG": "DBG",
        "ICECREAM": "ICM",
        "INFO": "INF",
        "SUCCESS": "SUC",
        "WARNING": "WRN",
        "ERROR": "ERR",
        "CRITICAL": "CRT",
    },
}


@attrs.define
class RichHandlerColumnLevel(RichHandlerColumn):
    align: AlignMethod = "right"
    width: int = 3

    @override
    def render(self, record: logging.LogRecord) -> Text:
        level: str = self._get_abbr(record)
        text = Text(level, f"logging.level.{record.levelname.lower()}")
        text.align(self.align, self.width)
        return text

    def _get_abbr(self, record: logging.LogRecord) -> str:
        if record.levelname == f"Level {record.levelno}":
            return str(record.levelno)
        aliases: dict[str, str] = _LEVEL_ALIASES.get(self.width, {})
        return aliases.get(record.levelname, record.levelname)
