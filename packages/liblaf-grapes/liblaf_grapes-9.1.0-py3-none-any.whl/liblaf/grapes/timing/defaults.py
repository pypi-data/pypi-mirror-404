import logging
from collections.abc import Iterable, Sequence

from ._clock import ClockName
from ._statistics import StatisticName

DEFAULT_CLOCKS: Sequence[ClockName] = ("perf",)


LOG_RECORD_DEFAULT_LEVEL: int = logging.DEBUG


LOG_SUMMARY_DEFAULT_LEVEL: int = logging.INFO
LOG_SUMMARY_DEFAULT_STATISTICS: Iterable[StatisticName] = (
    "total",
    "mean+stdev",
    "range",
    # "median",
)
