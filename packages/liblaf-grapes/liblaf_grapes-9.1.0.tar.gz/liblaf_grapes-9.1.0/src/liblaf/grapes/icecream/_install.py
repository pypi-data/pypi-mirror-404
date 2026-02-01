import builtins

from ._icecream import ic


def install() -> None:
    from liblaf.grapes.logging import init

    init()
    builtins.ic = ic  # pyright: ignore[reportAttributeAccessIssue]
