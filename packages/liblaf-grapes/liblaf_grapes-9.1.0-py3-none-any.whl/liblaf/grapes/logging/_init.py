from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from liblaf.grapes._config import config
from liblaf.grapes.rich.logging import RichHandler

from .filters import LimitsFilter
from .handlers import RichFileHandler
from .helpers import (
    init_levels,
    install_excepthook,
    install_unraisablehook,
    remove_non_root_stream_handlers,
    set_default_logger_level_by_release_type,
)

if TYPE_CHECKING:
    from _typeshed import StrPath


def init(*, file: StrPath | None = None, force: bool = False) -> None:
    if file is None:
        file = config.logging.file.get()
    handlers: list[logging.Handler] = []
    if force or not logging.root.hasHandlers():
        handlers.append(RichHandler())
        if file is not None:
            handlers.append(RichFileHandler(file))
        for handler in handlers:
            handler.addFilter(LimitsFilter())
    init_levels()
    install_excepthook()
    install_unraisablehook()
    logging.basicConfig(handlers=handlers, force=force)
    logging.captureWarnings(True)  # noqa: FBT003
    logging.getLogger("liblaf").setLevel(logging.DEBUG)
    remove_non_root_stream_handlers()
    set_default_logger_level_by_release_type()
