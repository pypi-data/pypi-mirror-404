from pyscript.core.checks import is_keyword
from pyscript.core.constants import TOKENS
from pyscript.core.mapping import SYMBOLS_TOKEN_MAP
from pyscript.core.nodes import PysNode, PysStringNode
from pyscript.core.utils.string import indent as sindent

def indent(string):
    return sindent(string, 4)

def identifier(name):
    return f'${name}' if is_keyword(name) else name

def unparse(ast_obj):
    return get_visitor(ast_obj.__class__)(ast_obj)

def visit_NumberNode(node):
    return repr(node.value.value)

def visit_StringNode(node):
    return repr(node.value.value)

def visit_KeywordNode(node):
    return node.name.value

def visit_IdentifierNode(node):
    return identifier(node.name.value)

def visit_DictionaryNode(node):
    elements = []

    if node.class_type is dict:
        for key, value in node.pairs:
            element_string = unparse(key)
            element_string += ': '
            element_string += unparse(value)
            elements.append(element_string)
    else:
        for key, value in node.pairs:
            element_string = (
                key.value.value 
                if isinstance(key, PysStringNode) and key.value.value.isindentifier() else
                f'[{unparse(key)}]'
            )
            element_string += ': '
            element_string += unparse(value)
            elements.append(element_string)

    return '{' + ', '.join(elements) + '}'

def visit_SetNode(node):
    return '{' + ', '.join(map(unparse, node.elements)) + '}'

def visit_ListNode(node):
    return '[' + ', '.join(map(unparse, node.elements)) + ']'

def visit_TupleNode(node):
    string = ', '.join(map(unparse, node.elements))
    return '(' + (string + ',' if len(node.elements) == 1 else string) + ')'

def visit_AttributeNode(node):
    return f'{unparse(node.target)}.{identifier(node.attribute.value)}'

def visit_SubscriptNode(node):
    string = unparse(node.target)
    string += '['

    if isinstance(node.slice, slice):
        if node.slice.start:
            string += unparse(node.slice.start)
        string += ':'
        if node.slice.stop:
            string += unparse(node.slice.stop)
        string += ':'
        if node.slice.step:
            string += unparse(node.slice.step)

    elif isinstance(node.slice, tuple):
        indices = []

        for index in node.slice:
            index_string = ''

            if isinstance(index, slice):
                if index.start:
                    index_string += unparse(index.start)
                index_string += ':'
                if index.stop:
                    index_string += unparse(index.stop)
                index_string += ':'
                if index.step:
                    index_string += unparse(index.step)
            else:
                index_string += unparse(index)

            indices.append(index_string)

        string += indices[0] + ',' if len(indices) == 1 else ', '.join(indices)

    else:
        string += unparse(node.slice)

    string += ']'

    return string

def visit_CallNode(node):
    arguments = []

    for argument in node.arguments:
        if isinstance(argument, tuple):
            keyword, argument = argument
            arguments.append(f'{identifier(keyword.value)}={unparse(argument)}')
        else:
            arguments.append(unparse(argument))

    return f'{unparse(node.target)}({", ".join(arguments)})'

def visit_ChainOperatorNode(node):
    string = unparse(node.expressions[0])

    for i, operand in enumerate(node.operations, start=1):
        string += ' '

        if operand.match(TOKENS['KEYWORD'], 'in'):
            string += 'in'
        elif operand.match(TOKENS['KEYWORD'], 'is'):
            string += 'is'
        else:
            string += SYMBOLS_TOKEN_MAP[operand.type]

        string += ' '
        string += unparse(node.expressions[i])

    return f'({string})'

def visit_TernaryOperatorNode(node):
    return f'({unparse(node.condition)} ? {unparse(node.valid)} : {unparse(node.invalid)})'

def visit_BinaryOperatorNode(node):
    if node.operand.match(TOKENS['KEYWORD'], 'and'):
        operand = 'and'
    elif node.operand.match(TOKENS['KEYWORD'], 'or'):
        operand = 'or'
    else:
        operand = SYMBOLS_TOKEN_MAP[node.operand.type]

    return f'({unparse(node.left)} {operand} {unparse(node.right)})'

