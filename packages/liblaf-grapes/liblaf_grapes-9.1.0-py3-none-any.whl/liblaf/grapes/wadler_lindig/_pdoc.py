from typing import Any, Unpack

import wadler_lindig as wl

from liblaf.grapes.functools import wraps

from ._options import WadlerLindigOptions, make_kwargs


@wraps(wl.pdoc)
def pdoc(obj: Any, **kwargs: Unpack[WadlerLindigOptions]) -> wl.AbstractDoc:
    kwargs: WadlerLindigOptions = make_kwargs(**kwargs)
    return wl.pdoc(obj, **kwargs)
