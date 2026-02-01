from collections.abc import Callable
from typing import Any, TypedDict

import pydantic

type DecHook = Callable[[type, Any], Any]


class PydanticValidateOptions(TypedDict, total=False):
    strict: bool | None
    """Whether to enforce types strictly."""

    from_attributes: bool | None
    """Whether to extract data from object attributes."""

    context: Any | None
    """Additional context to pass to the validator."""

    by_alias: bool | None
    """Whether to use the field's alias when validating against the provided input data."""

    by_name: bool | None
    """Whether to use the field's name when validating against the provided input data."""


def dec_hook(
    typ: type, obj: Any, /, *, pydantic_options: PydanticValidateOptions | None = None
) -> Any:
    if issubclass(typ, pydantic.BaseModel):
        pydantic_options = pydantic_options or {}
        return typ.model_validate(obj, **pydantic_options)
    return typ(obj)
