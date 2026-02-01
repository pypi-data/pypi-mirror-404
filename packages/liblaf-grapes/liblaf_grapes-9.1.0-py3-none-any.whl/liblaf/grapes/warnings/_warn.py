import warnings

from liblaf.grapes import magic
from liblaf.grapes.functools import wraps


@wraps(warnings.warn)
def warn(*args, **kwargs) -> None:
    _warnings_hide = True
    stacklevel: int = kwargs.get("stacklevel", 1)
    _, stacklevel = magic.get_frame_with_stacklevel(
        stacklevel, magic.hidden_from_warnings
    )
    kwargs["stacklevel"] = stacklevel
    return warnings.warn(*args, **kwargs)
