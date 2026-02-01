import contextlib
from collections.abc import Generator, Mapping
from typing import Any, Self

import attrs
import tlz
import wadler_lindig as wl
from rich.repr import RichReprResult

from ._constants import METADATA_KEY
from ._entry import Entry
from ._field import Field


class BaseConfigMeta(type):
    def __new__[T: type](
        mcs: type[T],
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs: Any,
    ) -> T:
        cls: T = super().__new__(mcs, name, bases, namespace)
        if "__attrs_attrs__" in namespace:
            return cls
        kwargs.setdefault("frozen", True)
        kwargs.setdefault("init", False)
        kwargs.setdefault("repr", False)
        cls = attrs.define(cls, **kwargs)
        return cls


class BaseConfig(metaclass=BaseConfigMeta):
    def __init__(self, name: str = "") -> None:
        kwargs: dict[str, Any] = {}
        cls: type[BaseConfig] = type(self)
        cls = attrs.resolve_types(cls)
        prefix: str = f"{name}." if name else ""
        for field in attrs.fields(type(self)):
            field: attrs.Attribute
            entry: Entry | None = field.metadata.get(METADATA_KEY, None)
            if entry is None:
                continue
            kwargs[field.name] = entry.make(field, prefix)
        self.__attrs_init__(**kwargs)  # pyright: ignore[reportAttributeAccessIssue]

    def __repr__(self) -> str:
        from liblaf.grapes.wadler_lindig import pformat

        return pformat(self)

    def __pdoc__(self, **kwargs) -> wl.AbstractDoc | None:
        from liblaf.grapes.wadler_lindig import pdoc_rich_repr

        return pdoc_rich_repr(self, **kwargs)

    def __rich_repr__(self) -> RichReprResult:
        from liblaf.grapes.rich.repr import rich_repr_fieldz

        yield from rich_repr_fieldz(self)

    def get(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for f in attrs.fields(type(self)):
            f: attrs.Attribute
            value: Any = getattr(self, f.name)
            if isinstance(value, (BaseConfig, Field)):
                result[f.name] = value.get()
        return result

    def set(self, changes: Mapping[str, Any] = {}, /, **kwargs: Any) -> None:
        changes = tlz.merge(changes, kwargs)
        for key, value in changes.items():
            field: BaseConfig | Field = getattr(self, key)
            field.set(value)

    @contextlib.contextmanager
    def overrides(
        self, changes: Mapping[str, Any] = {}, /, **kwargs: Any
    ) -> Generator[Self]:
        changes = tlz.merge(changes, kwargs)
        with contextlib.ExitStack() as stack:
            for key, value in changes.items():
                field: BaseConfig | Field = getattr(self, key)
                stack.enter_context(field.overrides(value))
            yield self
