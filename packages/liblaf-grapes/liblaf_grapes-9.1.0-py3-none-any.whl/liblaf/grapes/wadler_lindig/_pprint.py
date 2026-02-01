from typing import Any, Unpack

import wadler_lindig as wl

from liblaf.grapes.functools import wraps

from ._options import WadlerLindigOptions, make_kwargs


@wraps(wl.pprint)
def pprint(obj: Any, **kwargs: Unpack[WadlerLindigOptions]) -> None:
    kwargs: WadlerLindigOptions = make_kwargs(**kwargs)
    return wl.pprint(obj, **kwargs)
