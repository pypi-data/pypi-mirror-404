import collections
from collections.abc import Callable, Iterable, Sequence

import attrs
import limits

from liblaf.grapes import pretty, warnings
from liblaf.grapes.logging import LazyStr, LimitsHitArgs, autolog

from ._clock import ClockName, clock
from ._statistics import StatisticName, pretty_statistic
from .defaults import (
    DEFAULT_CLOCKS,
    LOG_RECORD_DEFAULT_LEVEL,
    LOG_SUMMARY_DEFAULT_LEVEL,
    LOG_SUMMARY_DEFAULT_STATISTICS,
)


@attrs.define
class Timings:
    label: str | None = attrs.field(default=None)
    name: str | None = attrs.field(default=None)
    clocks: Sequence[ClockName] = attrs.field(default=DEFAULT_CLOCKS)
    timings: dict[ClockName, list[float]] = attrs.field(
        factory=lambda: collections.defaultdict(list), init=False
    )

    _start_time: dict[ClockName, float] = attrs.field(factory=dict, init=False)
    _stop_time: dict[ClockName, float] = attrs.field(factory=dict, init=False)

    def __attrs_post_init__(self) -> None:
        _warnings_hide = True
        if self.label is None and self.name is not None:
            warnings.warn(
                "'name' parameter is deprecated. Please use 'label' instead.",
                DeprecationWarning,
            )
            self.label = self.name

    def __len__(self) -> int:
        return len(self.timings[self.default_clock])

    @property
    def default_clock(self) -> ClockName:
        return self.clocks[0]

    def clear(self) -> None:
        self.timings.clear()
        self._start_time.clear()
        self._stop_time.clear()

    def elapsed(self, clock_name: ClockName | None = None) -> float:
        clock_name = clock_name or self.default_clock
        stop_time: float
        if clock_name in self._stop_time:
            stop_time = self._stop_time[clock_name]
        else:
            stop_time = clock(clock_name)
        return stop_time - self._start_time[clock_name]

    def log_record(
        self,
        *,
        index: int = -1,
        level: int = LOG_RECORD_DEFAULT_LEVEL,
        limits: str | limits.RateLimitItem | None = "1/second",
    ) -> None:
        _logging_hide = True
        autolog.log(
            level,
            "%s",
            LazyStr(lambda: self.pretty_record(index=index)),
            extra={
                "limits": LimitsHitArgs(
                    item=limits, identifiers=(self.label or "Timer",)
                )
            },
        )

    def log_summary(
        self,
        *,
        level: int = LOG_SUMMARY_DEFAULT_LEVEL,
        stats: Iterable[StatisticName] = LOG_SUMMARY_DEFAULT_STATISTICS,
        limits: str | limits.RateLimitItem | None = None,
    ) -> None:
        _logging_hide = True
        autolog.log(
            level,
            "%s",
            LazyStr(lambda: self.pretty_summary(stats=stats)),
            extra={
                "limits": LimitsHitArgs(
                    item=limits, identifiers=(self.label or "Timer",)
                ),
                "markup": lambda: self.pretty_summary(stats=stats, rich_markup=True),
            },
        )

    def pretty_record(self, index: int = -1) -> str:
        name: str = self.label or "Timer"
        items: list[str] = [
            f"{clock_name}: {pretty.pretty_duration(self.timings[clock_name][index])}"
            for clock_name in self.clocks
        ]
        items_str: str = ", ".join(items)
        return f"{name} > {items_str}"

    def pretty_summary(
        self,
        stats: Iterable[StatisticName] = LOG_SUMMARY_DEFAULT_STATISTICS,
        *,
        rich_markup: bool = False,
    ) -> str:
        name: str = self.label or "Timer"
        header: str = f"{name} (count: {len(self)})"
        if len(self) == 0:
            return header
        lines: list[str] = []
        for clock_name in self.clocks:
            stats_str: list[str] = []
            for stat in stats:
                stat_name: str
                value: str
                stat_name, value = pretty_statistic(
                    self.timings[clock_name], stat, rich_markup=rich_markup
                )
                stats_str.append(f"{stat_name}: {value}")
            line: str = f"{clock_name} > {', '.join(stats_str)}"
            lines.append(line)
        if len(self.clocks) == 1:
            return f"{header} {lines[0]}"
        return f"{header}\n" + "\n".join(lines)


type Callback = Callable[[Timings], None]
