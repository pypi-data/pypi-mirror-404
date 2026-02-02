"""
PyScript is a programming language written 100% in Python. \
This language is not isolated and is directly integrated with the Python's library and namespace levels.
"""

if __import__('sys').version_info < (3, 10):
    raise ImportError("Python version 3.10 and above is required to run PyScript")

from . import core

from .core.constants import (
    DEFAULT, NO_COLOR, DEBUG, SILENT, RETURN_RESULT, DONT_SHOW_BANNER_ON_SHELL, HIGHLIGHT, DICT_TO_JSDICT
)
from .core.cache import undefined, hook
from .core.highlight import (
    HLFMT_HTML, HLFMT_ANSI, HLFMT_BBCODE, pys_highlight, PygmentsPyScriptStyle, PygmentsPyScriptLexer
)
from .core.runner import pys_runner, pys_exec, pys_eval, pys_require, pys_shell
from .core.version import version, version_info, __version__, __date__

__all__ = (
    'core',
    'DEFAULT',
    'NO_COLOR',
    'DEBUG',
    'SILENT',
    'RETURN_RESULT',
    'DONT_SHOW_BANNER_ON_SHELL',
    'HIGHLIGHT',
    'DICT_TO_JSDICT',
    'HLFMT_HTML',
    'HLFMT_ANSI',
    'HLFMT_BBCODE',
    'undefined',
    'hook',
    'version',
    'version_info',
    'pys_highlight',
    'pys_runner',
    'pys_exec',
    'pys_eval',
    'pys_require',
    'pys_shell',
    'PygmentsPyScriptStyle',
    'PygmentsPyScriptLexer'
)