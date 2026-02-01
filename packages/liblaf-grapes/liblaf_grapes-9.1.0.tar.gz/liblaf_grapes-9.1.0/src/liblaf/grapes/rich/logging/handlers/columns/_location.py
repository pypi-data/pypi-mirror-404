from logging import LogRecord
from typing import override

from rich.text import Text

from ._abc import RichHandlerColumn


class RichHandlerColumnLocation(RichHandlerColumn):
    @override
    def render(self, record: LogRecord) -> Text | None:
        if record.name == "py.warnings":
            return Text(record.name, "log.path")
        plain: str = f"{record.name}:{record.funcName}:{record.lineno}"
        return Text(plain, "log.path")
