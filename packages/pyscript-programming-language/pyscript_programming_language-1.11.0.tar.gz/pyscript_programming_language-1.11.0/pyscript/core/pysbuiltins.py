from .bases import Pys
from .buffer import PysFileBuffer
from .cache import loading_modules, modules, path, hook
from .checks import is_blacklist_python_builtins, is_private_attribute
from .constants import OTHER_PATH, NO_COLOR
from .exceptions import PysSignal
from .handlers import handle_call
from .mapping import ACOLORS, EMPTY_MAP
from .objects import PysFunction, PysPythonFunction, PysBuiltinFunction
from .results import PysRunTimeResult
from .shell import PysCommandLineShell
from .symtab import new_symbol_table
from .utils.generic import get_any, is_object_of as isobjectof, import_readline
from .utils.module import get_module_name_from_path, get_module_path, set_python_path, remove_python_path
from .utils.path import getcwd, normpath
from .utils.string import normstr

from math import inf, nan, isclose
from importlib import import_module
from inspect import signature
from os.path import dirname
from types import BuiltinFunctionType, BuiltinMethodType, FunctionType, MethodType, ModuleType
from typing import Any

import builtins
import sys

real_number = (int, float)
sequence = (list, tuple, set)
optional_mapping = (dict, type(None))
wrapper_function = (MethodType, PysPythonFunction)
python_function = (BuiltinFunctionType, BuiltinMethodType, FunctionType)

pyhelp = builtins.help
pyvars = builtins.vars
pydir = builtins.dir

def _supported_method(pyfunc, object, name, *args, **kwargs):
    if callable(method := getattr(object, name, None)):
        code = pyfunc.__code__
        handle_call(method, code.context, code.position)
        try:
            result = method(*args, **kwargs)
            if result is not NotImplemented:
                return True, result
        except NotImplementedError:
            pass
    return False, None

def _unpack_comprehension_function(pyfunc, function):
    code = pyfunc.__code__
    check = function
    final = function
    offset = 0

    if isinstance(function, wrapper_function):
        check = function.__func__
        offset += 1

    if isinstance(check, PysFunction):
        length = max(len(check.__code__.parameter_names) - offset, 0)
        if length == 0:
            def final(item):
                return function()
        elif length > 1:
            def final(item):
                return function(*item)

    elif isinstance(check, python_function):
        parameters = signature(check).parameters
        length = max(len(parameters) - offset, 0)
        if length == 0:
            def final(item):
                return function()
        elif length > 1 or any(p.kind == p.VAR_POSITIONAL for p in parameters.values()):
            def final(item):
                return function(*item)

    handle_call(function, code.context, code.position)
    return final

class _Printer(Pys):

    def __init__(self, name: str, text: str | Any) -> None:
        self.name = name
        self.text = text

    def __repr__(self) -> str:
        return f'Type {self.name}() to see the full information text.'

    def __call__(self) -> None:
        print(self.text)

class _Helper(_Printer):

    def __init__(self) -> None:
        super().__init__('help', None)

    def __repr__(self) -> str:
        return f'Type {self.name}() for interactive help, or {self.name}(object) for help about object.'

    def __call__(self, *args, **kwargs):
        if not (args or kwargs):
            print(
                "Welcome to the PyScript programming language! "
                "This is the help utility directly to the Python help.\n\n"
                "To get help on a specific object, type 'help(object)'.\n"
                "To get the list of builtin functions, types, exceptions, and other objects, type 'help(\"builtins\")'."
            )
        else:
            return pyhelp(*args, **kwargs)

try:
    with (
        open(normpath(OTHER_PATH, 'copyright', absolute=False)) as copyright, 
        open(normpath(OTHER_PATH, 'credits', absolute=False)) as credits, 
        open(normpath(OTHER_PATH, 'license', absolute=False)) as license
    ):
        copyright = _Printer('copyright', copyright.read())
        credits = _Printer('credits', credits.read())
        license = _Printer('license', license.read())
except:
    copyright = _Printer('copyright', '')
    credits = _Printer('credits', '')
    license = _Printer('license', '')

help = _Helper()

