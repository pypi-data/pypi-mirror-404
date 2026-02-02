from .generic import dsetitem, ddelitem

from typing import Any

ditems = dict.items

def jsset(self: 'jsdict', key: Any, value: Any) -> None:
    if value is None:
        if key in self:
            ddelitem(self, key)
    else:
        dsetitem(self, key, value)

def jsdel(self: 'jsdict', key: Any) -> None:
    if key in self:
        ddelitem(self, key)

class jsdict(dict):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for key, value in ditems(self):
            if value is None:
                ddelitem(self, key)

    def __repr__(self) -> str:
        return f'jsdict({super().__repr__()})'

    def __or__(self, *args, **kwargs) -> 'jsdict':
        return jsdict(super().__or__(*args, **kwargs))

    __getitem__ = __getattribute__ = dict.get
    __setitem__ = __setattr__ = jsset
    __delitem__ = __delattr__ = jsdel