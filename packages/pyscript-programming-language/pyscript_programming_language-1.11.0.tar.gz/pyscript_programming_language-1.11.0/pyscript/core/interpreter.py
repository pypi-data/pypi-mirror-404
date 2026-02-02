from .constants import TOKENS, DEBUG
from .cache import undefined
from .checks import is_unpack_assignment, is_equals, is_public_attribute
from .context import PysClassContext
from .exceptions import PysTraceback
from .handlers import handle_call
from .mapping import BINARY_FUNCTIONS_MAP, UNARY_FUNCTIONS_MAP
from .nodes import PysNode, PysIdentifierNode, PysAttributeNode, PysSubscriptNode
from .objects import PysFunction
from .pysbuiltins import ce, nce, increment, decrement
from .results import PysRunTimeResult
from .symtab import PysClassSymbolTable, find_closest
from .utils.generic import getattribute, setimuattr, is_object_of, get_error_args
from .utils.similarity import get_closest

from collections.abc import Iterable

T_KEYWORD = TOKENS['KEYWORD']
T_STRING = TOKENS['STRING']
T_AND = TOKENS['DOUBLE-AMPERSAND']
T_OR = TOKENS['DOUBLE-PIPE']
T_NOT = TOKENS['EXCLAMATION']
T_CE = TOKENS['EQUAL-TILDE']
T_NCE = TOKENS['EXCLAMATION-TILDE']
T_NULLISH = TOKENS['DOUBLE-QUESTION']

get_incremental_function = {
    TOKENS['DOUBLE-PLUS']: increment,
    TOKENS['DOUBLE-MINUS']: decrement
}.__getitem__

get_value_from_keyword = {
    'True': True,
    'False': False,
    'None': None,
    'true': True,
    'false': False,
    'nil': None,
    'none': None,
    'null': None
}.__getitem__

def visit_NumberNode(node, context):
    return PysRunTimeResult().success(node.value.value)

def visit_StringNode(node, context):
    return PysRunTimeResult().success(node.value.value)

def visit_KeywordNode(node, context):
    name = node.name.value
    return PysRunTimeResult().success(
        (True if context.flags & DEBUG else False)
        if name == '__debug__' else
        get_value_from_keyword(name)
    )

def visit_IdentifierNode(node, context):
    result = PysRunTimeResult()

    position = node.position
    name = node.name.value
    symbol_table = context.symbol_table

    with result(context, position):
        value = symbol_table.get(name)

        if value is undefined:
            closest_symbol = find_closest(symbol_table, name)

            return result.failure(
                PysTraceback(
                    NameError(
                        f"name {name!r} is not defined" +
                        (
                            ''
                            if closest_symbol is None else
                            f". Did you mean {closest_symbol!r}?"
                        )
                    ),
                    context,
                    position
                )
            )

    if result.should_return():
        return result

    return result.success(value)

def visit_DictionaryNode(node, context):
    result = PysRunTimeResult()

    elements = node.class_type()

    register = result.register
    should_return = result.should_return
    setitem = getattribute(elements, '__setitem__')

    for nkey, nvalue in node.pairs:
        key = register(get_visitor(nkey.__class__)(nkey, context))
        if should_return():
            return result

        value = register(get_visitor(nvalue.__class__)(nvalue, context))
        if should_return():
            return result

        with result(context, nkey.position):
            setitem(key, value)

        if should_return():
            return result

    return result.success(elements)

def visit_SetNode(node, context):
    result = PysRunTimeResult()

    elements = set()

    register = result.register
    should_return = result.should_return
    add = elements.add

    for nelement in node.elements:

        with result(context, nelement.position):
            add(register(get_visitor(nelement.__class__)(nelement, context)))

        if should_return():
            return result

    return result.success(elements)

def visit_ListNode(node, context):
    result = PysRunTimeResult()

    elements = []

    register = result.register
    should_return = result.should_return
    append = elements.append

    for nelement in node.elements:
        append(register(get_visitor(nelement.__class__)(nelement, context)))
        if should_return():
            return result

    return result.success(elements)

