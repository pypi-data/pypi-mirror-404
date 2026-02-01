import contextlib
from collections.abc import Generator

import attrs


@attrs.define
class MissingOptionalDependencyError(ImportError):
    err: ImportError
    package: str | None = None
    extra: str | None = None

    def __str__(self) -> str:
        msg: str = str(self.err)
        if self.package and self.extra:
            msg += f"\nPlease install optional dependencies with '{self.package}[{self.extra}]'"
        return msg


@contextlib.contextmanager
def optional_deps(
    package: str | None = None, extra: str | None = None
) -> Generator[None]:
    try:
        yield
    except ImportError as err:
        raise MissingOptionalDependencyError(
            err, package=package, extra=extra
        ) from None
