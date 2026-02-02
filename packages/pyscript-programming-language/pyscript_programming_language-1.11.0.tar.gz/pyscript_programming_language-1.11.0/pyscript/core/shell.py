from .bases import Pys
from .mapping import BRACKETS_MAP
from .utils.generic import clear_console

from typing import Literal

import sys

class PysCommandLineShell(Pys):

    def __init__(self, ps1: str = '>>> ', ps2: str = '... ') -> None:
        self.ps1 = ps1
        self.ps2 = ps2

        self._brackets_stack = []
        self.reset()

    def _is_nextline(self):
        return not self._must_break and (
            len(self._brackets_stack) > 0 or
            self._next_line or
            self._is_triple_string or
            self._in_decorator
        )

    def reset(self) -> None:
        self._brackets_stack.clear()
        self._in_string = False
        self._in_decorator = False
        self._is_triple_string = False
        self._next_line = False
        self._must_break = False
        self._string_prefix = ''
        self._full_text = ''

    def prompt(self) -> str | Literal[0]:
        while True:

            try:

                if self._is_nextline():
                    text = input(self.ps2)

                else:
                    text = input(self.ps1)
                    if text == '/exit':
                        return 0
                    elif text == '/clear':
                        clear_console()
                        continue

            except (OSError, ValueError):
                return 0

            except (MemoryError, UnicodeDecodeError):
                print("InputError", file=sys.stderr)
                continue

            self._next_line = False
            self._in_decorator = False

            is_space = True
            i = 0

            while i < len(text):
                character = text[i]

                if character == '\\':
                    i += 1
                    character = text[i:i+1]

                    if character == '':
                        self._next_line = True
                        break

                elif character in '\'"':
                    bind_3 = text[i:i+3]

                    if self._is_triple_string:
                        if len(bind_3) == 3 and self._string_prefix * 3 == bind_3:
                            self._in_string = False
                            self._is_triple_string = False
                            i += 2

                    else:
                        if not self._in_string and bind_3 in ("'''", '"""'):
                            self._is_triple_string = True
                            i += 2

                        if self._in_string and self._string_prefix == character:
                            self._in_string = False
                        else:
                            self._string_prefix = character
                            self._in_string = True

                if not self._in_string:

                    if character == '#':
                        break

                    elif is_space and character == '@':
                        self._in_decorator = True
                        i += 1
                        continue

                    elif character in '([{':
                        self._brackets_stack.append(ord(character))

                    elif character in ')]}':
                        self._must_break = (
                            BRACKETS_MAP[self._brackets_stack.pop()] != ord(character)
                            if self._brackets_stack else
                            True
                        )

                    if not character.isspace():
                        is_space = False

                i += 1

            if self._in_decorator and is_space:
                self._in_decorator = False

            if self._in_string and not (self._next_line or self._is_triple_string):
                self._must_break = True

            if self._is_nextline():
                self._full_text += text + '\n'
            else:
                full_text = self._full_text + text
                self.reset()
                return full_text