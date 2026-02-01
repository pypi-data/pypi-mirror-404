import functools
import os
import sys
from typing import IO

import rich
from rich.console import Console
from rich.style import Style
from rich.theme import Theme

from liblaf.grapes import magic
from liblaf.grapes.functools import wraps


def default_theme() -> Theme:
    """.

    References:
        1. <https://github.com/Delgan/loguru/blob/master/loguru/_defaults.py>
    """
    return Theme(
        {
            "logging.level.notset": Style(dim=True),
            "logging.level.trace": Style(color="cyan", bold=True),
            "logging.level.debug": Style(color="blue", bold=True),
            "logging.level.icecream": Style(color="magenta", bold=True),
            "logging.level.info": Style(bold=True),
            "logging.level.success": Style(color="green", bold=True),
            "logging.level.warning": Style(color="yellow", bold=True),
            "logging.level.error": Style(color="red", bold=True),
            "logging.level.critical": Style(color="red", bold=True, reverse=True),
        },
        inherit=True,
    )


@wraps(Console)
@functools.cache
def get_console(**kwargs) -> Console:
    if kwargs.get("theme") is None:
        kwargs["theme"] = default_theme()
    file: IO[str] | None = kwargs.get("file")
    stderr: bool = file is None and kwargs.get("stderr", False)
    stdout: bool = file is None and not stderr
    if "force_terminal" not in kwargs and (stdout or stderr) and magic.in_ci():
        kwargs["force_terminal"] = True
    if "width" not in kwargs and (
        (stdout and not sys.stdout.isatty())
        or (stderr and not sys.stderr.isatty())
        or (file is not None and not os.isatty(file.fileno()))
    ):
        kwargs["width"] = 128
    if stdout:
        rich.reconfigure(**kwargs)
        return rich.get_console()
    return Console(**kwargs)
