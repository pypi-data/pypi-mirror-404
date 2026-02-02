from .bases import Pys
from .utils.decorators import immutable
from .utils.generic import setimuattr
from .utils.string import normstr

from io import IOBase
from types import BuiltinMethodType
from typing import Iterable, Optional

@immutable
class PysBuffer(Pys):
    __slots__ = ()

class PysFileBuffer(PysBuffer):

    __slots__ = ('text', 'name')

    def __new__(
        cls,
        text: str | bytes | bytearray | Iterable | BuiltinMethodType | IOBase | 'PysFileBuffer',
        name: Optional[str | bytes] = None
    ) -> 'PysFileBuffer':

        if isinstance(text, PysFileBuffer):
            return text

        elif isinstance(text, IOBase):
            name = normstr(getattr(text, 'name', '<io>') if name is None else name)
            text = normstr(text)

        else:
            name = '<string>' if name is None else normstr(name)
            text = normstr(text)

        instance = super().__new__(cls)

        setimuattr(instance, 'text', text)
        setimuattr(instance, 'name', name)

        return instance

    def __repr__(self) -> str:
        return f'<FileBuffer from {self.name!r}>'