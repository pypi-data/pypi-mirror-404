from collections.abc import Iterable


def len_or_none(iterable: Iterable) -> int | None:
    try:
        return len(iterable)  # pyright: ignore[reportArgumentType]
    except TypeError:
        return None