def visit_TupleNode(node, context):
    result = PysRunTimeResult()

    elements = []

    register = result.register
    should_return = result.should_return
    append = elements.append

    for nelement in node.elements:
        append(register(get_visitor(nelement.__class__)(nelement, context)))
        if should_return():
            return result

    return result.success(tuple(elements))

def visit_AttributeNode(node, context):
    result = PysRunTimeResult()

    should_return = result.should_return
    nattribute = node.attribute
    ntarget = node.target

    target = result.register(get_visitor(ntarget.__class__)(ntarget, context))
    if should_return():
        return result

    with result(context, nattribute.position):
        return result.success(getattr(target, nattribute.value))

    if should_return():
        return result

def visit_SubscriptNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ntarget = node.target

    target = register(get_visitor(ntarget.__class__)(ntarget, context))
    if should_return():
        return result

    slice = register(visit_slice_SubscriptNode(node.slice, context))
    if should_return():
        return result

    with result(context, node.position):
        return result.success(target[slice])

    if should_return():
        return result

def visit_CallNode(node, context):
    result = PysRunTimeResult()

    args = []
    kwargs = {}

    register = result.register
    should_return = result.should_return
    append = args.append
    setitem = kwargs.__setitem__
    nposition = node.position
    ntarget = node.target

    target = register(get_visitor(ntarget.__class__)(ntarget, context))
    if should_return():
        return result

    for nargument in node.arguments:

        if nargument.__class__ is tuple:
            keyword, nvalue = nargument
            setitem(keyword.value, register(get_visitor(nvalue.__class__)(nvalue, context)))
            if should_return():
                return result

        else:
            append(register(get_visitor(nargument.__class__)(nargument, context)))
            if should_return():
                return result

    with result(context, nposition):
        handle_call(target, context, nposition)
        return result.success(target(*args, **kwargs))

    if should_return():
        return result

def visit_ChainOperatorNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    nposition = node.position
    get_expression = node.expressions.__getitem__
    first = get_expression(0)

    left = register(get_visitor(first.__class__)(first, context))
    if should_return():
        return result

    with result(context, nposition):

        for i, toperand in enumerate(node.operations, start=1):
            omatch = toperand.match
            otype = toperand.type
            nexpression = get_expression(i)

            right = register(get_visitor(nexpression.__class__)(nexpression, context))
            if should_return():
                return result

            if omatch(T_KEYWORD, 'in'):
                value = left in right
            elif omatch(T_KEYWORD, 'is'):
                value = left is right
            elif otype == T_CE:
                handle_call(ce, context, nposition)
                value = ce(left, right)
            elif otype == T_NCE:
                handle_call(nce, context, nposition)
                value = nce(left, right)
            else:
                value = BINARY_FUNCTIONS_MAP(otype)(left, right)

            if not value:
                break

            left = right

    if should_return():
        return result

    return result.success(value)

def visit_TernaryOperatorNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ncondition = node.condition

    condition = register(get_visitor(ncondition.__class__)(ncondition, context))
    if should_return():
        return result

    with result(context, node.position):
        nvalue = node.valid if condition else node.invalid
        value = register(get_visitor(nvalue.__class__)(nvalue, context))
        if should_return():
            return result

        return result.success(value)

    if should_return():
        return result

def visit_BinaryOperatorNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    omatch = node.operand.match
    otype = node.operand.type
    nleft = node.left
    nright = node.right

    left = register(get_visitor(nleft.__class__)(nleft, context))
    if should_return():
        return result

    with result(context, node.position):
        should_return_right = True

        if omatch(T_KEYWORD, 'and') or otype == T_AND:
            if not left:
                return result.success(left)
        elif omatch(T_KEYWORD, 'or') or otype == T_OR:
            if left:
                return result.success(left)
        elif otype == T_NULLISH:
            if left is not None:
                return result.success(left)
        else:
            should_return_right = False

        right = register(get_visitor(nright.__class__)(nright, context))
        if should_return():
            return result

        return result.success(
            right
            if should_return_right else
            BINARY_FUNCTIONS_MAP(otype)(left, right)
        )

    if should_return():
        return result

