def has_ansi(s: str, /) -> bool:
    r""".

    Examples:
        >>> has_ansi("\x1b[31m red text \x1b[0m")
        True
        >>> has_ansi("plain text")
        False
    """
    return "\x1b" in s
