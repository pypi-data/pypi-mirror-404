from typing import Any

import fieldz


def has_fields(obj: Any) -> bool:
    try:
        fieldz.get_adapter(obj)
    except TypeError:
        return False
    else:
        return True
