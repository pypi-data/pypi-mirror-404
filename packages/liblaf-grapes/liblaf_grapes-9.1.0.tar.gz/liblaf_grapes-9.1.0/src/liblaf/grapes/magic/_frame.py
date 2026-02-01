import inspect
import types
from collections.abc import Callable, Iterable, Mapping

from liblaf.grapes._config import config

from ._release_type import is_pre_release


def hidden_from_logging(frame: types.FrameType | None) -> bool:
    if frame is None:
        return False
    # `__logging_hide` does not work as expected in some cases due to name mangling
    # `__logging_hide__` will violate Ruff F841
    # so we use `_logging_hide` here
    if _coalesce(frame.f_locals, ("_logging_hide", "__tracebackhide__")):
        return True
    name: str = frame.f_globals.get("__name__", "")
    return f"{name}.".startswith(tuple(config.logging.hide_frame.get()))


def hidden_from_traceback(
    frame: types.FrameType | None, *, hide_stable_release: bool | None = None
) -> bool:
    if frame is None:
        return False
    if _coalesce(frame.f_locals, ("__tracebackhide__",)):
        return True
    if hide_stable_release is None:
        hide_stable_release = config.traceback.hide_stable_release.get()
    if hide_stable_release:
        name: str | None = frame.f_globals.get("__name__")
        if not is_pre_release(frame.f_code.co_filename, name):
            return True
    return False


def hidden_from_warnings(
    frame: types.FrameType | None, *, hide_stable_release: bool | None = None
) -> bool:
    if frame is None:
        return False
    if _coalesce(frame.f_locals, ("_warnings_hide", "__tracebackhide__")):
        return True
    if hide_stable_release is None:
        hide_stable_release = config.traceback.hide_stable_release.get()
    if hide_stable_release:
        name: str | None = frame.f_globals.get("__name__")
        if not is_pre_release(frame.f_code.co_filename, name):
            return True
    return False


def get_frame(
    depth: int = 1, hidden: Callable[[types.FrameType], bool] | None = None
) -> types.FrameType | None:
    frame: types.FrameType | None = inspect.currentframe()
    while frame is not None and depth > 0:
        frame = frame.f_back
        depth -= 1
        if hidden is not None:
            while frame is not None and hidden(frame):
                frame = frame.f_back
    return frame


def get_frame_with_stacklevel(
    depth: int = 1, hidden: Callable[[types.FrameType], bool] | None = None
) -> tuple[types.FrameType | None, int]:
    frame: types.FrameType | None = inspect.currentframe()
    stacklevel: int = 0
    while frame is not None and depth > 0:
        frame = frame.f_back
        depth -= 1
        stacklevel += 1
        if hidden is not None:
            while frame is not None and hidden(frame):
                frame = frame.f_back
                stacklevel += 1
    return frame, stacklevel


def _coalesce[KT, VT](
    obj: Mapping[KT, VT], keys: Iterable[KT], *, default: bool = False
) -> bool:
    for key in keys:
        try:
            return bool(obj[key])
        except (KeyError, ValueError):
            continue
    return default
