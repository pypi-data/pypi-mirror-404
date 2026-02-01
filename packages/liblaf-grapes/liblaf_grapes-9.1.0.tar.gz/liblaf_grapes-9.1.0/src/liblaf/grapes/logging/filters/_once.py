import logging
from collections.abc import Hashable

import attrs


@attrs.define
class OnceFilter:
    _history: set[Hashable] = attrs.field(repr=False, init=False, factory=set)

    def __call__(self, record: logging.LogRecord) -> bool:
        if not getattr(record, "once", False):
            return True
        record_hash: Hashable = self._hash_record(record)
        if record_hash in self._history:
            return False
        self._history.add(record_hash)
        return True

    def _hash_record(self, record: logging.LogRecord) -> Hashable:
        return hash((record.name, record.levelno, record.filename, record.lineno))
