import sys
import types
from typing import Any

_ARRAY_KINDS: list[tuple[str, str]] = [
    ("numpy", "ndarray"),
    ("jax", "Array"),
    ("torch", "Tensor"),
    ("cupy", "ndarray"),
]


def array_kind(obj: Any) -> str | None:
    # ref: <https://github.com/arogozhnikov/einops/blob/43a12ee010a844f3ad57bf404d27e4ee2d151131/einops/_backends.py>
    # ref: <https://github.com/patrick-kidger/wadler_lindig/blob/03ed125c04766008fb3f2eaa611fd3627b09de3d/wadler_lindig/_definitions.py#L254-L265>
    for module_name, type_name in _ARRAY_KINDS:
        module: types.ModuleType | None = sys.modules.get(module_name)
        if module is None:
            continue
        if isinstance(obj, getattr(module, type_name)):
            return module_name
    return None


def is_array(obj: Any) -> bool:
    return array_kind(obj) is not None
