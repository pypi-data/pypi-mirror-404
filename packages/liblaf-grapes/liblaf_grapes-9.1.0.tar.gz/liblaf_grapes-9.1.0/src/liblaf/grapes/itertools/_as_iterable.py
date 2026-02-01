import types
from collections.abc import Iterable
from typing import Any

type ClassInfo = type | types.UnionType | tuple[ClassInfo, ...]


def as_iterable(obj: Any, base_type: ClassInfo | None = (str, bytes)) -> Iterable:
    """.

    Examples:
        If `obj` is iterable, return an iterator over its items:

        >>> obj = (1, 2, 3)
        >>> as_iterable(obj)
        (1, 2, 3)

        If `obj` is not iterable, return a one-item iterable containing `obj`:

        >>> obj = 1
        >>> as_iterable(obj)
        (1,)

        If `obj` is `None`, return an empty iterable:

        >>> obj = None
        >>> as_iterable(None)
        ()

        By default, binary and text strings are not considered iterable:

        >>> obj = "foo"
        >>> as_iterable(obj)
        ('foo',)

        If `base_type` is set, objects for which `isinstance(obj, base_type)` returns ``True`` won't be considered iterable.

        >>> obj = {"a": 1}
        >>> as_iterable(obj)
        {'a': 1}
        >>> as_iterable(obj, base_type=dict)  # Treat dicts as a unit
        ({'a': 1},)

        Set `base_type` to `None` to avoid any special handling and treat objects Python considers iterable as iterable:

        >>> obj = "foo"
        >>> as_iterable(obj, base_type=None)
        'foo'

    References:
        1. [`more_itertools.always_iterable`](https://more-itertools.readthedocs.io/en/stable/api.html#more_itertools.always_iterable)
    """
    if obj is None:
        return ()
    if base_type is not None and isinstance(obj, base_type):
        return (obj,)
    if isinstance(obj, Iterable):
        return obj
    return (obj,)