@PysBuiltinFunction
def require(pyfunc, name):

    """
    require(name: str | bytes) -> ModuleType | Any

    Import a PyScript module.

    name: A name or path of the module to be imported.
    """

    name, *other_components = normstr(name).split('>')
    code = pyfunc.__code__
    context = code.context
    filename = context.file.name

    for p in path:
        module_path = get_module_path(normpath(p, name, absolute=False))
        if module_path is not None:
            break
    else:
        module_path = get_module_path(normpath(dirname(filename) or getcwd(), name, absolute=False))
        if module_path == filename:
            module_path = None

    if module_path is None:
        if name == '_pyscript':
            from .. import core as module
        elif name == 'builtins':
            module = pys_builtins
        else:
            module_path = name

    if module_path is not None:
        module = modules.get(module_path, None)

        if module is None:

            if module_path in loading_modules:
                raise ImportError(
                    f"cannot import module name {name!r} from partially initialized module {filename!r}, "
                    "mostly during circular import"
                )

            try:
                loading_modules.add(module_path)

                try:
                    with open(module_path, 'r', encoding='utf-8') as file:
                        file = PysFileBuffer(file, module_path)
                except FileNotFoundError as e:
                    raise ModuleNotFoundError(f"No module named {name!r}") from e
                except BaseException as e:
                    raise ImportError(f"Cannot import module named {name!r}: {e}") from e

                symtab, module = new_symbol_table(
                    file=file.name,
                    name=get_module_name_from_path(name)
                )

                from .runner import pys_runner

                # minimize circular imports (python standard)
                modules[module_path] = module

                result = pys_runner(
                    file=file,
                    mode='exec',
                    symbol_table=symtab,
                    context_parent=context,
                    context_parent_entry_position=code.position
                )

                if result.error:
                    raise PysSignal(PysRunTimeResult().failure(result.error))

                # can also get circular imports
                # modules[module_path] = module

            finally:
                loading_modules.discard(module_path)

    for component in other_components:
        module = getattr(module, component)

    return module

@PysBuiltinFunction
def pyimport(pyfunc, name):

    """
    pyimport(name: str | bytes) -> ModuleType

    Import a Python module.

    name: A name of the module to be imported.
    """

    dirpath = dirname(pyfunc.__code__.context.file.name)
    try:
        set_python_path(dirpath)
        return import_module(normstr(name))
    finally:
        remove_python_path(dirpath)

@PysBuiltinFunction
def breakpoint(pyfunc):

    """
    Pauses program execution and enters shell debugging mode.
    """

    if hook.running_breakpoint:
        raise RuntimeError("another breakpoint is still running")

    from .runner import pys_runner

    code = pyfunc.__code__
    context = code.context
    position = code.position
    symtab = context.symbol_table

    if context.flags & NO_COLOR:
        reset = ''
        bmagenta = ''
    else:
        reset = ACOLORS('reset')
        bmagenta = ACOLORS('bold-magenta')

    shell = PysCommandLineShell(f'{bmagenta}(Pdb) {reset}', f'{bmagenta}...   {reset}')
    scopes = []

    def show_line():
        print(f"> {context.file.name}({position.start_line}){context.name}")

    import_readline()
    show_line()

    try:
        hook.running_breakpoint = True

        while True:

            try:
                text = shell.prompt()

                split = ['exit'] if text == 0 else text.split()
                if split:
                    command, *args = split
                else:
                    command, args = '', []

                if command in ('c', 'continue'):
                    return

                elif command in ('h', 'help'):
                    print(
                        "\n"
                        "Documented commands:\n"
                        "====================\n"
                        "(c)ontinue          : Exit the debugger and continue the program.\n"
                        "(d)own [count]      : Decrease the scope level (default one) to the older frame.\n"
                        "(h)elp              : Show this help display.\n"
                        "(l)ine              : Show the position where breakpoint() was called.\n"
                        "(q)uit / exit [code]: Exit the interpreter by throwing SystemExit.\n"
                        "(u)p [count]        : Increase the scope level (default one) to the older frame.\n"
                    )

                elif command in ('l', 'line'):
                    show_line()

                elif command in ('q', 'quit', 'exit'):
                    code = get_any(args, 0, '0')
                    raise SystemExit(int(code) if code.isdigit() else code)

                elif command in ('u', 'up'):
                    count = get_any(args, 0, '')
                    for _ in range(int(count) if count.isdigit() else 1):
                        if scopes:
                            symtab = scopes.pop()
                        else:
                            print('*** Oldest frame')
                            break

                elif command in ('d', 'down'):
                    count = get_any(args, 0, '')
                    parent = symtab.parent
                    for _ in range(int(count) if count.isdigit() else 1):
                        if parent is None:
                            print('*** Newest frame')
                            break
                        else:
                            scopes.append(symtab)
                            symtab = parent

                else:
                    exit_code, exit = pys_runner(
                        file=PysFileBuffer(text, '<breakpoint>'),
                        mode='single',
                        symbol_table=symtab
                    ).end_process()

                    if exit:
                        raise SystemExit(exit_code)

            except KeyboardInterrupt:
                shell.reset()
                print('\r--KeyboardInterrupt--', file=sys.stderr)

            except EOFError as e:
                raise SystemExit from e

    finally:
        hook.running_breakpoint = False

