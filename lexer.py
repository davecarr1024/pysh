from __future__ import annotations
import itertools
import util
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence

class Token(NamedTuple):
  rule_name: str
  val: str

Rule = Callable[[str],Optional[str]]

def _apply_rule_from(rule_name: str, s: str, rules: Dict[str,Rule])->Optional[Token]:
  val = rules[rule_name](s)
  return Token(rule_name, val) if val is not None else None

def _apply_all_from(s: str, rules: Dict[str,Rule])->List[Token]:
  return [tok for tok in [_apply_rule_from(rule_name, s, rules) for rule_name in rules.keys()] if tok]

def take_while(pred: Callable[[str],bool])->Rule:
  def impl(s: str)->Optional[str]:
    val = ''.join(itertools.takewhile(pred, s))
    return val if val else None
  return impl

class Literal:
  def __init__(self, val: str):
    self.val = val

  def __repr__(self)->str:
    return self.val

  def __call__(self, s: str)->Optional[str]:
    return self.val if s.startswith(self.val) else None

class ZeroOrMore:
  def __init__(self, rule: Rule):
    self.rule = rule

  def __repr__(self)->str:
    return '%s*' % self.rule

  def __call__(self, s: str)->Optional[str]:
    r = ''
    while True:
      v = self.rule(s[len(r):])
      if not v:
        return r
      r += v

class OneOrMore:
  def __init__(self, rule: Rule):
    self.rule = rule

  def __repr__(self)->str:
    return '%s+' % self.rule

  def __call__(self, s: str)->Optional[str]:
    v = self.rule(s)
    if v is None:
      return None
    r = v
    while True:
      v = self.rule(s[len(r):])
      if not v:
        return r
      r += v

class ZeroOrOne:
  def __init__(self, rule: Rule):
    self.rule = rule

  def __repr__(self)->str:
    return '%s?' % self.rule

  def __call__(self, s: str)->Optional[str]:
    v = self.rule(s)
    return v if v else ''

class And:
  def __init__(self, *rules: Rule):
    self.rules = rules

  def __repr__(self)->str:
    return '(%s)' % ''.join(map(str, self.rules))

  def __call__(self, s: str)->Optional[str]:
    r = ''
    for rule in self.rules:
      v = rule(s[len(r):])
      if v is None:
        return None
      r += v
    return r

class Or:
  def __init__(self, *rules: Rule):
    self.rules = rules

  def __repr__(self)->str:
    return '(%s)' % '|'.join(map(str, self.rules))

  def __call__(self, s: str)->Optional[str]:
    vals = [val for val in [rule(s) for rule in self.rules] if val is not None]
    assert len(vals) <= 1, 'ambiguous or %s' % vals
    return vals[0] if vals else None

class Not:
  def __init__(self, rule: Rule):
    self.rule = rule

  def __repr__(self)->str:
    return '^%s' % self.rule

  def __call__(self, s: str)->Optional[str]:
    return s[0] if s and self.rule(s) is None else None

class Lexer:
  def __init__(self, rules: Dict[str,Rule], silent_rules: Dict[str,Rule]):
    self.rules = rules
    self.silent_rules = silent_rules

  def __repr__(self)->str:
    return 'Lexer(%s, %s)' % (self.rules, self.silent_rules)

  def apply(self, s: str)->Sequence[Token]:
    toks: List[Token] = []
    pos = 0
    while pos < len(s):
      rule_toks = _apply_all_from(s[pos:], self.rules)
      silent_rule_toks = _apply_all_from(s[pos:], self.silent_rules)
      assert rule_toks or silent_rule_toks, 'lex error at %d: %s' % (pos, s[pos:min(pos+10,len(s))])
      assert len(rule_toks) + len(silent_rule_toks) == 1, 'lex error at %d: %s ambiguous results: %s' % (pos, s[pos:min(pos+10,len(s))], rule_toks + silent_rule_toks)
      if rule_toks:
        tok = rule_toks[0]
        toks.append(tok)
      else:
        tok = silent_rule_toks[0]
      pos += len(tok.val)
    return toks

def test():
  util.test(Lexer({'id': take_while(str.isalpha),'[': Literal('[')},{'ws': take_while(str.isspace)}).apply, ' [ a b ', [Token('[','['), Token('id','a'), Token('id','b')])
  util.test_cases(Literal('['),[('[a]','['),('a',None)])
  util.test_cases(take_while(str.isalpha), [('a[','a'),('[a',None)])
  util.test_cases(ZeroOrMore(Literal('a')),[('b',''),('aab','aa')])
  util.test_cases(OneOrMore(Literal('a')), [('aab','aa'),('b',None)])
  util.test_cases(And(Literal('a'),Literal('b')), [('abc','ab'),('ac',None)])
  util.test_cases(Or(Literal('a'),Literal('b')), [('ac','a'),('c',None)])
  util.test_cases(Not(Literal('a')), [('a',None),('b','b')])
  util.test_cases(ZeroOrOne(Literal('a')), [('b',''),('ab','a'),('','')])
  util.test_cases(ZeroOrOne(Literal('-')), [('-', '-'),('', '')])
