from __future__ import annotations

import functools
import importlib.metadata
from collections.abc import Hashable
from importlib.metadata import Distribution, PackagePath
from pathlib import Path
from typing import TYPE_CHECKING

import attrs
import cachetools
import packaging.version
from packaging.version import InvalidVersion, Version

if TYPE_CHECKING:
    from _typeshed import StrPath


@attrs.define
class FilesIndex:
    _distributions: list[Distribution] = attrs.field(
        repr=False, init=False, factory=list
    )

    def add(self, distributuion: Distribution) -> None:
        self._distributions.append(distributuion)

    def has(self, file: StrPath) -> bool:
        file = Path(file).resolve()
        return self._has(str(file))

    _has_cache: cachetools.Cache[Hashable, bool] = attrs.field(
        repr=False, init=False, factory=lambda: cachetools.LRUCache(maxsize=1024)
    )

    @cachetools.cachedmethod(lambda self: self._has_cache)
    def _has(self, file: str) -> bool:
        if file in self._files:
            return True
        file: Path = Path(file)
        return any(file.is_relative_to(prefix) for prefix in self._pth)

    @functools.cached_property
    def _files(self) -> set[str]:
        files: set[str]
        files, _ = self._files_pth
        return files

    @functools.cached_property
    def _pth(self) -> set[str]:
        pth: set[str]
        _, pth = self._files_pth
        return pth

    @functools.cached_property
    def _files_pth(self) -> tuple[set[str], set[str]]:
        files: set[str] = set()
        pth: set[str] = set()
        for distribution in self._distributions:
            dist_files: list[PackagePath] | None = distribution.files
            if dist_files is None:
                continue
            for dist_file in dist_files:
                if dist_file.suffix == ".pth":
                    for line in dist_file.read_text().splitlines():
                        folder = Path(line)
                        if folder.is_dir():
                            pth.add(line)
                else:
                    files.add(str(dist_file.locate()))
        return files, pth


@attrs.define
class ReleaseTypeIndex:
    def is_dev(self, file: StrPath | None = None, name: str | None = None) -> bool:
        if name == "__main__":
            return True
        return file is not None and self._dev_index.has(file)

    def is_pre(
        self, file: StrPath | None = None, name: str | None = None
    ) -> bool | None:
        if name == "__main__":
            return True
        return file is not None and self._pre_index.has(file)

    @functools.cached_property
    def _dev_index(self) -> FilesIndex:
        dev_index: FilesIndex
        dev_index, _ = self._index
        return dev_index

    @functools.cached_property
    def _pre_index(self) -> FilesIndex:
        pre_index: FilesIndex
        _, pre_index = self._index
        return pre_index

    @functools.cached_property
    def _index(self) -> tuple[FilesIndex, FilesIndex]:
        dev_index: FilesIndex = FilesIndex()
        pre_index: FilesIndex = FilesIndex()
        for distribution in importlib.metadata.distributions():
            try:
                version: Version = packaging.version.parse(distribution.version)
            except InvalidVersion:
                continue
            if version.is_devrelease:
                dev_index.add(distribution)
            if version.is_prerelease:
                pre_index.add(distribution)
        return dev_index, pre_index


def is_dev_release(file: StrPath | None = None, name: str | None = None) -> bool:
    return _release_type_index.is_dev(file, name)


def is_pre_release(file: StrPath | None = None, name: str | None = None) -> bool | None:
    return _release_type_index.is_pre(file, name)


_release_type_index = ReleaseTypeIndex()
