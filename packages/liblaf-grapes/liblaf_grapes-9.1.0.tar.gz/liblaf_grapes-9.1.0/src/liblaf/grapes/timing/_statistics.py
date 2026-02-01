import math
import statistics
from collections.abc import Sequence

import autoregistry

from liblaf.grapes import pretty

type StatisticName = str


STATISTICS_REGISTRY = autoregistry.Registry(prefix="_compute_")


STATISTICS_REGISTRY["max"] = max
STATISTICS_REGISTRY["mean"] = statistics.mean
STATISTICS_REGISTRY["median"] = statistics.median
STATISTICS_REGISTRY["min"] = min
STATISTICS_REGISTRY["stdev"] = statistics.stdev
STATISTICS_REGISTRY["total"] = sum


def compute_statistic(series: Sequence[float], stat_name: StatisticName) -> float:
    try:
        return STATISTICS_REGISTRY[stat_name](series)
    except (ValueError, statistics.StatisticsError):
        return math.nan


def pretty_statistic(
    series: Sequence[float], stat_name: StatisticName, *, rich_markup: bool = False
) -> tuple[str, str]:
    match stat_name:
        case "mean+stdev":
            mean: float = compute_statistic(series, "mean")
            stdev: float = compute_statistic(series, "stdev")
            pretty_name: str = (
                "[bold green]mean[/bold green] ± [green]σ[/green]"  # noqa: RUF001
                if rich_markup
                else "mean ± σ"  # noqa: RUF001
            )
            mantissas: list[str]
            spacer: str
            units: str
            mantissas, spacer, units = pretty.pretty_durations((mean, stdev))
            pretty_mean: str
            pretty_stdev: str
            pretty_mean, pretty_stdev = mantissas
            if rich_markup:
                pretty_mean = f"[bold green]{pretty_mean}[/bold green]"
                pretty_stdev = f"[green]{pretty_stdev}[/green]"
            if units and rich_markup:
                units = f"[green]{units}[/green]"
            return pretty_name, f"{pretty_mean} ± {pretty_stdev}{spacer}{units}"
        case "range":
            minimum: float = compute_statistic(series, "min")
            maximum: float = compute_statistic(series, "max")
            pretty_name: str = (
                "[cyan]min[/cyan] … [magenta]max[/magenta]"
                if rich_markup
                else "min … max"
            )
            mantissas: list[str]
            spacer: str
            units: str
            mantissas, spacer, units = pretty.pretty_durations((minimum, maximum))
            pretty_min: str
            pretty_max: str
            pretty_min, pretty_max = mantissas
            if rich_markup:
                pretty_min = f"[cyan]{pretty_min}[/cyan]"
                pretty_max = f"[magenta]{pretty_max}[/magenta]"
            if units and rich_markup:
                units = f"[magenta]{units}[/magenta]"
            return pretty_name, f"{pretty_min} … {pretty_max}{spacer}{units}"
        case stat_name:
            value: float = compute_statistic(series, stat_name)
            return stat_name, pretty.pretty_duration(value)
