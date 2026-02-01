from collections.abc import Iterable

from ._quantiphy import PrettyQuantitiesComponents, pretty_quantities, pretty_quantity


def pretty_duration(seconds: float, *, prec: int = 2, **kwargs) -> str:
    """.

    Examples:
        >>> pretty_duration(0.1234)
        '123. ms'
        >>> pretty_duration(0.01234)
        '12.3 ms'
    """
    return pretty_quantity(seconds, "s", prec=prec, **kwargs)


def pretty_durations(
    seconds: Iterable[float], *, prec: int = 2, **kwargs
) -> PrettyQuantitiesComponents:
    """.

    Examples:
        >>> pretty_durations([0.1234, 0.01234, 0.001234])
        PrettyQuantitiesComponents(mantissas=['123.', '12.', '1.'], spacer=' ', units='ms')
    """
    return pretty_quantities(seconds, "s", prec=prec, **kwargs)
