import ast
import logging
import textwrap
import types
from collections.abc import Mapping, Sequence
from typing import Any, Unpack

import attrs
import wadler_lindig as wl
from asttokens import ASTTokens

from liblaf.grapes import magic
from liblaf.grapes.wadler_lindig import WadlerLindigOptions, pdoc

from ._source import Source

ICON: str = "🍦"
ICECREAM: int = 15  # between DEBUG (10) and INFO (20)


@attrs.define
class IceCreamDebugger:
    enabled: bool = True

    def __call__(self, *args, **kwargs) -> Any:
        if self.enabled:
            frame: types.FrameType | None = magic.get_frame(depth=2)
            logger: logging.Logger = self._get_logger(frame)
            logger.log(ICECREAM, self._format(args, kwargs, frame), stacklevel=2)
        match len(args):
            case 0:
                return None
            case 1:
                return args[0]
            case _:
                return args

    def _annotate_args(
        self, args: Sequence[Any], frame: types.FrameType | None = None
    ) -> list[tuple[str | None, Any]]:
        call: ast.Call | None = None
        if frame is not None:
            call = Source.executing(frame).node  # pyright: ignore[reportAssignmentType]
        if frame is None or call is None:
            return [(None, arg) for arg in args]
        source: Source = Source.for_frame(frame)
        asttokens: ASTTokens = source.asttokens()
        result: list[tuple[str | None, Any]] = []
        for value, node in zip(args, call.args, strict=True):
            text: str = asttokens.get_text(node)
            if _is_literal(text):
                result.append((None, value))
                continue
            if "\n" in text:
                text = " " * node.col_offset + text
                text = textwrap.dedent(text)
            text = text.strip()
            result.append((text, value))
        return result

    def _format(
        self,
        args: Sequence[Any],
        kwargs: Mapping[str, Any] = {},
        frame: types.FrameType | None = None,
    ) -> str:
        if len(args) == 0:
            if frame is not None:
                context: str = self._format_context(frame)
                return f"{ICON} {context}"
            return ICON
        pairs: list[tuple[str | None, Any]] = self._annotate_args(args, frame)
        doc: wl.AbstractDoc = self._pdoc_args(pairs, **kwargs)
        return wl.pformat(doc)

    def _format_context(self, frame: types.FrameType) -> str:
        filename: str = frame.f_code.co_filename
        filename = magic.abbr_path(filename)
        lineno: int = frame.f_lineno
        name: str = frame.f_code.co_name
        if name != "<module>":
            name += "()"
        return f"{filename}:{lineno} in {name}"

    def _get_logger(self, frame: types.FrameType | None) -> logging.Logger:
        _logging_hide = True
        name: str | None = None
        if frame is not None:
            name = frame.f_globals.get("__name__")
        if name is None:
            name = "icecream"
        return logging.getLogger(name)

    def _pdoc_args(
        self,
        args: Sequence[tuple[str | None, Any]],
        **kwargs: Unpack[WadlerLindigOptions],
    ) -> wl.AbstractDoc:
        docs: list[wl.AbstractDoc] = []
        for name, value in args:
            value_doc: wl.AbstractDoc = pdoc(value, **kwargs)
            arg_doc: wl.AbstractDoc
            if name is None:
                arg_doc = value_doc
            else:
                arg_doc = wl.TextDoc(name) + wl.TextDoc(": ") + value_doc
            docs.append(arg_doc)
        return wl.join(wl.BreakDoc(", "), docs)


ic = IceCreamDebugger()


def _is_literal(s: str) -> bool:
    try:
        ast.literal_eval(s)
    except Exception:  # noqa: BLE001
        return False
    else:
        return True