@PysBuiltinFunction
def globals(pyfunc):

    """
    Returns a dictionary containing the current global scope of variables.

    NOTE: Modifying the contents of a dictionary within a program or module scope will affect that scope. However,
    this does not apply to local scopes (creating a new dictionary).
    """

    original = pyfunc.__code__.context.symbol_table
    symbol_table = original.parent

    if symbol_table:
        result = {}

        while symbol_table:
            result |= symbol_table.symbols
            symbol_table = symbol_table.parent

        return result

    return original.symbols

@PysBuiltinFunction
def locals(pyfunc):

    """
    Returns a dictionary containing the current local scope of variables.

    NOTE: Changing the contents of the dictionary will affect the scope.
    """

    return pyfunc.__code__.context.symbol_table.symbols

@PysBuiltinFunction
def vars(pyfunc, *args):

    """
    Without arguments, equivalent to locals(). With an argument, equivalent to object.__dict__.
    """

    return pyvars(*args) if args else pyfunc.__code__.context.symbol_table.symbols

@PysBuiltinFunction
def dir(pyfunc, *args):

    """
    If called without an argument, return the names in the current scope. Else, return an alphabetized list of names
    comprising (some of) the attributes of the given object, and of attributes reachable from it. If the object supplies
    a method named __dir__, it will be used; otherwise the default dir() logic is used and returns:
        for a module object: the module's attributes.
        for a class object: its attributes, and recursively the attributes of its bases.
        for any other object: its attributes, its class's attributes, and recursively the attributes of its class's base
            classes.
    """

    return pydir(*args) if args else list(pyfunc.__code__.context.symbol_table.symbols.keys())

@PysBuiltinFunction
def exec(pyfunc, source, globals=None):

    """
    exec(source: str | bytes, globals: Optional[dict]) -> None

    Executes PyScript code statements from the given source.

    source: A string containing the code statements to be executed.
    globals: The namespace scope for the code that can be accessed, modified, and deleted. If not provided, the current
             local scope will be used.
    """

    if not isinstance(globals, optional_mapping):
        raise TypeError("exec(): globals must be dict")

    file = PysFileBuffer(source, '<exec>')
    code = pyfunc.__code__

    if globals is None:
        symtab = code.context.symbol_table
    else:
        symtab, _ = new_symbol_table(symbols=globals)

    from .runner import pys_runner

    result = pys_runner(
        file=file,
        mode='exec',
        symbol_table=symtab,
        context_parent=code.context,
        context_parent_entry_position=code.position
    )

    if result.error:
        raise PysSignal(PysRunTimeResult().failure(result.error))

