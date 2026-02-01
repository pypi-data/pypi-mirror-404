import logging
import sys
import types
from typing import ClassVar, override

from liblaf.grapes import magic


class CleanLogger(logging.Logger):
    dev_level: ClassVar[int | str] = 1
    pre_level: ClassVar[int | str] = logging.DEBUG

    def __init__(self, name: str, level: int | str = logging.NOTSET) -> None:
        _logging_hide = True
        super().__init__(name, level)
        if level != logging.NOTSET:
            return
        module: types.ModuleType | None = sys.modules.get(name)
        file: str | None = None
        if module is not None:
            file = getattr(module, "__file__", None)
        if file is None:
            frame: types.FrameType | None = magic.get_frame(
                hidden=magic.hidden_from_logging
            )
            if frame is not None:
                file = frame.f_code.co_filename
        if magic.is_dev_release(file, name):
            self.setLevel(self.dev_level)
        elif magic.is_pre_release(file, name):
            self.setLevel(self.pre_level)

    @property
    def propagate(self) -> bool:  # pyright: ignore[reportIncompatibleVariableOverride]
        return True

    @propagate.setter
    def propagate(self, value: bool) -> None:  # pyright: ignore[reportIncompatibleVariableOverride]
        pass

    @override
    def addHandler(self, hdlr: logging.Handler) -> None:
        if self.name != "root" and isinstance(hdlr, logging.StreamHandler):
            return
        super().addHandler(hdlr)


def set_default_logger_level_by_release_type(
    dev_level: int | str | None = None, pre_level: int | str | None = None
) -> None:
    if dev_level is not None:
        CleanLogger.dev_level = dev_level
    if pre_level is not None:
        CleanLogger.pre_level = pre_level
    logging.setLoggerClass(CleanLogger)


def _is_logging_frame(frame: types.FrameType) -> bool:
    if frame.f_locals.get("__tracebackhide__", False):
        return True
    name: str | None = frame.f_globals.get("__name__")
    if name is None:
        return False
    return name == "logging" or name.startswith("logging.")
