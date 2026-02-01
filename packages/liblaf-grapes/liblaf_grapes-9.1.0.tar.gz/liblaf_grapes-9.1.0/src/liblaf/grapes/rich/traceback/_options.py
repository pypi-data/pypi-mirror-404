import attrs
from rich.syntax import Syntax, SyntaxTheme

from liblaf.grapes._config import config


@attrs.define
class RichTracebackOptions:
    indent_guide: bool = attrs.field(factory=config.traceback.indent_guide.get)
    locals_hide_dunder: bool = attrs.field(
        factory=config.traceback.locals_hide_dunder.get
    )
    locals_hide_sunder: bool = attrs.field(
        factory=config.traceback.locals_hide_sunder.get
    )
    locals_max_length: int = attrs.field(factory=config.traceback.locals_max_length.get)
    locals_max_string: int = attrs.field(factory=config.traceback.locals_max_string.get)
    show_locals: bool = attrs.field(factory=config.traceback.show_locals.get)
    theme: SyntaxTheme = attrs.field(
        factory=lambda: Syntax.get_theme(config.traceback.theme.get())
    )
