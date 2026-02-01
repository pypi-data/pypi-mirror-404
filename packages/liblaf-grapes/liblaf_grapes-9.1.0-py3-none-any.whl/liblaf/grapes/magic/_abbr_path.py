from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _typeshed import StrPath


def abbr_path(path: StrPath, truncation_symbol: str = "󰇘/") -> str:
    path = Path(path)
    for prefix in sys.path:
        if path.is_relative_to(prefix):
            return f"{truncation_symbol}{path.relative_to(prefix)}"
    return str(path)
