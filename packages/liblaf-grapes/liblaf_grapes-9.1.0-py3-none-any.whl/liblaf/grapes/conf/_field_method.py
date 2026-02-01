from __future__ import annotations

import functools
from collections.abc import Callable, Iterable
from typing import Any, TypedDict, Unpack, overload

import attrs
import environs

from liblaf.grapes.sentinel import MISSING, MissingType

from ._constants import METADATA_KEY
from ._entry import Entry
from ._field import Field


# I don't know why but mkdocstrings will fail if I use
# `environs.types.BaseMethodKwargs` directly, so I redefine it here as a
# workaround.
class BaseMethodKwargs(TypedDict, total=False):
    # kwargs shared by all parser methods
    validate: Callable[[Any], Any] | Iterable[Callable[[Any], Any]] | None


@attrs.define
class VarEntry[T](Entry[Field[T]]):
    getter: Callable[[str], T]
    default: T | MissingType = MISSING
    env: str | None = None
    factory: Callable[[], T] | None = None

    def make(self, field: attrs.Attribute, prefix: str) -> Field[T]:
        return Field(
            name=prefix + field.name,
            default=self.default,
            env=self.env,
            factory=self.factory,
            getter=self.getter,
        )


@attrs.define
class FieldMethod[T]:
    wrapped: environs.FieldMethod[T]

    @overload
    def __call__(
        self, *, default: T, env: str | None = None, **kwargs: Unpack[BaseMethodKwargs]
    ) -> Field[T]: ...
    @overload
    def __call__(
        self,
        *,
        default: None,
        env: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> Field[T | None]: ...
    @overload
    def __call__(
        self,
        *,
        factory: Callable[[], T],
        env: str | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> Field[T]: ...
    @overload
    def __call__(
        self,
        *,
        env: str | None = None,
        factory: None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> Field[T]: ...
    def __call__(
        self,
        *,
        default: T | MissingType | None = MISSING,
        env: str | None = None,
        factory: Callable[[], T] | None = None,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> Field[T] | Field[T | None]:
        return attrs.field(
            metadata={
                METADATA_KEY: VarEntry(
                    getter=functools.partial(self.wrapped, **kwargs),
                    default=default,
                    factory=factory,
                    env=env,
                )
            }
        )


@attrs.define
class ListFieldMethod[T]:
    wrapped: environs.ListFieldMethod

    def __call__(
        self,
        subcast: environs.Subcast[T] | None = None,
        *,
        delimiter: str | None = None,
        env: str | None = None,
        factory: Callable[[], list[T]] | None = list,
        **kwargs: Unpack[BaseMethodKwargs],
    ) -> Field[list[T]]:
        return attrs.field(
            metadata={
                METADATA_KEY: VarEntry(
                    getter=functools.partial(
                        self.wrapped, subcast=subcast, delimiter=delimiter, **kwargs
                    ),
                    factory=factory,
                    env=env,
                )
            }
        )
