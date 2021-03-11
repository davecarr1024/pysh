from __future__ import annotations
import parser
from typing import Callable, List, Optional, Sequence, Set, TypeVar

Expr = TypeVar('Expr')
Rule = Callable[[parser.Node, Sequence[Expr]], Optional[Expr]]


def rule_name(rule_name: str, rule: Rule) -> Rule:
    return lambda node, exprs: rule(node, exprs) if node.rule_name == rule_name else None


def nary(n: int, rule: Rule) -> Rule:
    return lambda node, exprs: rule(node, exprs) if len(exprs) == n else None


def binary(factory: Callable[[Expr, Expr], Optional[Expr]]) -> Rule:
    return nary(2, lambda node, exprs: factory(exprs[0], exprs[1]))


def unary(factory: Callable[[Expr], Optional[Expr]]) -> Rule:
    return nary(1, lambda node, exprs: factory(exprs[0]))


def terminal(factory: Callable[[str], Optional[Expr]]) -> Rule:
    return lambda node, exprs: factory(node.token.val) if node.token else None


class Syntax:
    def __init__(self, rules: Set[Rule]):
        self.rules = rules

    def __call__(self, node: parser.Node) -> Sequence[Expr]:
        child_exprs: List[Expr] = []
        for child_node in node.children:
            child_exprs.extend(self(child_node))
        exprs = [expr for expr in [rule(node, child_exprs)
                                   for rule in self.rules] if expr]
        assert len(exprs) <= 1, 'syntax error %s' % exprs
        return [exprs[0]] if exprs else child_exprs
