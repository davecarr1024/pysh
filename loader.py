from __future__ import annotations
import lexer
import parser
import syntax
from typing import Dict, Optional, Sequence, Tuple


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
    }, 'rule')(toks)

    class Class:
        def __init__(self, val: str):
            self.low, self.high = val.strip('[]').split('-')

        def __repr__(self) -> str:
            return '[%s-%s]' % (self.low, self.high)

        def __call__(self, s: str) -> Optional[str]:
            return s[0] if s and self.low <= s[0] <= self.high else None

    return syntax.Syntax({
        syntax.rule_name('class', syntax.terminal(Class)),
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
    operators = {'=', '~=', ';', '->', '+'}
    lexer_rules: Dict[str, lexer.Rule] = {
        operator: lexer.Literal(operator) for operator in operators}
    lexer_rules.update({
        'id': lexer_rule('([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*'),
        'lexer_def': lexer_rule('"(^")*"'),
        '|': lexer_rule('\|'),
    })
    toks = lexer.Lexer(lexer_rules,
                       {
                           'ws': lexer.take_while(str.isspace),
                       })(s)

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
            parser.ref('rule_decl_id'),
            parser.literal('->'),
            parser.ref('rule'),
            parser.literal(';'),
        ),
        'rule_decl_id': parser.literal('id'),
        'rule': parser.or_(
            parser.ref('or'),
            parser.ref('and'),
            parser.ref('operand'),
        ),
        'ref': parser.literal('id'),
        'literal': parser.literal('lexer_def'),
        'or': parser.and_(
            parser.ref('operand'),
            parser.one_or_more(
                parser.and_(
                    parser.literal('|'),
                    parser.ref('operand'),
                )
            ),
        ),
        'and': parser.and_(
            parser.ref('operand'),
            parser.one_or_more(
                parser.ref('operand')
            ),
        ),
        'operand': parser.or_(
            parser.ref('unary_operand'),
            parser.ref('unary_operation'),
        ),
        'unary_operand': parser.or_(
            parser.ref('ref'),
            parser.ref('literal'),
        ),
        'unary_operation': parser.or_(
            parser.ref('one_or_more'),
        ),
        'one_or_more': parser.and_(
            parser.ref('unary_operand'),
            parser.literal('+'),
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
            return parser.literal(name)
        else:
            return parser.ref(name)

    def literal(node: parser.Node, rules: Sequence[parser.Rule]) -> Optional[parser.Rule]:
        val = lexer_def_str(node)
        lexer_.rules[val] = lexer_rule(val)
        return parser.literal(val)

    syntax.Syntax({
        syntax.rule_name('lexer_rule', add_lexer_rule(lexer_.rules)),
        syntax.rule_name('silent_lexer_rule',
                         add_lexer_rule(lexer_.silent_rules)),
        syntax.rule_name('rule_decl', rule_decl),
        syntax.rule_name('ref', ref),
        syntax.rule_name('literal', literal),
        syntax.rule_name('or', lambda node, rules: parser.or_(*rules)),
        syntax.rule_name('and', lambda node, rules: parser.and_(*rules)),
        syntax.rule_name('one_or_more', syntax.unary(parser.one_or_more)),
    }).apply_many(node)

    return lexer_, parser_