def visit_UnaryOperatorNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    omatch = node.operand.match
    otype = node.operand.type
    nvalue = node.value

    value = register(get_visitor(nvalue.__class__)(nvalue, context))
    if should_return():
        return result

    with result(context, node.position):
        if omatch(T_KEYWORD, 'not') or otype == T_NOT:
            return result.success(not value)
        elif omatch(T_KEYWORD, 'typeof'):
            return result.success(type(value).__name__)
        return result.success(UNARY_FUNCTIONS_MAP(otype)(value))

    if should_return():
        return result

def visit_IncrementalNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    nposition = node.position
    ntarget = node.target

    value = register(get_visitor(ntarget.__class__)(ntarget, context))
    if should_return():
        return result

    with result(context, nposition):
        func = get_incremental_function(node.operand.type)

        handle_call(func, context, nposition)
        increast_value = func(value)
        if node.operand_position == 'left':
            value = increast_value

        register(visit_declaration_AssignNode(ntarget, context, increast_value))
        if should_return():
            return result

        return result.success(value)

    if should_return():
        return result

def visit_StatementsNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    body = node.body

    if len(body) == 1:
        nvalue = body[0]
        value = register(get_visitor(nvalue.__class__)(nvalue, context))
        if should_return():
            return result

        return result.success(value)

    for nelement in body:
        register(get_visitor(nelement.__class__)(nelement, context))
        if should_return():
            return result

    return result.success(None)

def visit_AssignNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    nvalue = node.value

    value = register(get_visitor(nvalue.__class__)(nvalue, context))
    if should_return():
        return result

    register(visit_declaration_AssignNode(node.target, context, value, node.operand.type))
    if should_return():
        return result

    return result.success(value)

def visit_ImportNode(node, context):
    result = PysRunTimeResult()

    should_return = result.should_return
    get_symbol = context.symbol_table.get
    set_symbol = context.symbol_table.set
    npackages = node.packages
    tname, tas_name = node.name
    name_position = tname.position

    with result(context, name_position):
        name_module = tname.value
        use_python_package = False

        require = get_symbol('require')

        if require is undefined:
            use_python_package = True
        else:
            handle_call(require, context, name_position)
            try:
                module = require(name_module)
            except ModuleNotFoundError:
                use_python_package = True

        if use_python_package:
            pyimport = get_symbol('pyimport')

            if pyimport is undefined:
                pyimport = get_symbol('__import__')

                if pyimport is undefined:
                    return result.failure(
                        PysTraceback(
                            NameError("names 'require', 'pyimport', and '__import__' is not defined"),
                            context,
                            node.position
                        )
                    )

            handle_call(pyimport, context, name_position)
            module = pyimport(name_module)

    if should_return():
        return result

    if npackages == 'all':

        with result(context, name_position):
            exported_from = '__all__'
            exported_packages = getattr(module, exported_from, undefined)
            if exported_packages is undefined:
                exported_from = '__dir__()'
                exported_packages = filter(is_public_attribute, dir(module))

            for package in exported_packages:

                if not isinstance(package, str):
                    return result.failure(
                        PysTraceback(
                            TypeError(
                                f"Item in {module.__name__}.{exported_from} must be str, not {type(package).__name__}"
                            ),
                            context,
                            name_position
                        )
                    )

                set_symbol(package, getattr(module, package))

        if should_return():
            return result

    elif npackages:

        for tpackage, tas_package in npackages:

            with result(context, tpackage.position):
                set_symbol(
                    (tpackage if tas_package is None else tas_package).value,
                    getattr(module, tpackage.value)
                )

            if should_return():
                return result

    elif not (tname.type == T_STRING and tas_name is None):

        with result(context, node.position):
            set_symbol((tname if tas_name is None else tas_name).value, module)

        if should_return():
            return result

    return result.success(None)

