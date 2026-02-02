from .bases import Pys
from .context import PysContext, PysClassContext
from .exceptions import PysTraceback, PysSignal
from .results import PysRunTimeResult
from .symtab import PysSymbolTable
from .utils.similarity import get_closest
from .utils.string import join

from types import MethodType

class PysObject(Pys):
    __slots__ = ()

class PysCode(PysObject):

    def __init__(self, **kwargs):
        self.__dict__ = kwargs

class PysFunction(PysObject):

    def __init__(self, name, qualname, parameters, body, context, position):
        # circular import problem solved
        from .interpreter import get_visitor

        context = context.parent if isinstance(context, PysClassContext) else context

        argument_names = []
        keyword_argument_names = []
        parameter_names = []
        keyword_arguments = {}

        append_argnames = argument_names.append
        append_keynames = keyword_argument_names.append
        append_paramnames = parameter_names.append
        set_keywordarg = keyword_arguments.__setitem__

        for parameter in parameters:
            if parameter.__class__ is tuple:
                arg, value = parameter
                append_paramnames(arg)
                append_keynames(arg)
                set_keywordarg(arg, value)
            else:
                append_paramnames(parameter)
                append_argnames(parameter)

        self.__name__ = name = '<function>' if name is None else name
        self.__qualname__ = name if qualname is None else f'{qualname}.{name}'
        self.__code__ = PysCode(
            parameters=parameters,
            body=body,
            context=context,
            position=position,
            file=context.file,
            closure_symbol_table=context.symbol_table,
            get_visitor=get_visitor,
            parameters_length=len(parameters),
            argument_names=tuple(argument_names),
            keyword_argument_names=tuple(keyword_argument_names),
            parameter_names=tuple(parameter_names),
            keyword_arguments=keyword_arguments
        )

    def __repr__(self):
        return f'<function {self.__qualname__} at 0x{id(self):016X}>'

    def __get__(self, instance, owner):
        return self if instance is None else MethodType(self, instance)

    def __call__(self, *args, **kwargs):
        qualname = self.__qualname__
        code = self.__code__
        code_body = code.body
        code_context = code.context
        code_position = code.position
        code_parameters_length = code.parameters_length
        code_parameter_names = code.parameter_names
        arguments_length = len(args)

        result = PysRunTimeResult()
        symbol_table = PysSymbolTable(code.closure_symbol_table)
        registered_arguments = set()

        add_argument = registered_arguments.add
        set_symbol = symbol_table.set

        for name, arg in zip(code.argument_names, args):
            set_symbol(name, arg)
            add_argument(name)

        combined_keyword_arguments = code.keyword_arguments | kwargs
        pop_keyword_arguments = combined_keyword_arguments.pop

        for name, arg in zip(code.keyword_argument_names, args[len(registered_arguments):]):
            set_symbol(name, arg)
            add_argument(name)
            pop_keyword_arguments(name, None)

        for name, value in combined_keyword_arguments.items():

            if name in registered_arguments:
                raise PysSignal(
                    result.failure(
                        PysTraceback(
                            TypeError(f"{qualname}() got multiple values for argument {name!r}"),
                            code_context,
                            code_position
                        )
                    )
                )

            elif name not in code_parameter_names:
                closest_argument = get_closest(set(code_parameter_names), name)
                hint_message = "" if closest_argument is None else f". Did you mean {closest_argument!r}?"

                raise PysSignal(
                    result.failure(
                        PysTraceback(
                            TypeError(f"{qualname}() got an unexpected keyword argument {name!r}{hint_message}"),
                            code_context,
                            code_position
                        )
                    )
                )

            set_symbol(name, value)
            add_argument(name)

        total_registered = len(registered_arguments)

        if total_registered < code_parameters_length:
            missing_arguments = [repr(name) for name in code_parameter_names if name not in registered_arguments]
            total_missing = len(missing_arguments)

            raise PysSignal(
                result.failure(
                    PysTraceback(
                        TypeError(
                            f"{qualname}() missing {total_missing} required positional argument"
                            f"{'' if total_missing == 1 else 's'}: {join(missing_arguments, conjunction='and')}"
                        ),
                        code_context,
                        code_position
                    )
                )
            )

        elif total_registered > code_parameters_length or arguments_length > code_parameters_length:
            given_arguments = arguments_length if arguments_length > code_parameters_length else total_registered

            raise PysSignal(
                result.failure(
                    PysTraceback(
                        TypeError(
                            f"{qualname}() takes no arguments ({given_arguments} given)"
                            if code_parameters_length == 0 else
                            f"{qualname}() takes {code_parameters_length} positional argument"
                            f"{'' if code_parameters_length == 1 else 's'} but {given_arguments} were given"
                        ),
                        code_context,
                        code_position
                    )
                )
            )

        result.register(
            code.get_visitor(code_body.__class__)(
                code_body,
                PysContext(
                    file=code.file,
                    name=self.__name__,
                    qualname=qualname,
                    symbol_table=symbol_table,
                    parent=code_context,
                    parent_entry_position=code_position
                )
            )
        )

        if result.should_return() and not result.func_should_return:
            raise PysSignal(result)

        return result.func_return_value

class PysPythonFunction(PysFunction):

    def __init__(self, func):
        # circular import problem solved
        from .handlers import handle_call

        self.__func__ = func
        self.__name__ = getattr(func, '__name__', '<function>')
        self.__qualname__ = getattr(func, '__qualname__', '<function>')
        self.__doc__ = getattr(func, '__doc__', None)
        self.__code__ = PysCode(
            context=None,
            position=None,
            handle_call=handle_call
        )

    def __repr__(self):
        return f'<python function {self.__qualname__} at 0x{id(self):016X}>'

    def __call__(self, *args, **kwargs):
        func = self.__func__
        code = self.__code__
        code.handle_call(func, code.context, code.position)
        return func(self, *args, **kwargs)

class PysBuiltinFunction(PysPythonFunction):

    def __repr__(self):
        return f'<built-in function {self.__qualname__}>'