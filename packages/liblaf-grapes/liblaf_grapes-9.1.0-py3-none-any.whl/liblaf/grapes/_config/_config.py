from liblaf.grapes import conf
from liblaf.grapes.conf import BaseConfig

from ._joblib import ConfigJoblib
from ._logging import ConfigLogging
from ._pretty import ConfigPretty
from ._traceback import ConfigTraceback
from ._warnings import ConfigWarnings


class Config(BaseConfig):
    joblib: ConfigJoblib = conf.group()
    logging: ConfigLogging = conf.group()
    pretty: ConfigPretty = conf.group()
    traceback: ConfigTraceback = conf.group()
    warnings: ConfigWarnings = conf.group()


config: Config = Config()
