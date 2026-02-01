import logging
from typing import Any, override

import limits
from rich.console import Console
from rich.progress import (
    BarColumn,
    GetTimeCallable,
    MofNCompleteColumn,
    ProgressColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.progress import Progress as RichProgress

from liblaf.grapes.logging.helpers import autolog

from ._rate_column import RateColumn


class Progress(RichProgress):
    limit: limits.RateLimitItem
    limiter: limits.strategies.RateLimiter
    logger: logging.Logger
    stale: bool = False

    def __init__(
        self,
        *columns: str | ProgressColumn,
        limit: str | limits.RateLimitItem | None = None,
        limiter: limits.strategies.RateLimiter | None = None,
        logger: logging.Logger | None = None,
        # RichProgress options
        speed_estimate_period: float = 30.0,
        get_time: GetTimeCallable | None = None,
        disable: bool = False,
        expand: bool = False,
    ) -> None:
        super().__init__(
            *columns,
            console=Console(quiet=True),
            auto_refresh=False,
            speed_estimate_period=speed_estimate_period,
            get_time=get_time,
            disable=disable,
            expand=expand,
        )
        if limit is None:
            limit = limits.RateLimitItemPerSecond(1)
        elif isinstance(limit, str):
            limit = limits.parse(limit)
        self.limit = limit
        if limiter is None:
            limiter = limits.strategies.SlidingWindowCounterRateLimiter(
                limits.storage.MemoryStorage()
            )
        self.limiter = limiter
        if logger is None:
            logger = autolog
        self.logger = logger

    @override
    @classmethod
    def get_default_columns(cls) -> tuple[str | ProgressColumn, ...]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return (
            # SpinnerColumn(),
            TextColumn("{task.description}", style="progress.description"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            "[",
            TimeElapsedColumn(),
            "<",
            TimeRemainingColumn(),
            ",",
            RateColumn(),
            "]",
        )

    @override
    def advance(self, task_id: TaskID, advance: float = 1) -> None:
        _logging_hide = True
        self.stale = True
        super().advance(task_id, advance)
        self.refresh()

    @override
    def refresh(self, *, force: bool = False) -> None:
        _logging_hide = True
        if self.stale and (self.limiter.hit(self.limit) or force):
            self.stale = False
            self.logger.info(self.get_renderable())

    @override
    def reset(
        self,
        task_id: TaskID,
        *,
        start: bool = True,
        total: float | None = None,
        completed: int = 0,
        visible: bool | None = None,
        description: str | None = None,
        **fields: Any,
    ) -> None:
        _logging_hide = True
        self.stale = True
        super().reset(
            task_id,
            start=start,
            total=total,
            completed=completed,
            visible=visible,
            description=description,
            **fields,
        )

    @override
    def start(self) -> None:
        pass

    @override
    def stop(self) -> None:
        _logging_hide = True
        self.refresh(force=True)

    @override
    def update(
        self,
        task_id: TaskID,
        *,
        total: float | None = None,
        completed: float | None = None,
        advance: float | None = None,
        description: str | None = None,
        visible: bool | None = None,
        refresh: bool = False,
        **fields: Any,
    ) -> None:
        _logging_hide = True
        self.stale = True
        super().update(
            task_id,
            total=total,
            completed=completed,
            advance=advance,
            description=description,
            visible=visible,
            refresh=refresh,
            **fields,
        )
