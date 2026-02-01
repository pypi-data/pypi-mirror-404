from collections.abc import Iterable

from ._progress import Progress


def track[T](
    sequence: Iterable[T],
    total: float | None = None,
    completed: int = 0,
    description: str = "Working...",
    *,
    progress: Progress | None = None,
) -> Iterable[T]:
    _logging_hide = True
    if progress is None:
        progress = Progress()
    with progress:
        yield from progress.track(
            sequence, total=total, completed=completed, description=description
        )