@PysBuiltinFunction
def eval(pyfunc, source, globals=None):

    """
    eval(source: str | bytes, globals: Optional[dict]) -> None

    Executes a PyScript code expression from the given source.

    source: A string containing the code statements to be executed.
    globals: The namespace scope for the code that can be accessed, modified, and deleted. If not provided, the current
             local scope will be used.
    """

    if not isinstance(globals, optional_mapping):
        raise TypeError("eval(): globals must be dict")

    file = PysFileBuffer(source, '<eval>')
    code = pyfunc.__code__

    if globals is None:
        symtab = code.context.symbol_table
    else:
        symtab, _ = new_symbol_table(symbols=globals)

    from .runner import pys_runner

    result = pys_runner(
        file=file,
        mode='eval',
        symbol_table=symtab,
        context_parent=code.context,
        context_parent_entry_position=code.position
    )

    if result.error:
        raise PysSignal(PysRunTimeResult().failure(result.error))

    return result.value

@PysBuiltinFunction
def ce(pyfunc, a, b, *, rel_tol=1e-9, abs_tol=0):

    """
    ce(a: Any, b: Any, *, rel_tol: Any = 1e-9, abs_tol: Any = 0) -> Any
    a ~= b

    Comparing two objects a and b to close equal.

    a, b: Two objects to be compared. If both are integer or float, it will call `math.isclose()` function. Otherwise,
          it will attempt to call the __ce__ method (if both fail, it calls the negated __nce__ method) of one of the
          two objects. If all else fails, it will throw a TypeError.
    rel_tol: maximum difference for being considered "close", relative to the magnitude of the input values.
    abs_tol: maximum difference for being considered "close", regardless of the magnitude of the input values.
    """

    if isinstance(a, real_number) and isinstance(b, real_number):
        return isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

    success, result = _supported_method(pyfunc, a, '__ce__', b, rel_tol=rel_tol, abs_tol=abs_tol)
    if not success:
        success, result = _supported_method(pyfunc, b, '__ce__', a, rel_tol=rel_tol, abs_tol=abs_tol)
        if not success:
            success, result = _supported_method(pyfunc, a, '__nce__', b, rel_tol=rel_tol, abs_tol=abs_tol)
            if not success:
                success, result = _supported_method(pyfunc, b, '__nce__', a, rel_tol=rel_tol, abs_tol=abs_tol)
                if not success:
                    raise TypeError(
                        f"unsupported operand type(s) for ~= or ce(): {type(a).__name__!r} and {type(b).__name__!r}"
                    )
            result = not result

    return result

@PysBuiltinFunction
def nce(pyfunc, a, b, *, rel_tol=1e-9, abs_tol=0):

    """
    nce(a: Any, b: Any, *, rel_tol: Any = 1e-9, abs_tol: Any = 0) -> Any
    a ~! b

    Comparing two objects a and b to not close equal.

    a, b: Two objects to be compared. If both are integer or float, it calls the `not math.isclose()` function.
          Otherwise, it attempts to call the __nce__ method (if both fail, it calls the negated __ce__ method) of one of
          the two objects. If both fail, it throws a TypeError.
    rel_tol: maximum difference for being considered "close", relative to the magnitude of the input values.
    abs_tol: maximum difference for being considered "close", regardless of the magnitude of the input values.
    """

    if isinstance(a, real_number) and isinstance(b, real_number):
        return not isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)

    success, result = _supported_method(pyfunc, a, '__nce__', b, rel_tol=rel_tol, abs_tol=abs_tol)
    if not success:
        success, result = _supported_method(pyfunc, b, '__nce__', a, rel_tol=rel_tol, abs_tol=abs_tol)
        if not success:
            success, result = _supported_method(pyfunc, a, '__ce__', b, rel_tol=rel_tol, abs_tol=abs_tol)
            if not success:
                success, result = _supported_method(pyfunc, b, '__ce__', a, rel_tol=rel_tol, abs_tol=abs_tol)
                if not success:
                    raise TypeError(
                        f"unsupported operand type(s) for ~! or nce(): {type(a).__name__!r} and {type(b).__name__!r}"
                    )
            result = not result

    return result

@PysBuiltinFunction
def increment(pyfunc, object):

    """
    increment(object: Any) -> Any
    object++
    ++object

    Increase to the object. If the given type is integer or float, it will increment by 1, if the given type is unpack
    assignment (list, tuple, or set), it will increment each element. Otherwise, it will attempt to call the
    __increment__ method, which if unsuccessful will throw a TypeError.
    """

    if isinstance(object, real_number):
        return object + 1
    elif isinstance(object, sequence):
        return tuple(pyincrement(pyfunc, obj) for obj in object)

    success, result = _supported_method(pyfunc, object, '__increment__')
    if not success:
        raise TypeError(f"bad operand type for unary ++ or increment(): {type(object).__name__!r}")

    return result

