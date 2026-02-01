from collections.abc import Iterable
from typing import NamedTuple

import quantiphy
from quantiphy import Quantity

# to make unit conversion work, unit must be a non-empty string
_SENTINEL_UNIT = "SENTINEL_UNIT"


class PrettyQuantitiesComponents(NamedTuple):
    mantissas: list[str]
    spacer: str
    units: str


class PrettyQuantityComponents(NamedTuple):
    whole: str
    frac: str
    units: str


def pretty_quantities(
    values: Iterable[float], unit: str | None = None, *, prec: int = 2, **kwargs
) -> PrettyQuantitiesComponents:
    """.

    Examples:
        >>> pretty_quantities([0.1234, 0.01234, 0.001234], "s")
        PrettyQuantitiesComponents(mantissas=['123.', '12.', '1.'], spacer=' ', units='ms')
    """
    unit_or_sentinel: str = unit or _SENTINEL_UNIT
    components: PrettyQuantityComponents = pretty_quantity_components(
        max(values), unit_or_sentinel, prec=prec, **kwargs
    )
    spacer: str = _get_spacer(unit)

    def number_fmt(whole: str, frac: str, _units: str) -> str:
        if not frac.startswith("."):
            frac = f".{frac}"
        return f"{whole}{frac}"

    with Quantity.prefs(
        map_sf=Quantity.map_sf_to_greek,
        number_fmt=number_fmt,
        strip_radix=False,
        strip_zeros=False,
        show_units=False,
    ):
        mantissas: list[str] = [
            quantiphy.fixed(
                value,
                unit_or_sentinel,
                prec=len(components.frac) - 1,
                scale=components.units,
            )
            for value in values
        ]
    units: str = components.units
    if unit is None:
        units = units.removesuffix(_SENTINEL_UNIT)
    return PrettyQuantitiesComponents(mantissas, spacer, units)


def pretty_quantity(
    value: float, unit: str | None = None, *, prec: int = 2, **kwargs
) -> str:
    """.

    Examples:
        >>> pretty_quantity(0.1234, "s")
        '123. ms'
        >>> pretty_quantity(0.01234, "s")
        '12.3 ms'
    """
    spacer: str = _get_spacer(unit)

    def number_fmt(whole: str, frac: str, units: str) -> str:
        if not frac.startswith("."):
            frac = f".{frac}"
        mantissa: str = f"{whole}{frac}"
        return f"{mantissa}{spacer}{units}"

    with Quantity.prefs(
        map_sf=Quantity.map_sf_to_greek,
        number_fmt=number_fmt,
        strip_radix=False,
        strip_zeros=False,
    ):
        q: Quantity = Quantity(value) if unit is None else Quantity(value, unit)
        return q.render(prec=prec, **kwargs)


def pretty_quantity_components(
    value: float, unit: str | None = None, *, prec: int = 2, **kwargs
) -> PrettyQuantityComponents:
    number_fmt = _NumberFmt()
    with Quantity.prefs(
        map_sf=Quantity.map_sf_to_greek,
        number_fmt=number_fmt,
        strip_radix=False,
        strip_zeros=False,
    ):
        quantiphy.render(value, unit or _SENTINEL_UNIT, prec=prec, **kwargs)
    whole: str = number_fmt.whole
    frac: str = number_fmt.frac
    units: str = number_fmt.units
    if not frac.startswith("."):
        frac = f".{frac}"
    if unit is None:
        units = units.removesuffix(_SENTINEL_UNIT)
    return PrettyQuantityComponents(whole, frac, units)


class _NumberFmt:
    whole: str
    frac: str
    units: str

    def __call__(self, whole: str, frac: str, units: str) -> str:
        self.whole = whole
        self.frac = frac
        self.units = units
        return ""


def _get_spacer(unit: str | None) -> str:
    if not unit:
        return ""
    if unit in Quantity.get_pref("tight_units"):
        return ""
    return Quantity.get_pref("spacer")
