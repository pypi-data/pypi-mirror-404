import inspect
from typing import Any


def get_name(obj: Any) -> str:
    obj = inspect.unwrap(obj)
    return getattr(obj, "__qualname__", None) or getattr(obj, "__name__", "<unknown>")
