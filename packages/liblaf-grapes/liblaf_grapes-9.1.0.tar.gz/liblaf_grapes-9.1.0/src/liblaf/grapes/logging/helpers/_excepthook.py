import logging
import sys
import types

logger: logging.Logger = logging.getLogger()


def install_excepthook(level: int = logging.CRITICAL) -> None:
    def excepthook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: types.TracebackType | None,
    ) -> None:
        logger.log(level, exc_value, exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = excepthook
