from .analyzer import PysAnalyzer
from .buffer import PysFileBuffer
from .cache import undefined, hook, PysUndefined
from .constants import DEFAULT, SILENT, RETURN_RESULT, NO_COLOR, DONT_SHOW_BANNER_ON_SHELL
from .context import PysContext
from .exceptions import PysTraceback, PysSignal
from .handlers import handle_call
from .interpreter import get_visitor
from .lexer import PysLexer
from .mapping import ACOLORS
from .parser import PysParser
from .position import PysPosition
from .pysbuiltins import require
from .results import PysRunTimeResult, PysExecuteResult
from .shell import PysCommandLineShell
from .symtab import PysSymbolTable, new_symbol_table
from .utils.decorators import _TYPECHECK, typechecked
from .utils.generic import get_frame, get_locals, import_readline
from .version import version

from types import ModuleType
from typing import Any, Literal, Optional

import sys

def _normalize_namespace(file, namespace):
    if namespace is None:
        symtab, _ = new_symbol_table(symbols=get_locals(3 if _TYPECHECK else 2))
    elif namespace is undefined:
        symtab, _ = new_symbol_table(file=file.name, name='__main__')
    elif isinstance(namespace, dict):
        symtab, _ = new_symbol_table(symbols=namespace)
    else:
        symtab = namespace
    return symtab

