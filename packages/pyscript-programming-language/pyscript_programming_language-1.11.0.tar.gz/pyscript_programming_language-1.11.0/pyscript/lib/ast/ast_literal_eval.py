from pyscript.core.constants import TOKENS
from pyscript.core.interpreter import get_value_from_keyword
from pyscript.core.mapping import BINARY_FUNCTIONS_MAP, UNARY_FUNCTIONS_MAP, REVERSE_TOKENS
from pyscript.core.nodes import PysNode, PysIdentifierNode
from pyscript.core.pysbuiltins import pys_builtins

is_arith = frozenset([TOKENS['PLUS'], TOKENS['MINUS']]).__contains__

inf = pys_builtins.inf
nan = pys_builtins.nan

get_identifier = {
    'ellipsis': Ellipsis,
    'Ellipsis': Ellipsis,
    'inf': inf,
    'infinity': inf,
    'Infinity': inf,
    'nan': nan,
    'notanumber': nan,
    'NaN': nan,
    'NotANumber': nan
}.get

def visit(node):
    return get_visitor(node.__class__)(node)

def visit_unknown_node(node):
    raise ValueError(f"invalid node: {type(node).__name__}")

def visit_NumberNode(node):
    return node.value.value

def visit_StringNode(node):
    return node.value.value

def visit_KeywordNode(node):
    if (name := node.name.value) == '__debug__':
        raise ValueError("invalid constant keyword for __debug__")
    #      vvvvvvvvvvvvvvvvvvvvvvvvvvvv <- always boolean or none
    return get_value_from_keyword(name)

def visit_IdentifierNode(node):
    if (value := get_identifier(name := node.name.value, None)) is None:
        raise ValueError(f"invalid identifier: {name}")
    return value

def visit_DictionaryNode(node):
    return {visit(key): visit(value) for key, value in node.pairs}

def visit_SetNode(node):
    return set(map(visit, node.elements))

def visit_ListNode(node):
    return list(map(visit, node.elements))

def visit_TupleNode(node):
    return tuple(map(visit, node.elements))

def visit_CallNode(node):
    if isinstance(target := node.target, PysIdentifierNode) and target.name.value == 'set' and not node.arguments:
        return set()
    raise ValueError("invalid call except for 'set()'")

def visit_UnaryOperatorNode(node):
    if is_arith(operand := node.operand.type):
        return UNARY_FUNCTIONS_MAP(operand)(visit(node.value))
    raise ValueError(f"invalid unary operand: {REVERSE_TOKENS[operand]}")

def visit_BinaryOperatorNode(node):
    if is_arith(operand := node.operand.type):
        return BINARY_FUNCTIONS_MAP(operand)(visit(node.left), visit(node.right))
    raise ValueError(f"invalid binary operand: {REVERSE_TOKENS[operand]}")

def visit_EllipsisNode(node):
    return ...

get_visitor = {
    class_node: globals().get('visit_' + class_node.__name__.removeprefix('Pys'), visit_unknown_node)
    for class_node in PysNode.__subclasses__()
}.__getitem__