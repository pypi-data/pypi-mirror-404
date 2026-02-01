from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, overload

from ._decode import DecHook, PydanticValidateOptions
from ._serde import json, toml, yaml

if TYPE_CHECKING:
    from _typeshed import StrPath

readers: dict[str, Callable] = {}
readers[".json"] = json.load
readers[".toml"] = toml.load
readers[".yaml"] = yaml.load
readers[".yml"] = yaml.load


@overload
def load(
    path: StrPath,
    /,
    *,
    dec_hook: DecHook | None = ...,
    force_ext: str | None = None,
    pydantic: PydanticValidateOptions | None = None,
    strict: bool = True,
) -> Any: ...
@overload
def load[T](
    path: StrPath,
    /,
    *,
    dec_hook: DecHook | None = ...,
    force_ext: str | None = None,
    pydantic: PydanticValidateOptions | None = None,
    strict: bool = True,
    type: type[T],
) -> T: ...
@overload
def load[T](
    path: StrPath,
    /,
    *,
    dec_hook: DecHook | None = ...,
    force_ext: str | None = None,
    pydantic: PydanticValidateOptions | None = None,
    strict: bool = True,
    type: Any,
) -> Any: ...
def load(path: StrPath, /, *, force_ext: str | None = None, **kwargs) -> Any:
    path = Path(path)
    ext: str = force_ext or path.suffix
    return readers[ext](path, **kwargs)