def visit_UnaryOperatorNode(node):
    if node.operand.match(TOKENS['KEYWORD'], 'not'):
        operand = 'not '
    elif node.operand.match(TOKENS['KEYWORD'], 'typeof'):
        operand = 'typeof '
    else:
        operand = SYMBOLS_TOKEN_MAP[node.operand.type]

    return f'({operand}{unparse(node.value)})'

def visit_IncrementalNode(node):
    operand = SYMBOLS_TOKEN_MAP[node.operand.type]
    target = unparse(node.target)
    return '(' + (operand + target if node.operand_position == 'left' else target + operand) + ')'

def visit_StatementsNode(node):
    return '\n'.join(map(unparse, node.body))

def visit_AssignNode(node):
    return f'{unparse(node.target)} {SYMBOLS_TOKEN_MAP[node.operand.type]} {unparse(node.value)}'

def visit_ImportNode(node):
    string = ''

    name, as_name = node.name
    name_string = identifier(name.value) if name.type == TOKENS['IDENTIFIER'] else repr(name.value)

    if as_name:
        name_string += ' as '
        name_string += identifier(as_name.value)

    if node.packages == 'all':
        string += 'from '
        string += identifier(name_string)
        string += ' import *'

    elif node.packages:
        packages = []

        for package, as_package in node.packages:
            package_string = identifier(package.value)

            if as_package:
                package_string += ' as '
                package_string += identifier(as_package.value)

            packages.append(package_string)

        string += 'from '
        string += name_string
        string += ' import '
        string += ', '.join(packages)

    else:
        string += 'import '
        string += name_string

    return string

def visit_IfNode(node):
    cases = []

    for i, (condition, body) in enumerate(node.cases_body):
        case_string = 'if' if i == 0 else 'elif'
        case_string += ' ('
        case_string += unparse(condition)
        case_string += ') {\n'
        case_string += indent(unparse(body))
        case_string += '\n}'

        cases.append(case_string)

    string = '\n'.join(cases)

    if node.else_body:
        string += '\nelse {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    return string

def visit_SwitchNode(node):
    cases = []

    for condition, body in node.case_cases:
        case_string = 'case '
        case_string += unparse(condition)
        case_string += ':\n'
        case_string += indent(unparse(body))

        cases.append(case_string)

    if node.default_body:
        default_string = 'default:\n'
        default_string += indent(unparse(node.default_body))

        cases.append(default_string)

    string = 'switch ('
    string += unparse(node.target)
    string += ') {\n'
    string += '\n'.join(map(indent, cases))
    string += '\n}'

    return string

def visit_MatchNode(node):
    string = 'match '

    if node.target:
        string += '('
        string += unparse(node.target)
        string += ') '

    cases = []

    for condition, value in node.cases:
        case_string = unparse(condition)
        case_string += ': '
        case_string += unparse(value)

        cases.append(case_string)

    if node.default:
        default_string = 'default: '
        default_string += unparse(node.default)

        cases.append(default_string)

    string += '{\n'
    string += indent(',\n'.join(cases))
    string += '\n}'

    return string

def visit_TryNode(node):
    catch_cases = []

    for (targets, parameter), body in node.catch_cases:
        name_string = ''

        if not (not targets and parameter is None):
            name_string += ' ('

            if targets:
                name_string += ', '.join(identifier(target.name.value) for target in targets)
                name_string += ' '

            name_string += identifier(parameter.value)
            name_string += ')'

        catch_string = 'catch'
        catch_string += name_string
        catch_string += ' {\n'
        catch_string += indent(unparse(body))
        catch_string += '\n}'

        catch_cases.append(catch_string)

    string = 'try {\n'
    string += indent(unparse(node.body))
    string += '\n}\n'
    string += '\n'.join(catch_cases)

    if catch_cases:
        string += '\n'

    if node.else_body:
        string += 'else {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    if node.finally_body:
        string += 'finally {\n'
        string += indent(unparse(node.finally_body))
        string += '\n}'

    return string

