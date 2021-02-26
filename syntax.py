from __future__ import annotations
import lexer, parser
from typing import Callable, List, NamedTuple, Optional, Sequence, Set, TypeVar

Expr = TypeVar('Expr')
Rule=Callable[[parser.Node, Sequence[Expr]], Optional[Expr]]

def variadic(rule_name: str, factory: Callable[[Sequence[Expr]],Optional[Expr]])->Rule:
    return lambda node, exprs: factory(exprs) if node.rule_name == rule_name else None
 
def nary(rule_name: str, n: int, factory: Callable[[Sequence[Expr]],Optional[Expr]])->Rule:
  return variadic(rule_name, lambda exprs: factory(exprs) if len(exprs) == n else None)

def unary(rule_name: str, factory: Callable[[Expr],Optional[Expr]])->Rule:
  return nary(rule_name, 1, lambda exprs: factory(exprs[0]))

def binary(rule_name: str, factory: Callable[[Expr,Expr],Optional[Expr]])->Rule:
  return nary(rule_name, 2, lambda exprs: factory(exprs[0],exprs[1]))

def terminal(rule_name: str, factory: Callable[[str],Optional[Expr]])->Rule:
  return lambda node, exprs: factory(node.tok.val) if node.rule_name == rule_name and node.tok else None

def variadic_descendants(rule_name: str, child_rule_name: str, factory: Callable[[Sequence[parser.Node]],Optional[Expr]])->Rule:
  return lambda node, exprs: factory(node.variadic_descendants(child_rule_name)) if node.rule_name == rule_name else None

def nary_descendants(rule_name: str, child_rule_name: str, n: int, factory: Callable[[Sequence[parser.Node]],Optional[Expr]])->Rule:
  return variadic_descendants(rule_name, child_rule_name, lambda nodes: factory(nodes) if len(nodes) == n else None)

def unary_descendants(rule_name: str, child_rule_name: str, factory: Callable[[parser.Node],Optional[Expr]])->Rule:
  return nary_descendants(rule_name, child_rule_name, 1, lambda exprs: factory(exprs[0]))

def binary_descendants(rule_name: str, child_rule_name: str, factory: Callable[[parser.Node,parser.Node],Optional[Expr]])->Rule:
  return nary_descendants(rule_name, child_rule_name, 2, lambda exprs: factory(exprs[0], exprs[1]))

class Syntax:
  def __init__(self, rules: Set[Rule]):
    self.rules = rules

  def apply_many(self, node: parser.Node)->Sequence[Expr]:
    child_exprs: List[Expr] = []
    for child_node in node.children:
      child_exprs.extend(self.apply_many(child_node))
    exprs = [expr for expr in {rule(node, child_exprs) for rule in self.rules} if expr]
    assert len(exprs) <= 1, 'syntax error'
    return [exprs[0]] if exprs else child_exprs

  def apply(self, node: parser.Node)->Expr:
    exprs: Sequence[Expr] = self.apply_many(node)
    assert len(exprs) == 1, 'syntax error'
    return exprs[0]

class _IntExpr(NamedTuple):
  val: int
class _OperandExpr(NamedTuple):
  expr: _IntExpr
class _AddExpr(NamedTuple):
  lhs: _OperandExpr
  rhs: _OperandExpr
def test():
  assert Syntax({
    terminal('int', lambda val: _IntExpr(int(val))),
    unary('operand', _OperandExpr),
    binary('add', _AddExpr)
  }).apply(parser.Node(rule_name='add',children=[
    parser.Node(rule_name='other_rule',children=[parser.Node(rule_name='operand',children=[parser.Node(rule_name='int',tok=lexer.Token('int','1'))])]),
    parser.Node(rule_name='operand',children=[parser.Node(rule_name='int',tok=lexer.Token('int','2'))]),
  ])) == _AddExpr(lhs=_OperandExpr(expr=_IntExpr(val=1)), rhs=_OperandExpr(expr=_IntExpr(val=2)))