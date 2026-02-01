from typing import Any

import attrs


@attrs.define
class MatchError(ValueError):
    value: Any
    typ: str | type = "match"

    def __str__(self) -> str:
        cls: str = self.typ if isinstance(self.typ, str) else self.typ.__qualname__
        return f"{self.value!r} is not a valid {cls}."