def visit_IfNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    else_body = node.else_body

    for ncondition, body in node.cases_body:
        condition = register(get_visitor(ncondition.__class__)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition.position):
            condition = True if condition else False

        if should_return():
            return result

        if condition:
            register(get_visitor(body.__class__)(body, context))
            if should_return():
                return result

            return result.success(None)

    if else_body:
        register(get_visitor(else_body.__class__)(else_body, context))
        if should_return():
            return result

    return result.success(None)

def visit_SwitchNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    default_body = node.default_body
    ntarget = node.target

    fall_through = False
    no_match_found = True

    target = register(get_visitor(ntarget.__class__)(ntarget, context))
    if should_return():
        return result

    for ncondition, body in node.case_cases:
        case = register(get_visitor(ncondition.__class__)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition.position):
            equal = True if target == case else False

        if should_return():
            return result

        if fall_through or equal:
            no_match_found = False

            register(get_visitor(body.__class__)(body, context))
            if should_return() and not result.should_break:
                return result

            if result.should_break:
                result.should_break = False
                fall_through = False
            else:
                fall_through = True

    if (fall_through or no_match_found) and default_body:
        register(get_visitor(default_body.__class__)(default_body, context))
        if should_return() and not result.should_break:
            return result

        result.should_break = False

    return result.success(None)

def visit_MatchNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ntarget = node.target

    compare = False

    if ntarget:
        target = register(get_visitor(ntarget.__class__)(ntarget, context))
        if should_return():
            return result

        compare = True

    for ncondition, nvalue in node.cases:
        condition = register(get_visitor(ncondition.__class__)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition.position):
            valid = target == condition if compare else (True if condition else False)

        if should_return():
            return result

        if valid:
            value = register(get_visitor(nvalue.__class__)(nvalue, context))
            if should_return():
                return result

            return result.success(value)

    ndefault = node.default

    if ndefault:
        default = register(get_visitor(ndefault.__class__)(ndefault, context))
        if should_return():
            return result

        return result.success(default)

    return result.success(None)

def visit_TryNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    failure = result.failure
    should_return = result.should_return
    body = node.body
    else_body = node.else_body
    finally_body = node.finally_body

    register(get_visitor(body.__class__)(body, context))
    error = result.error

    if error:
        exception = error.exception

        failure(None)

        for (targets, tparameter), body in node.catch_cases:
            handle_exception = True
            stop = False

            if targets:
                handle_exception = False

                for nerror_class in targets:
                    error_class = register(visit_IdentifierNode(nerror_class, context))
                    if result.error:
                        setimuattr(result.error, 'cause', error)
                        stop = True
                        break

                    if not (isinstance(error_class, type) and issubclass(error_class, BaseException)):
                        failure(
                            PysTraceback(
                                TypeError("catching classes that do not inherit from BaseException is not allowed"),
                                context,
                                nerror_class.position,
                                error
                            )
                        )
                        stop = True
                        break

                    if is_object_of(exception, error_class):
                        handle_exception = True
                        break

            if stop:
                break

            elif handle_exception:

                if tparameter:
                    with result(context, position := tparameter.position):
                        (symbol_table := context.symbol_table).set(parameter := tparameter.value, error.exception)
                    if should_return():
                        return

                register(get_visitor(body.__class__)(body, context))
                if result.error:
                    setimuattr(result.error, 'cause', error)

                if tparameter:
                    with result(context, position):
                        symbol_table.remove(parameter)
                    if should_return():
                        return

                break

        else:
            failure(error)

    elif else_body:
        register(get_visitor(else_body.__class__)(else_body, context))

    if finally_body:
        finally_result = PysRunTimeResult()
        finally_result.register(get_visitor(finally_body.__class__)(finally_body, context))
        if finally_result.should_return():
            if finally_result.error:
                setimuattr(finally_result.error, 'cause', result.error)
            return finally_result

    if should_return():
        return result

    return result.success(None)