@typechecked
def pys_runner(
    file: PysFileBuffer,
    mode: Literal['exec', 'eval', 'single'],
    symbol_table: PysSymbolTable,
    flags: Optional[int] = None,
    parser_flags: int = DEFAULT,
    context_parent: Optional[PysContext] = None,
    context_parent_entry_position: Optional[PysPosition] = None
) -> PysExecuteResult:

    """
    The core of execution PyScript code.

    Parameters
    ----------
    - file : Buffer object from PysFileBuffer (`pyscript.core.buffer.PysFileBuffer`).

    - mode : Complication and execution mode. 'exec' to compile a whole code block, 'eval' to compile a single
             expression. 'single' is typically used for interactive shells (prints the result value, compile within a
             whole code block or expression).

    - symbol_table : Symbol table scope (`pyscript.core.symtab.PysSymbolTable`).

    - flags : A special flag.

    - parser_flags : A special parser flag.

    - context_parent : The parent context object, useful for linking tracebacks (context_parent_entry_position is
                       required).

    - context_parent_entry_position : The last parent position object, useful for specifying the row and column
                                      sections in the traceback (context_parent is required).
    """

    if (context_parent is None) != (context_parent_entry_position is None):
        raise TypeError("context_parent and context_parent_entry_position both must be filled in")

    context = PysContext(
        file=file,
        name='<program>',
        flags=flags,
        symbol_table=symbol_table,
        parent=context_parent,
        parent_entry_position=context_parent_entry_position
    )

    result = PysExecuteResult(context, parser_flags)
    runtime_runner_result = PysRunTimeResult()
    position = PysPosition(file, -1, -1)

    with runtime_runner_result(context, position):

        try:

            lexer = PysLexer(
                file=file,
                flags=context.flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            tokens, error = lexer.make_tokens()
            if error:
                return result.failure(error)

            parser = PysParser(
                tokens=tokens,
                flags=context.flags,
                parser_flags=parser_flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            node, error = parser.parse(parser.expression if mode == 'eval' else None)
            if error:
                return result.failure(error)

            analyzer = PysAnalyzer(
                node=node,
                flags=parser.flags,
                context_parent=context_parent,
                context_parent_entry_position=context_parent_entry_position
            )

            error = analyzer.analyze()
            if error:
                return result.failure(error)

        except RecursionError:
            return result.failure(
                PysTraceback(
                    RecursionError("maximum recursion depth exceeded during complication"),
                    context,
                    position
                )
            )

        result.parser_flags = parser.parser_flags
        runtime_result = get_visitor(node.__class__)(node, context)

        if runtime_result.error:
            return result.failure(runtime_result.error)

        if mode == 'single' and hook.display is not None:
            hook.display(runtime_result.value)
        return result.success(runtime_result.value)

    if runtime_runner_result.error:
        return result.failure(runtime_runner_result.error)

@typechecked
def pys_exec(
    source,
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT,
    parser_flags: int = DEFAULT
) -> None | PysExecuteResult:

    """
    Execute a PyScript code from source given.

    Parameters
    ----------
    - source : A valid PyScript source code.

    - globals : A namespace dictionary or symbol table that can be accessed.
                If it is None, it uses the current global namespace at the Python level.
                If it is undefined, it creates a new default PyScript namespace.

    - flags : A special flags.

    - parser_flags : A special parser flags.
    """

    file = PysFileBuffer(source)

    result = pys_runner(
        file=file,
        mode='exec',
        symbol_table=_normalize_namespace(file, globals),
        flags=flags,
        parser_flags=parser_flags
    )

    if flags & RETURN_RESULT:
        return result

    elif result.error and not (flags & SILENT):
        raise PysSignal(PysRunTimeResult().failure(result.error))

@typechecked
def pys_eval(
    source,
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT,
    parser_flags: int = DEFAULT
) -> Any | PysExecuteResult:

    """
    Evaluate a PyScript code from source given.

    Parameters
    ----------
    - source : A valid PyScript (Expression) source code.

    - globals : A namespace dictionary or symbol table that can be accessed.
                If it is None, it uses the current global namespace at the Python level.
                If it is undefined, it creates a new default PyScript namespace.

    - flags : A special flags.

    - parser_flags : A special parser flags.
    """

    file = PysFileBuffer(source)

    result = pys_runner(
        file=file,
        mode='eval',
        symbol_table=_normalize_namespace(file, globals),
        flags=flags,
        parser_flags=parser_flags
    )

    if flags & RETURN_RESULT:
        return result

    elif result.error and not (flags & SILENT):
        raise PysSignal(PysRunTimeResult().failure(result.error))

    return result.value

@typechecked
def pys_require(name, flags: int = DEFAULT) -> ModuleType | Any:

    """
    Import a PyScript module.

    Parameters
    ----------
    - name : A name or path of the module to be imported.

    - flags : A special flags.
    """

    file = PysFileBuffer('', get_frame(2 if _TYPECHECK else 1).f_code.co_filename)
    handle_call(require, PysContext(file=file, flags=flags), PysPosition(file, -1, -1))
    return require(name)

@typechecked
def pys_shell(
    globals: Optional[dict[str, Any] | PysSymbolTable | PysUndefined] = None,
    flags: int = DEFAULT,
    parser_flags: int = DEFAULT
) -> int | Any:

    """
    Start an interactive PyScript shell.

    Parameters
    ----------
    - globals : A namespace dictionary or symbol table that can be accessed.
                If it is None, it uses the current global namespace at the Python level.
                If it is undefined, it creates a new default PyScript namespace.

    - flags : A special flags.

    - parser_flags : A special parser flags.
    """

    if hook.running_shell:
        raise RuntimeError("another shell is still running")

    file = PysFileBuffer('', '<pyscript-shell>')
    symtab = _normalize_namespace(file, globals)
    shell = PysCommandLineShell()
    line = 0

    if flags & NO_COLOR:
        reset = ''
        bmagenta = ''
    else:
        reset = ACOLORS('reset')
        bmagenta = ACOLORS('bold-magenta')

    import_readline()

    if not (flags & DONT_SHOW_BANNER_ON_SHELL):
        print(f'PyScript {version}')
        print(f'Python {sys.version}')
        print('Type "help", "copyright", "credits" or "license" for more information.')
        print('Type "quit", "exit" or "/exit" to exit the shell.')

    try:
        hook.running_shell = True

        while True:

            try:
                shell.ps1 = f'{bmagenta}{hook.ps1}{reset}'
                shell.ps2 = f'{bmagenta}{hook.ps2}{reset}'

                text = shell.prompt()
                if text == 0:
                    return 0

                result = pys_runner(
                    file=PysFileBuffer(text, f'<pyscript-shell-{line}>'),
                    mode='single',
                    symbol_table=symtab,
                    flags=flags,
                    parser_flags=parser_flags
                )

                parser_flags = result.parser_flags
                code, exit = result.end_process()
                if exit:
                    return code
                elif code == 0:
                    line += 1

            except KeyboardInterrupt:
                shell.reset()
                print(f'\r{bmagenta}KeyboardInterrupt{reset}', file=sys.stderr)

            except EOFError:
                print()
                return 0

    finally:
        hook.running_shell = False