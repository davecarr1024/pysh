from __future__ import annotations
from abc import ABC, abstractmethod
import lexer
from typing import Callable, Dict, List, Optional, Set, Sequence, Tuple

class Node:
  def __init__(self, tok: Optional[lexer.Token] = None, children: Optional[Sequence[Node]] = None, rule_name: Optional[str] = None):
    self.tok = tok
    self.children = children or []
    self.rule_name = rule_name

  def __eq__(self, rhs: object)->bool:
    assert isinstance(rhs, Node)
    if self.tok == rhs.tok and self.children == rhs.children and self.rule_name == rhs.rule_name:
      return True
    else:
      print('neq', self, rhs)
      return False

  def __hash__(self)->int:
    return hash((self.tok,tuple(self.children),self.rule_name))

  def __len__(self)->int:
    return (1 if self.tok else 0) + sum(map(len,self.children))

  def __repr__(self)->str:
    return 'Node(%s)' % ', '.join(['%s=%s' % (name, repr(val)) for name, val in [(name, getattr(self, name)) for name in dir(self) if not name.startswith('_')] if val and not callable(val)])

  def variadic_descendants(self, rule_name: str)->Sequence[Node]:
    return sum([child.variadic_descendants(rule_name) for child in self.children], [self] if self.rule_name == rule_name else [])

  def nary_descendants(self, rule_name: str, n: int)->Sequence[Node]:
    descendants = self.variadic_descendants(rule_name)
    assert len(descendants) == n
    return descendants

  def binary_descendants(self, rule_name)->Tuple[Node, Node]:
    descendants = self.nary_descendants(rule_name, 2)
    return descendants[0], descendants[1]

  def unary_descendants(self, rule_name)->Node:
    return self.nary_descendants(rule_name, 1)[0]

class IParser(ABC):
  @abstractmethod
  def apply_rule(self, rule_name: str, toks: Sequence[lexer.Token])->Set[Node]: pass

Rule = Callable[[IParser,Sequence[lexer.Token]],Set[Node]]

def literal(val: str)->Rule:
  return lambda parser, toks: {Node(tok=toks[0], rule_name=val)} if toks and toks[0].rule_name == val else set()

def ref(val: str)->Rule:
  return lambda parser, toks: {Node(rule_name=val, children=[node]) for node in parser.apply_rule(val, toks)}

def and_(rule: Rule, *rest_rules: Rule)->Rule:
  rules = [rule] + list(rest_rules)
  def _impl(parser: IParser, toks: Sequence[lexer.Token])->Set[Node]:
    def iter(rules: Sequence[Rule], toks: Sequence[lexer.Token])->List[List[Node]]:
      return [[node] for node in rules[0](parser, toks)] if len(rules) == 1 else [[node] + rest for node in rules[0](parser, toks) for rest in iter(rules[1:], toks[len(node):])]
    return {Node(children=nodes) for nodes in iter(rules, toks)}
  return _impl

def or_(*rules: Rule)->Rule:
  return lambda parser, toks: set.union(set(),*[{Node(children=[node])} for rule in rules for node in rule(parser, toks)])

def zero_or_more(rule: Rule)->Rule:
  def _impl(parser: IParser, toks: Sequence[lexer.Token])->Set[Node]:
    def iter(toks: Sequence[lexer.Token])->List[List[Node]]:
      nodes = rule(parser, toks)
      return [[node] + rest for node in nodes for rest in iter(toks[len(node):])] if nodes else [[]]
    nodess = iter(toks)
    return {Node(children=nodes) for nodes in nodess} if nodess else {Node()}
  return _impl

def one_or_more(rule: Rule)->Rule:
  def _impl(parser: IParser, toks: Sequence[lexer.Token])->Set[Node]:
    def iter(toks: Sequence[lexer.Token])->List[List[Node]]:
      nodes = rule(parser, toks)
      return [[node] + rest for node in nodes for rest in iter(toks[len(node):])] if nodes else [[]]
    return {Node(children=[node]+rest) for node in rule(parser, toks) for rest in iter(toks[len(node):])}
  return _impl

def zero_or_one(rule: Rule)->Rule:
  def _impl(parser: IParser, toks: Sequence[lexer.Token])->Set[Node]:
    nodes = rule(parser, toks)
    return {Node(children=[node]) for node in nodes} if nodes else {Node()}
  return _impl

class Parser(IParser):
  def __init__(self, rules: Dict[str, Rule], root: str):
    self.rules = rules
    self.root = root

  def apply_rule(self, rule_name: str, toks: Sequence[lexer.Token])->Set[Node]:
    assert rule_name in self.rules, 'unknown rule %s' % repr(rule_name)
    return self.rules[rule_name](self, toks)

  def apply(self, toks: Sequence[lexer.Token])->Node:
    nodes = {node for node in ref(self.root)(self, toks) if len(node) == len(toks)}
    assert nodes, 'parse error in %s' % toks
    return list(nodes)[0]

def test():
  def literal_node(rule_name: str, val: str)->Node:
    return Node(tok=lexer.Token(rule_name, val),rule_name=rule_name)
  assert literal('id')(Parser({},''),[lexer.Token('id','a')]) == {literal_node('id','a')}
  assert ref('idref')(Parser({'idref':literal('id')},''),[lexer.Token('id','a')]) == {Node(rule_name='idref',children=[literal_node('id','a')])}
  assert and_(literal('id'),literal('id'))(Parser({},''),[lexer.Token('id','a'),lexer.Token('id','b')]) == {Node(children=[literal_node('id','a'),literal_node('id','b')])}
  assert and_(literal('id'),literal('id'))(Parser({},''),[lexer.Token('id','a'),lexer.Token('notid','b')]) == set()
  assert zero_or_more(literal('id'))(Parser({},''),[lexer.Token('id','a'),lexer.Token('id','b')]) == {Node(children=[literal_node('id','a'),literal_node('id','b')])}, nodes
  assert zero_or_more(literal('id'))(Parser({},''),[lexer.Token('notid','a')]) == {Node()}
  val = one_or_more(literal('id'))(Parser({},''),[lexer.Token('id','a'),lexer.Token('id','b')])
  assert val == {Node(children=[literal_node('id','a'),literal_node('id','b')])}, val
  assert one_or_more(literal('id'))(Parser({},''),[]) == set()
  assert zero_or_one(literal('id'))(Parser({},''),[lexer.Token('id','a')]) == {Node(children=[literal_node('id','a')])}
  assert zero_or_one(literal('id'))(Parser({},''),[lexer.Token('notid','a')]) == {Node()}