def visit_WithNode(node, context):
    result = PysRunTimeResult()

    exits = []

    register = result.register
    failure = result.failure
    should_return = result.should_return
    append = exits.append
    set_symbol = context.symbol_table.set

    for ncontext, nalias in node.contexts:
        context_value = register(get_visitor(ncontext.__class__)(ncontext, context))
        if should_return():
            break

        ncontext_position = ncontext.position

        with result(context, ncontext_position):
            enter = getattr(context_value, '__enter__', undefined)
            exit = getattr(context_value, '__exit__', undefined)

            missed_enter = enter is undefined
            missed_exit = exit is undefined

            if missed_enter or missed_exit:
                message = f"{type(context_value).__name__!r} object does not support the context manager protocol"

                if missed_enter and missed_exit:
                    pass
                elif missed_enter:
                    message += " (missed __enter__ method)"
                elif missed_exit:
                    message += " (missed __exit__ method)"

                result.failure(
                    PysTraceback(
                        TypeError(message),
                        context,
                        ncontext_position
                    )
                )
                break

            handle_call(enter, context, ncontext_position)
            enter_value = enter()
            append((exit, ncontext_position))

        if should_return():
            break

        if nalias:
            with result(context, nalias.position):
                set_symbol(nalias.value, enter_value)
            if should_return():
                break

    if not should_return():
        body = node.body
        register(get_visitor(body.__class__)(body, context))

    error = result.error

    for exit, ncontext_position in reversed(exits):
        with result(context, ncontext_position):
            handle_call(exit, context, ncontext_position)
            if exit(*get_error_args(error)):
                failure(None)
                error = None

    if should_return():
        if result.error and result.error is not error:
            setimuattr(result.error, 'cause', error)
        return result

    return result.success(None)

def visit_ForNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    nheader = node.header
    nheader_length = len(nheader)
    body = node.body
    body_class = body.__class__
    else_body = node.else_body

    if nheader_length == 2:
        ndeclaration, niteration = nheader
        niteration_position = niteration.position

        iteration = register(get_visitor(niteration.__class__)(niteration, context))
        if should_return():
            return result

        with result(context, niteration_position):
            handle_call(getattr(iteration, '__iter__', None), context, niteration_position)
            iteration = iter(iteration)
            next = iteration.__next__

        if should_return():
            return result

        def condition():
            with result(context, niteration_position):
                handle_call(next, context, niteration_position)
                register(visit_declaration_AssignNode(ndeclaration, context, next()))

            if should_return():
                if is_object_of(result.error.exception, StopIteration):
                    result.failure(None)
                return False

            return True

        def update():
            pass

    elif nheader_length == 3:
        ndeclaration, ncondition, nupdate = nheader

        if ndeclaration:
            register(get_visitor(ndeclaration.__class__)(ndeclaration, context))
            if should_return():
                return result

        if ncondition:
            ncondition_class = ncondition.__class__
            ncondition_position = ncondition.position
            def condition():
                value = register(get_visitor(ncondition_class)(ncondition, context))
                if should_return():
                    return False
                with result(context, ncondition_position):
                    return True if value else False

        else:
            def condition():
                return True

        if nupdate:
            nupdate_class = nupdate.__class__
            def update():
                register(get_visitor(nupdate_class)(nupdate, context))

        else:
            def update():
                pass

    while True:
        done = condition()
        if should_return():
            return result

        if not done:
            break

        register(get_visitor(body_class)(body, context))
        if should_return() and not result.should_continue and not result.should_break:
            return result

        if result.should_continue:
            result.should_continue = False

        elif result.should_break:
            break

        update()
        if should_return():
            return result

    if result.should_break:
        result.should_break = False

    elif else_body:
        register(get_visitor(else_body.__class__)(else_body, context))
        if should_return():
            return result

    return result.success(None)

