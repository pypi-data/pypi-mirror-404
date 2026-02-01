from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, overload

from ._encode import EncHook, PydanticDumpOptions
from ._serde import json, toml, yaml

if TYPE_CHECKING:
    from _typeshed import StrPath

writers: dict[str, Callable] = {}
writers[".json"] = json.save
writers[".toml"] = toml.save
writers[".yaml"] = yaml.save
writers[".yml"] = yaml.save


@overload
def save(  # pyright: ignore[reportInconsistentOverload]
    path: StrPath,
    obj: Any,
    /,
    *,
    enc_hook: EncHook | None = ...,
    force_ext: str | None = None,
    order: Literal["deterministic", "sorted"] | None = None,
    pydantic: PydanticDumpOptions | None = None,
) -> None: ...
def save(path: StrPath, obj: Any, /, force_ext: str | None = None, **kwargs) -> None:
    path = Path(path)
    ext: str = force_ext or path.suffix
    return writers[ext](path, obj, **kwargs)
