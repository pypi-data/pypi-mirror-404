import abc

import attrs


class Entry[T](abc.ABC):
    @abc.abstractmethod
    def make(self, field: attrs.Attribute, prefix: str) -> T:
        raise NotImplementedError