def visit_WithNode(node):
    contexts = []

    for context, alias in node.contexts:
        context_string = unparse(context)

        if alias:
            context_string += ' as '
            context_string += identifier(alias.value)

        contexts.append(context_string)

    string = 'with ('
    string += ', '.join(contexts)
    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_ForNode(node):
    string = 'for ('

    if len(node.header) == 2:
        declaration, iteration = node.header

        string += unparse(declaration)
        string += ' of '
        string += unparse(iteration)

    elif len(node.header) == 3:
        declaration, condition, update = node.header

        if declaration:
            string += unparse(declaration)
        string += ';'
        if condition:
            string += unparse(condition)
        string += ';'
        if update:
            string += unparse(update)

    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    if node.else_body:
        string += '\nelse {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    return string

def visit_WhileNode(node):
    string = 'while ('
    string += unparse(node.condition)
    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    if node.else_body:
        string += '\nelse {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    return string

def visit_DoWhileNode(node):
    string = 'do {\n'
    string += indent(unparse(node.body))
    string += '\n} while ('
    string += unparse(node.condition)
    string += ')'

    if node.else_body:
        string += 'else {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    return string

def visit_RepeatNode(node):
    string = 'repeat {\n'
    string += indent(unparse(node.body))
    string += '\n} until ('
    string += unparse(node.condition)
    string += ')'

    if node.else_body:
        string += 'else {\n'
        string += indent(unparse(node.else_body))
        string += '\n}'

    return string

def visit_ClassNode(node):
    bases = []
    decorators = []

    for decorator in node.decorators:
        decorators.append(f'@{unparse(decorator)}')

    for base in node.bases:
        bases.append(unparse(base))

    string = ''

    if decorators:
        string += '\n'.join(decorators)
        string += '\n'

    string += 'class '
    string += identifier(node.name.value)

    if bases:
        string += '('
        string += ', '.join(bases)
        string += ')'

    string += ' {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_FunctionNode(node):
    decorators = []
    parameters = []

    for decorator in node.decorators:
        decorators.append(f'@{unparse(decorator)}')

    for parameter in node.parameters:
        if isinstance(parameter, tuple):
            parameter, value = parameter
            parameters.append(f'{identifier(parameter.value)}={unparse(value)}')
        else:
            parameters.append(parameter.value)

    string = ''

    if decorators:
        string += '\n'.join(decorators)
        string += '\n'

    if node.constructor:
        string += 'constructor'
    else:
        string += 'func'
        if node.name:
            string += ' '
            string += identifier(node.name.value)

    string += '('
    string += ', '.join(parameters)
    string += ') {\n'
    string += indent(unparse(node.body))
    string += '\n}'

    return string

def visit_GlobalNode(node):
    string = 'global '
    string += ', '.join(identifier(name.value) for name in node.identifiers)
    return string

def visit_ReturnNode(node):
    string = 'return'

    if node.value:
        string += ' '
        string += unparse(node.value)

    return string

def visit_ThrowNode(node):
    string = 'throw '
    string += unparse(node.target)

    if node.cause:
        string += ' from '
        string += unparse(node.cause)

    return string

def visit_AssertNode(node):
    string = 'assert '
    string += unparse(node.condition)

    if node.message:
        string += ', '
        string += unparse(node.message)

    return string

def visit_DeleteNode(node):
    string = 'del '
    string += ', '.join(map(unparse, node.targets))
    return string

def visit_EllipsisNode(node):
    return '...'

def visit_ContinueNode(node):
    return 'continue'

def visit_BreakNode(node):
    return 'break'

get_visitor = {
    class_node: globals()['visit_' + class_node.__name__.removeprefix('Pys')]
    for class_node in PysNode.__subclasses__()
}.__getitem__