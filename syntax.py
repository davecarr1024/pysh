from __future__ import annotations
import parser
from typing import Callable, List, Optional, Sequence, Set, TypeVar

Expr = TypeVar('Expr')
Rule = Callable[[parser.Node, Sequence[Expr]], Optional[Expr]]


def variadic(
    rule_name: str,
    factory: Callable[[Sequence[Expr]], Optional[Expr]],
) -> Rule:
    def impl(node: parser.Node, exprs: Sequence[Expr]) -> Optional[Expr]:
        return factory(exprs) if node.rule_name == rule_name else None
    return impl


def nary(
    rule_name: str,
    n: int,
    factory: Callable[[Sequence[Expr]], Optional[Expr]],
) -> Rule:
    return variadic(
        rule_name,
        lambda exprs: factory(exprs) if len(exprs) == n else None
    )


def unary(rule_name: str, factory: Callable[[Expr], Optional[Expr]]) -> Rule:
    return nary(rule_name, 1, lambda exprs: factory(exprs[0]))


def binary(
    rule_name: str,
    factory: Callable[[Expr, Expr],
                      Optional[Expr]],
) -> Rule:
    return nary(rule_name, 2, lambda exprs: factory(exprs[0], exprs[1]))


def terminal(rule_name: str, factory: Callable[[str], Optional[Expr]]) -> Rule:
    def impl(node: parser.Node, exprs: Sequence[Expr]) -> Optional[Expr]:
        if node.rule_name == rule_name and node.tok:
            return factory(node.tok.val)
        else:
            return None
    return impl


def node(
    rule_name: str,
    factory: Callable[[parser.Node], Optional[Expr]],
) -> Rule:
    def impl(node: parser.Node, exprs: Sequence[Expr]) -> Optional[Expr]:
        return factory(node) if node.rule_name == rule_name else None
    return impl


class Syntax:
    def __init__(self, rules: Set[Rule]):
        self.rules = rules

    def apply_many(self, node: parser.Node) -> Sequence[Expr]:
        child_exprs: List[Expr] = []
        for child_node in node.children:
            child_exprs.extend(self.apply_many(child_node))
        exprs = [expr for expr in [rule(node, child_exprs)
                                   for rule in self.rules] if expr]
        assert len(exprs) <= 1, 'syntax error'
        return [exprs[0]] if exprs else child_exprs

    def __call__(self, node: parser.Node) -> Expr:
        exprs: Sequence[Expr] = self.apply_many(node)
        assert len(exprs) == 1, 'syntax error'
        return exprs[0]
