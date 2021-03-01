from __future__ import annotations
import lexer
import parser
import syntax
from typing import Dict, Optional, Sequence, Tuple

class LexerClass:
    def __init__(self, low: str, high: str):
        self.low = low
        self.high = high

    @staticmethod
    def build(val: str):
        low, high = val.strip('[]').split('-')
        return LexerClass(low, high)

    def __repr__(self) -> str:
        return 'LexerClass(low=%s, high=%s)' % (repr(self.low), repr(self.high))

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.low == rhs.low and self.high == rhs.high

    def __call__(self, s: str) -> Optional[str]:
        return s[0] if s and self.low <= s[0] <= self.high else None


def lexer_rule(s: str) -> lexer.Rule:
    operators = {'*', '+', '(', ')', '|', '^', '?'}
    reserved_operators = operators | {'[', ']', '\\'}
    class_pairs = {('a', 'z'), ('A', 'Z'), ('0', '9')}
    lexer_rules: Dict[str, lexer.Rule] = {
        operator: lexer.Literal(operator) for operator in operators}
    lexer_rules.update({
        'class': lexer.Or(
            *[
                lexer.Literal('[%s-%s]' % class_pair)
                for class_pair in class_pairs
            ]
        ),
        'any': lexer.take_while(lambda s: s not in reserved_operators),
        'literal': lexer.Or(
            *[
                lexer.Literal('\\%s' % operator)
                for operator in reserved_operators
            ]
        ),
    })
    toks = lexer.Lexer(lexer_rules, {})(s)

    node = parser.Parser({
        'rule': parser.Or(
            parser.Ref('operand'),
            parser.Ref('or'),
            parser.Ref('and'),
        ),
        'operand': parser.Or(
            parser.Ref('unary_operand'),
            parser.Ref('unary_operation'),
        ),
        'unary_operand': parser.Or(
            parser.Literal('class'),
            parser.Literal('any'),
            parser.Literal('literal'),
            parser.Ref('paren_rule'),
        ),
        'paren_rule': parser.And(
            parser.Literal('('),
            parser.Ref('rule'),
            parser.Literal(')'),
        ),
        'unary_operation': parser.Or(
            parser.Ref('zero_or_more'),
            parser.Ref('one_or_more'),
            parser.Ref('zero_or_one'),
            parser.Ref('not'),
        ),
        'zero_or_more': parser.And(
            parser.Ref('unary_operand'),
            parser.Literal('*'),
        ),
        'one_or_more': parser.And(
            parser.Ref('unary_operand'),
            parser.Literal('+'),
        ),
        'zero_or_one': parser.And(
            parser.Ref('unary_operand'),
            parser.Literal('?'),
        ),
        'not': parser.And(
            parser.Literal('^'),
            parser.Ref('unary_operand'),
        ),
        'or': parser.And(
            parser.Ref('operand'),
            parser.OneOrMore(
                parser.And(
                    parser.Literal('|'),
                    parser.Ref('operand'),
                ),
            ),
        ),
        'and': parser.And(
            parser.Ref('operand'),
            parser.OneOrMore(
                parser.Ref('operand'),
            ),
        ),
    }, 'rule')(toks)

    return syntax.Syntax({
        syntax.rule_name('class', syntax.terminal(LexerClass.build)),
        syntax.rule_name('any', syntax.terminal(lexer.Literal)),
        syntax.rule_name('literal',
                         syntax.terminal(lambda val: lexer.Literal(val[1:]))),
        syntax.rule_name('zero_or_more', syntax.unary(lexer.ZeroOrMore)),
        syntax.rule_name('one_or_more', syntax.unary(lexer.OneOrMore)),
        syntax.rule_name('zero_or_one', syntax.unary(lexer.ZeroOrOne)),
        syntax.rule_name('not', syntax.unary(lexer.Not)),
        syntax.rule_name('and', lambda node, rules: lexer.And(*rules)),
        syntax.rule_name('or', lambda node, rules: lexer.Or(*rules)),
    })(node)


