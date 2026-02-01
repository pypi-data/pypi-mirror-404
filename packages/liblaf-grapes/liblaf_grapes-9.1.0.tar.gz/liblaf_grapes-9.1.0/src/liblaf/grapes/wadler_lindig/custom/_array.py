import contextlib
import sys
from typing import Any, Unpack

import wadler_lindig as wl

from liblaf.grapes.wadler_lindig._typing import WadlerLindigOptions


def pdoc_array(
    obj: Any, **kwargs: Unpack[WadlerLindigOptions]
) -> wl.AbstractDoc | None:
    size: int | None = _array_size(obj)
    if size is None:
        return None
    if kwargs.get("short_arrays") is None:
        with contextlib.suppress(TypeError):
            kwargs["short_arrays"] = size > kwargs.get("short_arrays_threshold", 100)
    return wl.pdoc(obj, **kwargs)


def _array_size(obj: Any) -> int | None:
    for module, type_name in [
        ("jax", "Array"),
        ("mlx.core", "array"),
        ("numpy", "ndarray"),
    ]:
        if module not in sys.modules:
            continue
        typ: type = getattr(sys.modules[module], type_name)
        if isinstance(obj, typ):
            return obj.size
    for module, type_name in [("torch", "Tensor")]:
        if module not in sys.modules:
            continue
        typ: type = getattr(sys.modules[module], type_name)
        if isinstance(obj, typ):
            return obj.numel()
    return None
