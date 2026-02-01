import logging
from collections.abc import Mapping

from liblaf.grapes.icecream import ICECREAM

_DEFAULT_LEVELS: dict[int, str] = {5: "TRACE", ICECREAM: "ICECREAM", 25: "SUCCESS"}


def init_levels(levels: Mapping[int, str] | None = None) -> None:
    if levels is None:
        levels = _DEFAULT_LEVELS
    for level, name in levels.items():
        logging.addLevelName(level, name)