@PysBuiltinFunction
def decrement(pyfunc, object):

    """
    decrement(object: Any) -> Any
    object--
    --object

    Decrease to the object. If the given type is integer or float, it will decrement by 1, if the given type is unpack
    assignment (list, tuple, or set), it will decrement each element. Otherwise, it will attempt to
    call the __decrement__ method, which if unsuccessful will throw a TypeError.
    """

    if isinstance(object, real_number):
        return object - 1
    elif isinstance(object, sequence):
        return tuple(pydecrement(pyfunc, obj) for obj in object)

    success, result = _supported_method(pyfunc, object, '__decrement__')
    if not success:
        raise TypeError(f"bad operand type for unary -- or decrement(): {type(object).__name__!r}")

    return result

pyincrement = increment.__func__
pydecrement = decrement.__func__

@PysBuiltinFunction
def unpack(pyfunc, function, args=(), kwargs=EMPTY_MAP):

    """
    unpack(function: Callable, args: Iterable = (), kwargs: Mapping = {}) -> Any

    A replacement function for Python's argument unpack on function calls, which uses the syntax
    `function(*args, **kwargs)`.

    function: the function to be called.
    args: regular arguments (iterable object).
    kwargs: keyword arguments (mapping object).
    """

    code = pyfunc.__code__
    handle_call(function, code.context, code.position)
    return function(*args, **kwargs)

@PysBuiltinFunction
def comprehension(pyfunc, init, wrap, condition=None):

    """
    comprehension(
        init: Iterable[Any],
        wrap: Callable[[Any], Any],
        condition: Optional[Callable[[Any], bool]] = None
    ) -> Iterable[Any]

    A replacement function for Python's list comprehension, which uses the syntax
    `[wrap for item in init if condition]`.

    init: The iterable object to be iterated.
    wrap: The function that wraps the results of the iteration (Unpack per-iteration if parameter is more than 1).
    condition: The function that filters the iteration (Unpack per-iteration if parameter is more than 1).
    """

    if not callable(wrap):
        raise TypeError("comprehension(): wrap must be callable")
    if not (condition is None or callable(condition)):
        raise TypeError("comprehension(): condition must be callable")

    return map(
        _unpack_comprehension_function(pyfunc, wrap),
        init if condition is None else filter(_unpack_comprehension_function(pyfunc, condition), init)
    )

pys_builtins = ModuleType(
    'built-in',
    "Built-in functions, types, exceptions, and other objects.\n\n"
    "This module provides direct access to all 'built-in' identifiers of PyScript and Python."
)

pys_builtins.__dict__.update(
    (name, getattr(builtins, name))
    for name in pydir(builtins)
    if not (is_private_attribute(name) or is_blacklist_python_builtins(name))
)

pys_builtins.__file__ = __file__
pys_builtins.true = True
pys_builtins.false = False
pys_builtins.none = None
pys_builtins.ellipsis = Ellipsis
pys_builtins.inf = pys_builtins.infinity = pys_builtins.Infinity = inf
pys_builtins.nan = pys_builtins.notanumber = pys_builtins.NaN = pys_builtins.NotANumber = nan
pys_builtins.copyright = copyright
pys_builtins.credits = credits
pys_builtins.license = license
pys_builtins.help = help
pys_builtins.require = require
pys_builtins.pyimport = pyimport
pys_builtins.breakpoint = breakpoint
pys_builtins.globals = globals
pys_builtins.locals = locals
pys_builtins.vars = vars
pys_builtins.dir = dir
pys_builtins.exec = exec
pys_builtins.eval = eval
pys_builtins.ce = ce
pys_builtins.nce = nce
pys_builtins.increment = increment
pys_builtins.decrement = decrement
pys_builtins.unpack = unpack
pys_builtins.comprehension = comprehension
pys_builtins.isobjectof = isobjectof