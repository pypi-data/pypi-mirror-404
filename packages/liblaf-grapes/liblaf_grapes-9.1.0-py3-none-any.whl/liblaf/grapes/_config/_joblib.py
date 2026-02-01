from pathlib import Path

import platformdirs

from liblaf.grapes import conf
from liblaf.grapes.conf import BaseConfig, Field


def _default_location() -> Path:
    return platformdirs.user_cache_path(appname="joblib")


class ConfigJoblibMemory(BaseConfig):
    bytes_limit: Field[str] = conf.str(default="4G")
    location: Field[Path] = conf.path(factory=_default_location)


class ConfigJoblib(BaseConfig):
    memory: ConfigJoblibMemory = conf.group()
