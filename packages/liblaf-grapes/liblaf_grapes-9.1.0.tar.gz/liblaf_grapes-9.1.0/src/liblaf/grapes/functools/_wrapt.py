from typing import Any, overload

from liblaf.grapes.sentinel import MISSING


def wrapt_setattr(obj: Any, name: str, value: Any, /) -> None:
    name = f"_self_{name}"
    setattr(obj, name, value)


@overload
def wrapt_getattr(obj: Any, name: str, /) -> Any: ...
@overload
def wrapt_getattr[T](obj: Any, name: str, default: T, /) -> Any | T: ...
def wrapt_getattr(obj: Any, name: str, default: Any = MISSING, /) -> Any:
    name = f"_self_{name}"
    try:
        return getattr(obj, name)
    except AttributeError:
        parent: Any = getattr(obj, "_self_parent", None)
        if parent is None:
            if default is MISSING:
                raise
            return default
        if hasattr(parent, name):
            return getattr(parent, name)
        if default is MISSING:
            raise
        return default
