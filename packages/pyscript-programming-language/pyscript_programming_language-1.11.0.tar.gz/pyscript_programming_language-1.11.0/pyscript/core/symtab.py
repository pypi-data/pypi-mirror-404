from .bases import Pys
from .checks import is_equals
from .constants import TOKENS
from .cache import PysUndefined, undefined
from .mapping import BINARY_FUNCTIONS_MAP, EMPTY_MAP
from .utils.decorators import immutable
from .utils.generic import setimuattr, dcontains, dgetitem, dsetitem, ddelitem, dget, dkeys
from .utils.similarity import get_closest

from types import ModuleType
from typing import Any, Optional

@immutable
class PysSymbolTable(Pys):

    __slots__ = ('parent', 'symbols', 'globals')

    def __init__(self, parent: Optional['PysSymbolTable'] = None) -> None:
        setimuattr(self, 'parent', parent.parent if isinstance(parent, PysClassSymbolTable) else parent)
        setimuattr(self, 'symbols', {})
        setimuattr(self, 'globals', set())

    def get(self, name: str) -> Any | PysUndefined:
        if (value := dget(symbols := self.symbols, name, undefined)) is undefined:
            if parent := self.parent:
                return parent.get(name)

            builtins = dget(symbols, '__builtins__', undefined)
            if builtins is not undefined:
                return dget(
                    builtins if isinstance(builtins, dict) else getattr(builtins, '__dict__', EMPTY_MAP),
                    name,
                    undefined
                )

        return value

    def set(self, name: str, value: Any, *, operand: int = TOKENS['EQUAL']) -> bool:
        if is_equals(operand):
            if name in self.globals and (parent := self.parent):
                return parent.set(name, value, operand=operand)
            dsetitem(self.symbols, name, value)
            return True

        elif not dcontains(symbols := self.symbols, name):
            return (
                parent.set(name, value, operand=operand)
                if name in self.globals and (parent := self.parent) else
                False
            )

        dsetitem(symbols, name, BINARY_FUNCTIONS_MAP(operand)(dgetitem(symbols, name), value))
        return True

    def remove(self, name: str) -> bool:
        if not dcontains(symbols := self.symbols, name):
            return (
                parent.remove(name)
                if name in self.globals and (parent := self.parent) else 
                False
            )

        ddelitem(symbols, name)
        return True

class PysClassSymbolTable(PysSymbolTable):

    __slots__ = ()

    def __init__(self, parent: PysSymbolTable) -> None:
        super().__init__(parent)

def find_closest(symtab: PysSymbolTable, name: str) -> str | None:
    symbols = set(dkeys(symtab.symbols))
    update = symbols.update

    parent = symtab.parent
    while parent:
        update(dkeys(parent.symbols))
        parent = parent.parent

    builtins = symtab.get('__builtins__')
    if builtins is not undefined:
        update(dkeys(builtins if isinstance(builtins, dict) else getattr(builtins, '__dict__', EMPTY_MAP)))

    return get_closest(symbols, name)

def new_symbol_table(*, symbols=None, file=None, name=None, doc=None):
    symtab = PysSymbolTable()

    if symbols is None:
        module = ModuleType(name, doc)
        setimuattr(symtab, 'symbols', module.__dict__)
        symtab.set('__file__', file)
    else:
        module = None
        setimuattr(symtab, 'symbols', symbols)

    if symtab.get('__builtins__') is undefined:
        from .pysbuiltins import pys_builtins
        symtab.set('__builtins__', pys_builtins.__dict__)

    return symtab, module