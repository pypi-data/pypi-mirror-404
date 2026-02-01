from typing import Any, Unpack

import wadler_lindig as wl

from liblaf.grapes.functools import wraps

from ._options import WadlerLindigOptions, make_kwargs


@wraps(wl.pformat)
def pformat(obj: Any, **kwargs: Unpack[WadlerLindigOptions]) -> str:
    kwargs: WadlerLindigOptions = make_kwargs(**kwargs)
    return wl.pformat(obj, **kwargs)
