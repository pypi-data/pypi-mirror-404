def first_not_none[T](*args: T | None) -> T:
    """Returns the first `not None` value in the `args`.

    Examples:
        >>> first_not_none(1, 2)
        1
        >>> first_not_none(None, 1)
        1

    References:
        1. [`more_itertools.first_true`](https://more-itertools.readthedocs.io/en/stable/api.html#more_itertools.first_true)
    """
    return next(arg for arg in args if arg is not None)