def visit_WhileNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ncondition = node.condition
    ncondition_class = ncondition.__class__
    ncondition_position = ncondition.position
    body = node.body
    body_class = body.__class__
    else_body = node.else_body

    while True:
        condition = register(get_visitor(ncondition_class)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition_position):
            if not condition:
                break

        if should_return():
            return result

        register(get_visitor(body_class)(body, context))
        if should_return() and not result.should_continue and not result.should_break:
            return result

        if result.should_continue:
            result.should_continue = False

        elif result.should_break:
            break

    if result.should_break:
        result.should_break = False

    elif else_body:
        register(get_visitor(else_body.__class__)(else_body, context))
        if should_return():
            return result

    return result.success(None)

def visit_DoWhileNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ncondition = node.condition
    ncondition_class = ncondition.__class__
    ncondition_position = ncondition.position
    body = node.body
    body_class = body.__class__
    else_body = node.else_body

    while True:
        register(get_visitor(body_class)(body, context))
        if should_return() and not result.should_continue and not result.should_break:
            return result

        if result.should_continue:
            result.should_continue = False

        elif result.should_break:
            break

        condition = register(get_visitor(ncondition_class)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition_position):
            if not condition:
                break

        if should_return():
            return result

    if result.should_break:
        result.should_break = False

    elif else_body:
        register(get_visitor(else_body.__class__)(else_body, context))
        if should_return():
            return result

    return result.success(None)

def visit_RepeatNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ncondition = node.condition
    ncondition_class = ncondition.__class__
    ncondition_position = ncondition.position
    body = node.body
    body_class = body.__class__
    else_body = node.else_body

    while True:
        register(get_visitor(body_class)(body, context))
        if should_return() and not result.should_continue and not result.should_break:
            return result

        if result.should_continue:
            result.should_continue = False

        elif result.should_break:
            break

        condition = register(get_visitor(ncondition_class)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition_position):
            if condition:
                break

        if should_return():
            return result

    if result.should_break:
        result.should_break = False

    elif else_body:
        register(get_visitor(else_body.__class__)(else_body, context))
        if should_return():
            return result

    return result.success(None)

def visit_ClassNode(node, context):
    result = PysRunTimeResult()

    bases = []

    register = result.register
    should_return = result.should_return
    append = bases.append
    nposition = node.position
    name = node.name.value
    body = node.body
    symbol_table = context.symbol_table

    for nbase in node.bases:
        append(register(get_visitor(nbase.__class__)(nbase, context)))
        if should_return():
            return result

    class_context = PysClassContext(
        name=name,
        symbol_table=PysClassSymbolTable(symbol_table),
        parent=context,
        parent_entry_position=nposition
    )

    register(get_visitor(body.__class__)(body, class_context))
    if should_return():
        return result

    with result(context, nposition):
        cls = type(name, tuple(bases), class_context.symbol_table.symbols)
        cls.__qualname__ = class_context.qualname

    if should_return():
        return result

    for ndecorator in reversed(node.decorators):
        decorator = register(get_visitor(ndecorator.__class__)(ndecorator, context))
        if should_return():
            return result

        dposition = ndecorator.position

        with result(context, dposition):
            handle_call(decorator, context, dposition)
            cls = decorator(cls)

        if should_return():
            return result

    with result(context, nposition):
        symbol_table.set(name, cls)

    if should_return():
        return result

    return result.success(None)

def visit_FunctionNode(node, context):
    result = PysRunTimeResult()

    parameters = []

    register = result.register
    should_return = result.should_return
    append = parameters.append
    nposition = node.position
    name = None if node.name is None else node.name.value

    for nparameter in node.parameters:

        if nparameter.__class__ is tuple:
            keyword, nvalue = nparameter

            value = register(get_visitor(nvalue.__class__)(nvalue, context))
            if should_return():
                return result

            append((keyword.value, value))

        else:
            append(nparameter.value)

    func = PysFunction(
        name=name,
        qualname=context.qualname,
        parameters=parameters,
        body=node.body,
        context=context,
        position=nposition
    )

    for ndecorator in reversed(node.decorators):
        decorator = register(get_visitor(ndecorator.__class__)(ndecorator, context))
        if should_return():
            return result

        dposition = ndecorator.position

        with result(context, dposition):
            handle_call(decorator, context, dposition)
            func = decorator(func)

        if should_return():
            return result

    if name:
        with result(context, nposition):
            context.symbol_table.set(name, func)
        if should_return():
            return result

    return result.success(func)

