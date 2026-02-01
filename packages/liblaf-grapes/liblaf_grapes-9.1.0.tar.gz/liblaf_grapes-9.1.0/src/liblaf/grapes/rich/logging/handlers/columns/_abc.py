import abc
import logging

from rich.text import Text


class RichHandlerColumn(abc.ABC):
    @abc.abstractmethod
    def render(self, record: logging.LogRecord, /) -> Text | None: ...
