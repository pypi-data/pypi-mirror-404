import collections
import logging
from collections.abc import Mapping

from rich.panel import Panel
from rich.pretty import Pretty
from rich.tree import Tree


class LoggerTree(collections.UserDict[str, Tree]):
    def __init__(
        self, mapping: Mapping[str, Tree] | None = None, /, **kwargs: Tree
    ) -> None:
        super().__init__(mapping, **kwargs)
        for logger in logging.root.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                self.add_logger(logger)

    def __rich__(self) -> Tree:
        return self["root"]

    def add_logger(self, logger: logging.Logger) -> Tree:
        if (tree := self.get(logger.name)) is not None:
            return tree
        tree = self._rich_logger(logger)
        self.data[logger.name] = tree
        if (parent := logger.parent) is not None:
            parent_tree: Tree = self.add_logger(parent)
            parent_tree.add(tree)
        return tree

    def _rich_logger(self, logger: logging.Logger) -> Tree:
        tree = Tree(Pretty(logger))
        for filter_ in logger.filters:
            tree.add(Pretty(filter_))
        for handler in logger.handlers:
            handler_node: Tree = tree.add(Pretty(handler))
            for filter_ in handler.filters:
                handler_node.add(Pretty(filter_))
        if len(tree.children) > 0:
            tree = Tree(Panel(tree))
        return tree
