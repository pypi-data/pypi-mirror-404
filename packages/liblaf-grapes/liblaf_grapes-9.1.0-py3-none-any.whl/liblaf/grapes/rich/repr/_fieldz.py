from typing import Any

import fieldz
from rich.repr import RichReprResult

from liblaf.grapes.sentinel import MISSING


def rich_repr_fieldz(obj: object) -> RichReprResult:
    for field in fieldz.fields(obj):
        if not field.repr:
            continue
        value: Any = getattr(obj, field.name, MISSING)
        # rich.repr uses `if default == value:` but does not protect against
        # exceptions. Some types (e.g. NumPy arrays) raise on equality/truth
        # checks (ambiguous truth value). Do the comparison here inside a
        # try/except so we can catch and handle those errors safely.
        try:
            if value == field.default:
                yield field.name, value, field.default
            else:
                yield field.name, value
        except Exception:  # noqa: BLE001
            yield field.name, value