def lexer_and_parser(s: str) -> Tuple[lexer.Lexer, parser.Parser]:
    operators = {'=', '~=', ';', '->', '+', '*', '?', '|', '(', ')'}
    lexer_rules: Dict[str, lexer.Rule] = {
        operator: lexer.Literal(operator) for operator in operators}
    lexer_rules.update({
        'id': lexer_rule('([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*'),
        'lexer_def': lexer_rule('"(^")*"'),
    })
    toks = lexer.Lexer(lexer_rules,
                       {
                           'ws': lexer.take_while(str.isspace),
                       })(s)

    node = parser.Parser({
        'lines': parser.OneOrMore(
            parser.Or(
                parser.Ref('lexer_rule'),
                parser.Ref('silent_lexer_rule'),
                parser.Ref('rule_decl'),
            )
        ),
        'lexer_rule': parser.And(
            parser.Literal('id'),
            parser.Literal('='),
            parser.Literal('lexer_def'),
            parser.Literal(';'),
        ),
        'silent_lexer_rule': parser.And(
            parser.Literal('id'),
            parser.Literal('~='),
            parser.Literal('lexer_def'),
            parser.Literal(';'),
        ),
        'rule_decl': parser.And(
            parser.Ref('rule_decl_id'),
            parser.Literal('->'),
            parser.Ref('rule'),
            parser.Literal(';'),
        ),
        'rule_decl_id': parser.Literal('id'),
        'rule': parser.Or(
            parser.Ref('or'),
            parser.Ref('and'),
            parser.Ref('operand'),
        ),
        'ref': parser.Literal('id'),
        'literal': parser.Literal('lexer_def'),
        'or': parser.And(
            parser.Ref('operand'),
            parser.OneOrMore(
                parser.And(
                    parser.Literal('|'),
                    parser.Ref('operand'),
                )
            ),
        ),
        'and': parser.And(
            parser.Ref('operand'),
            parser.OneOrMore(
                parser.Ref('operand')
            ),
        ),
        'operand': parser.Or(
            parser.Ref('unary_operand'),
            parser.Ref('unary_operation'),
        ),
        'paren_rule': parser.And(
            parser.Literal('('),
            parser.Ref('rule'),
            parser.Literal(')'),
        ),
        'unary_operand': parser.Or(
            parser.Ref('ref'),
            parser.Ref('literal'),
            parser.Ref('paren_rule'),
        ),
        'unary_operation': parser.Or(
            parser.Ref('one_or_more'),
            parser.Ref('zero_or_more'),
            parser.Ref('zero_or_one'),
        ),
        'one_or_more': parser.And(
            parser.Ref('unary_operand'),
            parser.Literal('+'),
        ),
        'zero_or_more': parser.And(
            parser.Ref('unary_operand'),
            parser.Literal('*'),
        ),
        'zero_or_one': parser.And(
            parser.Ref('unary_operand'),
            parser.Literal('?'),
        ),
    }, 'lines')(toks)

    lexer_ = lexer.Lexer({}, {})
    parser_ = parser.Parser({}, '')

    def lexer_def_str(node: parser.Node) -> str:
        return node.descendant('lexer_def').tok_val().strip('"')

    def lexer_def(node: parser.Node) -> lexer.Rule:
        return lexer_rule(lexer_def_str(node))

    def id(node: parser.Node) -> str:
        return node.descendant('id').tok_val()

    def add_lexer_rule(rules: Dict[str, lexer.Rule]) -> syntax.Rule:
        def impl(node: parser.Node, exprs: Sequence[parser.Rule]) -> Optional[parser.Rule]:
            rules[id(node)] = lexer_def(node)
            return None
        return impl

    def rule_decl(node: parser.Node, rules: Sequence[parser.Rule]) -> Optional[parser.Rule]:
        name = id(node.descendant('rule_decl_id'))
        assert len(rules) == 1, rules
        rule = rules[0]
        parser_.rules[name] = rule
        if not parser_.root:
            parser_.root = name
        return None

    def ref(node: parser.Node, rules: Sequence[parser.Rule]) -> Optional[parser.Rule]:
        name = id(node)
        if name in lexer_.rules:
            return parser.Literal(name)
        else:
            return parser.Ref(name)

    def literal(node: parser.Node, rules: Sequence[parser.Rule]) -> Optional[parser.Rule]:
        val = lexer_def_str(node)
        lexer_.rules[val] = lexer_rule(val)
        return parser.Literal(val)

    syntax.Syntax({
        syntax.rule_name('lexer_rule', add_lexer_rule(lexer_.rules)),
        syntax.rule_name('silent_lexer_rule',
                         add_lexer_rule(lexer_.silent_rules)),
        syntax.rule_name('rule_decl', rule_decl),
        syntax.rule_name('ref', ref),
        syntax.rule_name('literal', literal),
        syntax.rule_name('or', lambda node, rules: parser.Or(*rules)),
        syntax.rule_name('and', lambda node, rules: parser.And(*rules)),
        syntax.rule_name('one_or_more', syntax.unary(parser.OneOrMore)),
        syntax.rule_name('zero_or_more', syntax.unary(parser.ZeroOrMore)),
        syntax.rule_name('zero_or_one', syntax.unary(parser.ZeroOrOne)),
    }).apply_many(node)

    return lexer_, parser_
