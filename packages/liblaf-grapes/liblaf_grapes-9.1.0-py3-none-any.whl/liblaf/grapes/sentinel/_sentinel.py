import enum
from typing import Final, Literal


class _Missing(enum.Enum):
    MISSING = enum.auto()

    def __repr__(self) -> str:
        return f"<{self.name}>"


type MissingType = Literal[_Missing.MISSING]
MISSING: Final[MissingType] = _Missing.MISSING
