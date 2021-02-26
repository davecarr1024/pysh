from __future__ import annotations
import lexer, parser, syntax, util
from typing import Dict, Optional, Sequence, Tuple

def lexer_rule(s: str)->lexer.Rule:
  operators = {'*','+','(',')','|','^','?'}
  reserved_operators = operators | {'[',']','\\'}
  class_pairs = {('a','z'),('A','Z'),('0','9')}
  lexer_rules: Dict[str, lexer.Rule] = {operator: lexer.Literal(operator) for operator in operators}
  lexer_rules.update({
    'class': lexer.Or(*[lexer.Literal('[%s-%s]' % class_pair) for class_pair in class_pairs]),
    'any': lexer.take_while(lambda s: s not in reserved_operators),
    'literal': lexer.Or(*[lexer.Literal('\\%s' % operator) for operator in reserved_operators]),
  })
  toks = lexer.Lexer(lexer_rules, {}).apply(s)

  node = parser.Parser({
    'rule': parser.or_(
      parser.ref('operand'),
      parser.ref('or'),
      parser.ref('and'),
    ),
    'unary_operation': parser.or_(
      parser.ref('zero_or_more'),
      parser.ref('one_or_more'),
      parser.ref('zero_or_one'),
      parser.ref('not'),
    ),
    'zero_or_more': parser.and_(
      parser.ref('unary_operand'),
      parser.literal('*'),
    ),
    'one_or_more': parser.and_(
      parser.ref('unary_operand'),
      parser.literal('+'),
    ),
    'zero_or_one': parser.and_(
      parser.ref('unary_operand'),
      parser.literal('?'),
    ),
    'not': parser.and_(
      parser.literal('^'),
      parser.ref('unary_operand'),
    ),
    'unary_operand': parser.or_(
      parser.literal('class'),
      parser.literal('any'),
      parser.literal('literal'),
      parser.ref('paren_rule'),
    ),
    'paren_rule': parser.and_(
      parser.literal('('),
      parser.ref('rule'),
      parser.literal(')'),
    ),
    'or': parser.and_(
      parser.ref('operand'),
      parser.one_or_more(
        parser.and_(
          parser.literal('|'),
          parser.ref('operand'),
        ),
      ),
    ),
    'and': parser.and_(
      parser.ref('operand'),
      parser.one_or_more(
        parser.ref('operand'),
      ),
    ),
    'operand': parser.or_(
      parser.ref('unary_operand'),
      parser.ref('unary_operation'),
    ),
  }, 'rule').apply(toks)

  class Class:
    def __init__(self, val: str):
      self.low, self.high = val.strip('[]').split('-')

    def __repr__(self)->str:
      return '[%s-%s]' % (self.low, self.high)

    def __call__(self, s: str)->Optional[str]:
      return s[0] if s and self.low <= s[0] <= self.high else None

  return syntax.Syntax({
    syntax.terminal('class', Class),
    syntax.terminal('any', lexer.Literal),
    syntax.terminal('literal', lambda val: lexer.Literal(val[1:])),
    syntax.unary('zero_or_more', lexer.ZeroOrMore),
    syntax.unary('one_or_more', lexer.OneOrMore),
    syntax.unary('zero_or_one', lexer.ZeroOrOne),
    syntax.unary('not', lexer.Not),
    syntax.variadic('and', lambda rules: lexer.And(*rules)),
    syntax.variadic('or', lambda rules: lexer.Or(*rules)),
  }).apply(node)

def lexer_and_parser(s: str)->Tuple[lexer.Lexer, parser.Parser]:
  operators = {'=','~=',';','->'}
  lexer_rules: Dict[str, lexer.Rule] = {operator: lexer.Literal(operator) for operator in operators}
  lexer_rules.update({
    'id': lexer_rule('([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*'),
    'lexer_def': lexer_rule('"(^")*"'),
  })
  toks = lexer.Lexer(lexer_rules, 
  {
    'ws': lexer.take_while(str.isspace),
  }).apply(s)

  node = parser.Parser({
    'lines': parser.one_or_more(
      parser.or_(
        parser.ref('lexer_rule'),
        parser.ref('silent_lexer_rule'),
        parser.ref('rule_decl'),
      )
    ),
    'lexer_rule': parser.and_(
      parser.literal('id'),
      parser.literal('='),
      parser.literal('lexer_def'),
      parser.literal(';'),
    ),
    'silent_lexer_rule': parser.and_(
      parser.literal('id'),
      parser.literal('~='),
      parser.literal('lexer_def'),
      parser.literal(';'),
    ),
    'rule_decl': parser.and_(
      parser.literal('id'),
      parser.literal('->'),
      parser.ref('rule'),
      parser.literal(';'),
    ),
    'rule': parser.or_(
      parser.literal('id'),
    ),
  }, 'lines').apply(toks)

  l = lexer.Lexer({},{})
  p = parser.Parser({}, '')

  def tok_val(node: parser.Node)->str:
    assert node.tok
    return node.tok.val

  def lexer_rule_(node: parser.Node, exprs: Sequence[parser.Rule])->Optional[parser.Rule]:
    if node.rule_name == 'lexer_rule':
      l.rules[tok_val(node.unary_descendants('id'))] = lexer_rule(tok_val(node.unary_descendants('lexer_def')).strip('"'))
    if node.rule_name == 'silent_lexer_rule':
      l.silent_rules[tok_val(node.unary_descendants('id'))] = lexer_rule(tok_val(node.unary_descendants('lexer_def')).strip('"'))
    return None

  def rule_decl(rule: parser.Rule)->Optional[parser.Rule]:
    if not p.root:
      name = 
      p.root = rule.

  syntax.Syntax({
    lexer_rule_,
  }).apply_many(node)

  return l, p

def test(): 
  for rule_str, i, o in [
    ('[a-z]','pA','p'),
    ('[0-9]', '3', '3'),
    ('[0-9]', 'a', None),
    ('[a-z]*', 'abcd0', 'abcd'),
    ('[a-z][A-Z]*', 'bA0', 'bA'),
    ('([a-z][A-Z])*', 'aBcD123', 'aBcD'),
    ('[a-z]+', 'abc0', 'abc'),
    ('[a-z]+', '123', None),
    ('abc', 'abc', 'abc'),
    ('(a|[0-9])+', 'a3ab', 'a3a'),
    ('(a|[0-9])+', 'b', None),
    ('"(^")*"', '"foo"', '"foo"'),
    ('a(^a)*a', 'abc', None),
    ('\[', '[a', '['),
    ('\[', ']', None),
    ('a?', 'a', 'a'),
    ('[0-9]+', '20', '20'),
    ('-?', '-', '-'),
    ('-?', '', ''),
    ('-?[0-9]+', '-20', '-20'),
    ('-?[0-9]+', '20', '20'),
    ('-?[0-9]+', 'abc', None),
    ('([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*', '_a1D_', '_a1D_'),
  ]:
    util.test(lexer_rule(rule_str), i, o)
    
  for s, cases in [
    (r'''
      id = "([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*";
      ws ~= " +";
      expr -> id;
    ''', [
      ('abc', None),
    ]),
  ]:
    lexer, parser = lexer_and_parser(s)
    def test(i: str)->parser.node:
      toks = lexer.apply(i)
      print('test', i, toks)
      return parser.apply(toks)
    util.test_cases(test, cases)