def visit_GlobalNode(node, context):
    context.symbol_table.globals.update(name.value for name in node.identifiers)
    return PysRunTimeResult().success(None)

def visit_ReturnNode(node, context):
    result = PysRunTimeResult()

    nvalue = node.value

    if nvalue:
        value = result.register(get_visitor(nvalue.__class__)(nvalue, context))
        if result.should_return():
            return result
        return result.success_return(value)

    return result.success_return(None)

def visit_ThrowNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ntarget = node.target
    ncause = node.cause

    target = register(get_visitor(ntarget.__class__)(ntarget, context))
    if should_return():
        return result

    if not is_object_of(target, BaseException):
        return result.failure(
            PysTraceback(
                TypeError("exceptions must derive from BaseException"),
                context,
                ntarget.position
            )
        )

    if ncause:
        cause = register(get_visitor(ncause.__class__)(ncause, context))
        if should_return():
            return result

        if not is_object_of(cause, BaseException):
            return result.failure(
                PysTraceback(
                    TypeError("exceptions must derive from BaseException"),
                    context,
                    ncause.position
                )
            )

        cause = PysTraceback(
            cause,
            context,
            ncause.position
        )

    else:
        cause = None

    return result.failure(
        PysTraceback(
            target,
            context,
            node.position,
            cause,
            True if ncause else False
        )
    )

def visit_AssertNode(node, context):
    result = PysRunTimeResult()

    if not (context.flags & DEBUG):
        register = result.register
        should_return = result.should_return
        ncondition = node.condition

        condition = register(get_visitor(ncondition.__class__)(ncondition, context))
        if should_return():
            return result

        with result(context, ncondition.position):

            if not condition:
                nmessage = node.message

                if nmessage:
                    message = register(get_visitor(nmessage.__class__)(nmessage, context))
                    if should_return():
                        return result

                    return result.failure(
                        PysTraceback(
                            AssertionError(message),
                            context,
                            node.position
                        )
                    )

                return result.failure(
                    PysTraceback(
                        AssertionError,
                        context,
                        node.position
                    )
                )

        if should_return():
            return result

    return result.success(None)

def visit_DeleteNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    symbol_table = context.symbol_table

    for ntarget in node.targets:
        target_position = ntarget.position
        ntarget_type = ntarget.__class__

        if ntarget_type is PysIdentifierNode:
            name = ntarget.name.value

            with result(context, target_position):

                if not symbol_table.remove(name):
                    closest_symbol = get_closest(symbol_table.symbols.keys(), name)

                    return result.failure(
                        PysTraceback(
                            NameError(
                                (
                                    f"name {name!r} is not defined"
                                    if symbol_table.get(name) is undefined else
                                    f"name {name!r} is not defined on local"
                                )
                                +
                                (
                                    ''
                                    if closest_symbol is None else
                                    f". Did you mean {closest_symbol!r}?"
                                )
                            ),
                            context,
                            target_position
                        )
                    )

            if should_return():
                return result

        elif ntarget_type is PysAttributeNode:
            tntarget = ntarget.target
            target = register(get_visitor(tntarget.__class__)(tntarget, context))
            if should_return():
                return result

            with result(context, target_position):
                delattr(target, ntarget.attribute.value)

            if should_return():
                return result

        elif ntarget_type is PysSubscriptNode:
            tntarget = ntarget.target
            target = register(get_visitor(tntarget.__class__)(tntarget, context))
            if should_return():
                return result

            slice = register(visit_slice_SubscriptNode(ntarget.slice, context))
            if should_return():
                return result

            with result(context, target_position):
                del target[slice]

            if should_return():
                return result

    return result.success(None)

