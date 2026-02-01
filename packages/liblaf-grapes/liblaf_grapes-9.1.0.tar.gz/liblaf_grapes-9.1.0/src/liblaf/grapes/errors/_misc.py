from typing import Never

import attrs


@attrs.define
class TodoError(NotImplementedError):
    message: str = "not yet implemented"
    assignee: str | None = None

    def __str__(self) -> str:
        msg: str = "TODO"
        if self.assignee:
            msg += f"({self.assignee})"
        msg += f": {self.message}"
        return msg


@attrs.define
class UnreachableError(AssertionError):
    message: str | None = None

    def __str__(self) -> str:
        msg: str = "internal error: entered unreachable code"
        if self.message:
            msg += f": {self.message}"
        return msg


def todo(message: str = "not yet implemented", assignee: str | None = None) -> Never:
    raise TodoError(message=message, assignee=assignee)


def unreachable(message: str | None = None) -> Never:
    raise UnreachableError(message=message)
