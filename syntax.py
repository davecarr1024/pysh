from __future__ import annotations
import parser
from typing import Callable, Generic, MutableSequence, Optional, Sequence, Set, TypeVar

Expr = TypeVar('Expr')
Rule = Callable[[parser.Node, Sequence[Expr]], Optional[Expr]]


def rule_name(rule_name: str, rule: Rule) -> Rule:
    return lambda node, exprs: rule(node, exprs) if (node.rule_name == rule_name or (node.token and node.token.rule_name == rule_name)) else None


def nary(n: int, rule: Rule) -> Rule:
    return lambda node, exprs: rule(node, exprs) if len(exprs) == n else None


def binary(factory: Callable[[Expr, Expr], Optional[Expr]]) -> Rule:
    return nary(2, lambda node, exprs: factory(exprs[0], exprs[1]))


def unary(factory: Callable[[Expr], Optional[Expr]]) -> Rule:
    return nary(1, lambda node, exprs: factory(exprs[0]))


def terminal(factory: Callable[[str], Optional[Expr]]) -> Rule:
    return lambda node, exprs: factory(node.token.val) if node.token else None


class Syntax(Generic[Expr]):
    def __init__(self, *rules: Rule):
        self.rules = rules

    def __call__(self, node: parser.Node) -> Sequence[Expr]:
        child_exprs: MutableSequence[Expr] = []
        for child_node in node.children:
            child_exprs.extend(self(child_node))
        exprs = [expr for expr in [rule(node, child_exprs)
                                   for rule in self.rules] if expr]
        assert len(exprs) <= 1, 'syntax error %s' % exprs
        return [exprs[0]] if exprs else child_exprs


SubExpr = TypeVar('SubExpr')
def sub_syntax(syntax: Syntax[SubExpr], factory: Callable[[parser.Node, Sequence[SubExpr]], Optional[Expr]]) -> Rule:
    return lambda node, exprs: factory(node, syntax(node))


def aggregate_token_vals(node: parser.Node, exprs: Sequence[Expr]) -> Optional[str]:
    return node.token.val if node.token else None


def token_vals(rule_name: str, factory: Callable[[Sequence[str]], Optional[Expr]]) -> Rule:
    def impl(node: parser.Node, exprs: Sequence[Expr]) -> Optional[Expr]:
        return factory(Syntax(lambda node, exprs: node.token.val if node.token and node.token.rule_name == rule_name else None)(node))
    return impl


def get_token_vals(token_rule_name: str)->Syntax[str]:
    return Syntax(rule_name(token_rule_name, aggregate_token_vals))