def visit_EllipsisNode(node, context):
    return PysRunTimeResult().success(...)

def visit_ContinueNode(node, context):
    return PysRunTimeResult().success_continue()

def visit_BreakNode(node, context):
    return PysRunTimeResult().success_break()

def visit_slice_SubscriptNode(node, context):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ntype = node.__class__

    if ntype is slice:
        start = node.start
        stop = node.stop
        step = node.step

        if start is not None:
            start = register(get_visitor(start.__class__)(start, context))
            if should_return():
                return result

        if stop is not None:
            stop = register(get_visitor(stop.__class__)(stop, context))
            if should_return():
                return result

        if step is not None:
            step = register(get_visitor(step.__class__)(step, context))
            if should_return():
                return result

        return result.success(slice(start, stop, step))

    elif ntype is tuple:
        slices = []
        append = slices.append

        for element in node:
            append(register(visit_slice_SubscriptNode(element, context)))
            if should_return():
                return result

        return result.success(tuple(slices))

    else:
        value = register(get_visitor(node.__class__)(node, context))
        if should_return():
            return result

        return result.success(value)

def visit_declaration_AssignNode(node, context, value, operand=TOKENS['EQUAL']):
    result = PysRunTimeResult()

    register = result.register
    should_return = result.should_return
    ntype = node.__class__

    if ntype is PysIdentifierNode:
        symbol_table = context.symbol_table
        name = node.name.value

        with result(context, node.position):

            if not symbol_table.set(name, value, operand=operand):
                closest_symbol = get_closest(symbol_table.symbols.keys(), name)

                result.failure(
                    PysTraceback(
                        NameError(
                            (
                                f"name {name!r} is not defined"
                                if symbol_table.get(name) is undefined else
                                f"name {name!r} is not defined on local"
                            )
                            +
                            (
                                ''
                                if closest_symbol is None else
                                f". Did you mean {closest_symbol!r}?"
                            )
                        ),
                        context,
                        node.position
                    )
                )

        if should_return():
            return result

    elif ntype is PysAttributeNode:
        ntarget = node.target
        target = register(get_visitor(ntarget.__class__)(ntarget, context))
        if should_return():
            return result

        attribute = node.attribute.value

        with result(context, node.position):
            setattr(
                target,
                attribute,
                value
                if is_equals(operand) else
                BINARY_FUNCTIONS_MAP(operand)(getattr(target, attribute), value)
            )

        if should_return():
            return result

    elif ntype is PysSubscriptNode:
        ntarget = node.target
        target = register(get_visitor(ntarget.__class__)(ntarget, context))
        if should_return():
            return result

        slice = register(visit_slice_SubscriptNode(node.slice, context))
        if should_return():
            return result

        with result(context, node.position):
            target[slice] = value if is_equals(operand) else BINARY_FUNCTIONS_MAP(operand)(target[slice], value)

        if should_return():
            return result

    elif is_unpack_assignment(ntype):
        position = node.position

        if not isinstance(value, Iterable):
            return result.failure(
                PysTraceback(
                    TypeError(f"cannot unpack non-iterable {type(value).__name__} object"),
                    context,
                    position
                )
            )

        elements = node.elements
        count = 0

        with result(context, position):

            for element, element_value in zip(elements, value):
                register(visit_declaration_AssignNode(element, context, element_value, operand))
                if should_return():
                    return result

                count += 1

        if should_return():
            return result

        length = len(elements)

        if count < length:
            return result.failure(
                PysTraceback(
                    ValueError(f"not enough values to unpack (expected {length}, got {count})"),
                    context,
                    node.position
                )
            )

        elif count > length:
            return result.failure(
                PysTraceback(
                    ValueError(f"to many values to unpack (expected {length})"),
                    context,
                    node.position
                )
            )

    return result.success(None)

get_visitor = {
    class_node: globals()['visit_' + class_node.__name__.removeprefix('Pys')]
    for class_node in PysNode.__subclasses__()
}.__getitem__