from liblaf.grapes import conf
from liblaf.grapes.conf import BaseConfig, Field


class ConfigWarnings(BaseConfig):
    hide_stable_release: Field[bool] = conf.bool(
        default=True, env="WARNINGS_HIDE_STABLE_RELEASE"
    )
