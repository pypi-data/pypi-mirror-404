import functools
from typing import Unpack

import tlz

from liblaf.grapes._config import config

from ._typing import CustomCallable, WadlerLindigOptions
from .custom import chain_custom, pdoc_custom


def make_kwargs(**kwargs: Unpack[WadlerLindigOptions]) -> WadlerLindigOptions:
    kwargs = tlz.merge(config.pretty.get(), kwargs)  # pyright: ignore[reportAssignmentType]
    pdoc_custom_partial: CustomCallable = functools.partial(pdoc_custom, **kwargs)
    kwargs["custom"] = chain_custom(kwargs.get("custom"), pdoc_custom_partial)
    return kwargs
