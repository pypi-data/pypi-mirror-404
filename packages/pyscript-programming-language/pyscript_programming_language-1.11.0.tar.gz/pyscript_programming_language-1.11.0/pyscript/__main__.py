from .core.buffer import PysFileBuffer
from .core.cache import undefined, hook
from .core.constants import DEFAULT, DEBUG, DONT_SHOW_BANNER_ON_SHELL, NO_COLOR
from .core.highlight import (
    HLFMT_HTML, HLFMT_ANSI, HLFMT_BBCODE, pys_highlight, PygmentsPyScriptStyle, PygmentsPyScriptLexer
)
from .core.runner import _normalize_namespace, pys_runner, pys_shell
from .core.utils.module import get_module_name_from_path, remove_python_path
from .core.utils.path import normpath, getcwd
from .core.version import __version__

try:
    from pygments import highlight
    from pygments.formatters import (
        BBCodeFormatter,
        HtmlFormatter,
        LatexFormatter,
        TerminalFormatter, TerminalTrueColorFormatter, Terminal256Formatter
    )

    FORMAT_PYGMENTS_MAP = {
        'pm-bbcode': BBCodeFormatter,
        'pm-html': HtmlFormatter,
        'pm-latex': LatexFormatter,
        'pm-terminal': TerminalFormatter,
        'pm-true-terminal': TerminalTrueColorFormatter,
        'pm-256-terminal': Terminal256Formatter
    }

    PYGMENTS = True
except ImportError:
    PYGMENTS = False

from argparse import OPTIONAL, REMAINDER, ArgumentParser
from os import environ

import sys

FORMAT_HIGHLIGHT_MAP = {
    'html': HLFMT_HTML,
    'ansi': HLFMT_ANSI,
    'bbcode': HLFMT_BBCODE
}

parser = ArgumentParser(
    prog=f'{get_module_name_from_path(sys.executable)} -m pyscript',
    description=f'PyScript Launcher for Python Version {".".join(map(str, sys.version_info))}'
)

parser.add_argument(
    '-v', '--version',
    action='version',
    version=f"PyScript {__version__}",
)

parser.add_argument(
    '-c', '--command',
    type=str,
    default=None,
    help="Execute program from a string argument",
)

parser.add_argument(
    '-d', '-O', '--debug',
    action='store_true',
    help="Set a debug flag, this will ignore assert statement. Check the flag is active with the __debug__ keyword"
)

parser.add_argument(
    '-i', '--inspect',
    action='store_true',
    help="Inspect interactively after running a 'file'",
)

parser.add_argument(
    '-l', '--highlight',
    choices=tuple(FORMAT_HIGHLIGHT_MAP.keys()) + tuple(FORMAT_PYGMENTS_MAP.keys() if PYGMENTS else ()),
    default=None,
    help="Generate highlight code from a 'file'"
)

parser.add_argument(
    '-n', '--no-color',
    action='store_true',
    help="Suppress colored output"
)

parser.add_argument(
    '-r', '--py-recursion',
    type=int,
    default=None,
    help="Set a Python recursion limit"
)

parser.add_argument(
    '-P',
    action='store_true',
    help="Don't prepend a potentially unsafe path to sys.path (python sys.path)"
)

parser.add_argument(
    '-q',
    action='store_true',
    help="Don't print version and copyright messages on interactive startup"
)

parser.add_argument(
    'file',
    type=str,
    nargs=OPTIONAL,
    default=None,
    help="File path to be executed"
)

parser.add_argument(
    'argv',
    nargs=REMAINDER,
    help="Remaining arguments stored in hook.argv (sys.argv or sys.hook.argv)"
)

def argument_error(argument, message):
    parser.print_usage(sys.stderr)
    parser.exit(2, f"{parser.prog}: error: argument {argument}: {message}\n")

args = parser.parse_args()

if args.highlight and args.file is None:
    argument_error("-l/--highlight", "argument 'file' is required")

if args.py_recursion is not None:
    try:
        sys.setrecursionlimit(args.py_recursion)
    except BaseException as e:
        argument_error("-r/--py-recursion", e)

code = 0
flags = DEFAULT

if args.debug:
    flags |= DEBUG
if args.no_color or environ.get('NO_COLOR') is not None:
    flags |= NO_COLOR
if args.P:
    for cwd in {'', '.', getcwd()}:
        remove_python_path(cwd)
if args.q:
    flags |= DONT_SHOW_BANNER_ON_SHELL

hook.argv.extend(args.argv)

if args.file is not None:
    hook.argv[0] = args.file
    path = normpath(args.file)

    try:
        with open(path, 'r', encoding='utf-8') as file:
            file = PysFileBuffer(file, path)
    except FileNotFoundError:
        parser.error(f"can't open file {path!r}: No such file or directory")
    except PermissionError:
        parser.error(f"can't open file {path!r}: Permission denied")
    except IsADirectoryError:
        parser.error(f"can't open file {path!r}: Path is not a file")
    except NotADirectoryError:
        parser.error(f"can't open file {path!r}: Attempting to access directory from file")
    except (OSError, IOError):
        parser.error(f"can't open file {path!r}: Attempting to access a system directory or file")
    except UnicodeDecodeError:
        parser.error(f"can't read file {path!r}: Bad file")
    except BaseException as e:
        parser.error(f"file {path!r}: Unexpected error: {e}")

    if args.highlight:
        try:
            if args.highlight in FORMAT_HIGHLIGHT_MAP:
                print(
                    pys_highlight(
                        source=file,
                        format=FORMAT_HIGHLIGHT_MAP[args.highlight]
                    )
                )
            else:
                print(
                    highlight(
                        code=file.text,
                        lexer=PygmentsPyScriptLexer(),
                        formatter=FORMAT_PYGMENTS_MAP[args.highlight](style=PygmentsPyScriptStyle, full=True)
                    )
                )
        except BaseException as e:
            parser.error(f"file {path!r}: Highlight error: {e}")

    else:
        result = pys_runner(
            file=file,
            mode='exec',
            symbol_table=_normalize_namespace(file, undefined),
            flags=flags
        )

        code, _ = result.end_process()

        if args.inspect and not (sys.stdout.closed or sys.stderr.closed):
            if sys.stdin.closed:
                print("Can't run interactive shell: sys.stdin closed", file=sys.stderr)
            else:
                code = pys_shell(
                    globals=result.context.symbol_table,
                    flags=result.context.flags,
                    parser_flags=result.parser_flags
                )

elif args.command is not None:
    hook.argv[0] = '-c'

    file = PysFileBuffer(args.command, '<arg-command>')
    code = pys_runner(
        file=file,
        mode='exec',
        symbol_table=_normalize_namespace(file, undefined),
        flags=flags
    ).end_process()[0]

else:
    code = pys_shell(
        globals=undefined,
        flags=flags
    )

sys.exit(code)