from __future__ import annotations

from collections.abc import Container, Iterable
from typing import TYPE_CHECKING

from liblaf.grapes import warnings

if TYPE_CHECKING:
    from _typeshed import SupportsGetItem


_DEPRECATED_MESSAGE = "'{deprecated_key}' is deprecated. Please use '{key}' instead."


def contains[T](
    obj: Container[T],
    key: T,
    deprecated_keys: Iterable[T] = (),
    *,
    msg: str = _DEPRECATED_MESSAGE,
) -> bool:
    _warnings_hide = True
    if key in obj:
        return True
    for deprecated_key in deprecated_keys:
        if deprecated_key in obj:
            warnings.warn(
                msg.format_map({"deprecated_key": deprecated_key, "key": key}),
                DeprecationWarning,
            )
            return True
    return False


def getitem[KT, VT](
    obj: SupportsGetItem[KT, VT],
    key: KT,
    deprecated_keys: Iterable[KT] = (),
    *,
    msg: str = _DEPRECATED_MESSAGE,
) -> VT:
    _warnings_hide = True
    try:
        return obj[key]
    except KeyError:
        pass
    for deprecated_key in deprecated_keys:
        try:
            value: VT = obj[deprecated_key]
        except KeyError:
            continue
        warnings.warn(
            msg.format_map({"deprecated_key": deprecated_key, "key": key}),
            DeprecationWarning,
        )
        return value
    raise KeyError(key)
