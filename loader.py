from __future__ import annotations
import lexer
import parser
import processor
import regex
import syntax
from typing import Callable, Optional, Sequence


def load_regex(input: str) -> regex.Regex:
    operators = '*+?^!()[]-|'
    reserved_operators = operators + '\\'
    class_pairs = {('a', 'z'), ('A', 'Z'), ('0', '9')}
    lexer_ = lexer.Lexer({
        'any': regex.Regex(regex.Not(processor.Or(
            *[regex.Literal(op) for op in reserved_operators]))),
        'escape': regex.Regex(processor.Or(
            *[regex.Literal('\\%s' % op) for op in operators])),
        **{op: regex.Regex(regex.Literal(op)) for op in operators}
    }, {})
    toks = lexer_.lex(input)
    parser_ = parser.Parser({
        'root': processor.UntilEmpty(
            processor.Ref('rule'),
        ),
        'rule': processor.Or(
            processor.Ref('or'),
            processor.Ref('and'),
            processor.Ref('operand'),
        ),
        'and': processor.And(
            processor.Ref('operand'),
            processor.OneOrMore(
                processor.Ref('operand')
            ),
        ),
        'or': processor.And(
            processor.Ref('operand'),
            processor.OneOrMore(
                processor.And(
                    parser.Literal('|'),
                    processor.Ref('operand'),
                )
            ),
        ),
        'operand': processor.Or(
            processor.Ref('class'),
            processor.Ref('unary_operation'),
            processor.Ref('unary_operand'),
        ),
        'class': processor.And(
            parser.Literal('['),
            parser.Literal('any'),
            parser.Literal('-'),
            parser.Literal('any'),
            parser.Literal(']'),
        ),
        'unary_operand': processor.Or(
            parser.Literal('escape'),
            processor.Ref('literal'),
            processor.Ref('paren_rule'),
        ),
        'paren_rule': processor.And(
            parser.Literal('('),
            processor.Ref('rule'),
            parser.Literal(')'),
        ),
        'literal': parser.Literal('any'),
        'unary_operation': processor.Or(
            processor.Ref('zero_or_more'),
            processor.Ref('one_or_more'),
            processor.Ref('zero_or_one'),
            processor.Ref('until_empty'),
            processor.Ref('not'),
        ),
        'zero_or_more': processor.And(
            processor.Ref('unary_operand'),
            parser.Literal('*'),
        ),
        'one_or_more': processor.And(
            processor.Ref('unary_operand'),
            parser.Literal('+'),
        ),
        'zero_or_one': processor.And(
            processor.Ref('unary_operand'),
            parser.Literal('?'),
        ),
        'until_empty': processor.And(
            processor.Ref('unary_operand'),
            parser.Literal('!'),
        ),
        'not': processor.And(
            parser.Literal('^'),
            processor.Ref('unary_operand'),
        ),
    }, 'root')
    node = parser_.parse(toks)

    def any(factory: Callable[[Sequence[str]], regex.Rule]) -> syntax.Rule:
        def impl(node: parser.Node, exprs: Sequence[regex.Rule]) -> Optional[regex.Rule]:
            return factory(syntax.Syntax({syntax.rule_name('any', lambda node, exprs: node.token and node.token.val)})(node))
        return impl

    syntax_ = syntax.Syntax({
        syntax.rule_name('literal', any(lambda vals: regex.Literal(vals[0]))),
        syntax.rule_name('zero_or_more', syntax.unary(processor.ZeroOrMore)),
        syntax.rule_name('one_or_more', syntax.unary(processor.OneOrMore)),
        syntax.rule_name('zero_or_one', syntax.unary(processor.ZeroOrOne)),
        syntax.rule_name('until_empty', syntax.unary(processor.UntilEmpty)),
        syntax.rule_name('not', syntax.unary(regex.Not)),
        syntax.rule_name('and', lambda node, exprs: processor.And(*exprs)),
        syntax.rule_name('or', lambda node, exprs: processor.Or(*exprs)),
        syntax.rule_name('class', any(
            lambda vals: regex.Class(vals[0], vals[1]))),
        syntax.rule_name('escape', syntax.terminal(
            lambda val: regex.Literal(val[1:]))),
    })
    rules: Sequence[regex.Rule] = syntax_(node)
    return regex.Regex(*rules)
