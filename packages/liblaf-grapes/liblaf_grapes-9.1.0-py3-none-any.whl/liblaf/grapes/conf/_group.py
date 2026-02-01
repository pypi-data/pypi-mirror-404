from __future__ import annotations

from typing import Any

import attrs

from ._config import BaseConfig
from ._constants import METADATA_KEY
from ._entry import Entry


class GroupEntry[T: BaseConfig](Entry[T]):
    def make(self, field: attrs.Attribute, prefix: str) -> T:
        assert field.type is not None
        return field.type(f"{prefix}{field.name}")


def group() -> Any:
    return attrs.field(metadata={METADATA_KEY: GroupEntry()})
