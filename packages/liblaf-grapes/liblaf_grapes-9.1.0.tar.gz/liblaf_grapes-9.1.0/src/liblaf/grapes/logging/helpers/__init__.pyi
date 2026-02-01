from ._autolog import autolog
from ._excepthook import install_excepthook
from ._lazy import LazyRepr, LazyStr
from ._level import init_levels
from ._logger import CleanLogger, set_default_logger_level_by_release_type
from ._remove_handlers import remove_non_root_stream_handlers
from ._tree import LoggerTree
from ._unraisablehook import install_unraisablehook

__all__ = [
    "CleanLogger",
    "LazyRepr",
    "LazyStr",
    "LoggerTree",
    "autolog",
    "init_levels",
    "install_excepthook",
    "install_unraisablehook",
    "remove_non_root_stream_handlers",
    "set_default_logger_level_by_release_type",
]
