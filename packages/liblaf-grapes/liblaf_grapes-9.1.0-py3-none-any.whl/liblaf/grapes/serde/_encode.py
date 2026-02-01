from __future__ import annotations

import functools
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, TypedDict

import pydantic

if TYPE_CHECKING:
    from pydantic.main import IncEx


type EncHook = Callable[[Any], Any]


class PydanticDumpOptions(TypedDict, total=False):
    mode: Literal["json", "python"]
    include: IncEx | None
    exclude: IncEx | None
    context: Any | None
    by_alias: bool | None
    exclude_unset: bool
    exclude_defaults: bool
    exclude_none: bool
    round_trip: bool
    warnings: bool | Literal["none", "warn", "error"]
    fallback: Callable[[Any], Any] | None
    serialize_as_any: bool


@functools.singledispatch
def enc_hook(obj: Any, /, **_kwargs) -> Any:
    msg: str = f"Objects of type {type(obj)} are not supported"
    raise NotImplementedError(msg)


@enc_hook.register(pydantic.BaseModel)
def _(
    obj: pydantic.BaseModel,
    /,
    *,
    pydantic_options: PydanticDumpOptions | None = None,
    **_kwargs,
) -> Any:
    pydantic_options = pydantic_options or {}
    pydantic_options.setdefault("mode", "json")
    return obj.model_dump(**pydantic_options)


@enc_hook.register(os.PathLike)
def _(obj: os.PathLike, /, **_kwargs) -> str:
    return str(obj)
