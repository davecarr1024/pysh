from __future__ import annotations
import lexer
import parser
import processor
import regex
import syntax
from typing import Callable, Optional, Sequence, Tuple


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
    }, 'rule')
    node = parser_.parse(toks)

    syntax_: syntax.Syntax[regex.Rule] = syntax.Syntax(
        syntax.rule_name('literal',
                         syntax.sub_syntax(
                             syntax.get_token_vals('any'),
                             lambda node, vals: regex.Literal(vals[0])
                         )
                         ),
        syntax.rule_name('zero_or_more', syntax.unary(processor.ZeroOrMore)),
        syntax.rule_name('one_or_more', syntax.unary(processor.OneOrMore)),
        syntax.rule_name('zero_or_one', syntax.unary(processor.ZeroOrOne)),
        syntax.rule_name('until_empty', syntax.unary(processor.UntilEmpty)),
        syntax.rule_name('not', syntax.unary(regex.Not)),
        syntax.rule_name('and', lambda node, exprs: processor.And(*exprs)),
        syntax.rule_name('or', lambda node, exprs: processor.Or(*exprs)),
        syntax.rule_name('class',
                         syntax.sub_syntax(
                             syntax.get_token_vals('any'),
                             lambda node, vals: regex.Class(vals[0], vals[1])
                         )
                         ),
        syntax.rule_name('escape', syntax.terminal(
            lambda val: regex.Literal(val[1:]))),
    )
    rules: Sequence[regex.Rule] = syntax_(node)
    assert len(rules) == 1, (input, toks, node, rules)
    return regex.Regex(rules[0])


def load_lexer_and_parser(input: str) -> Tuple[lexer.Lexer, parser.Parser]:
    operators = {'=', '~=', ';', '=>'}
    lexer_ = lexer.Lexer(
        {
            'id': load_regex('([a-z]|[A-Z]|_|\-)([a-z]|[A-Z]|[0-9]|_|\-)*'),
            'regex': load_regex('"(^")*"'),
            **{op: regex.Regex(regex.Literal(op)) for op in operators}
        },
        {
            'ws': regex.Regex(processor.OneOrMore(processor.Or(*[regex.Literal(val) for val in ' \t\n']))),
        }
    )
    toks = lexer_.lex(input)
    parser_ = parser.Parser({
        'root': processor.UntilEmpty(
            processor.Ref('decl')
        ),
        'decl': processor.Or(
            processor.Ref('lex_rule_decl'),
            processor.Ref('silent_lex_rule_decl'),
            processor.Ref('rule_decl'),
        ),
        'lex_rule_decl': processor.And(
            parser.Literal('id'),
            parser.Literal('='),
            parser.Literal('regex'),
            parser.Literal(';'),
        ),
        'silent_lex_rule_decl': processor.And(
            parser.Literal('id'),
            parser.Literal('~='),
            parser.Literal('regex'),
            parser.Literal(';'),
        ),
        'rule_decl': processor.And(
            parser.Literal('id'),
            parser.Literal('=>'),
            processor.Ref('rule'),
            parser.Literal(';'),
        ),
        'rule': processor.Or(
            processor.Ref('ref'),
            processor.Ref('literal'),
        ),
        'ref': parser.Literal('id'),
        'literal': parser.Literal('regex'),
    }, 'root')
    node = parser_.parse(toks)
    loaded_lexer = lexer.Lexer({}, {})
    loaded_parser = parser.Parser({}, '')

    def lex_rule_decl(include: bool) -> syntax.Rule:
        def impl(node: parser.Node, exprs: Sequence[parser.Rule]) -> None:
            id = syntax.get_token_vals('id')(node)[0]
            val = syntax.get_token_vals('regex')(node)[0][1:-1]
            loaded_lexer.add_rule(id, load_regex(val), include)
        return impl

    def rule_decl(node: parser.Node, exprs: Sequence[parser.Rule]) -> parser.Rule:
        id = syntax.get_token_vals('id')(node)[0]
        assert exprs
        rule = exprs[0]
        assert not id in loaded_parser.rules, f'duplicate rule {repr(id)}'
        loaded_parser.rules[id] = rule
        if not loaded_parser.root:
            loaded_parser.root = id
        return rule

    def literal(node: parser.Node, exprs: Sequence[parser.Rule])->parser.Rule:
        val = syntax.get_token_vals('regex')(node)[0][1:-1]
        if val not in loaded_lexer.rules:
            loaded_lexer.add_rule(val, load_regex(val))
        return parser.Literal(val)

    syntax_: syntax.Syntax[parser.Rule] = syntax.Syntax(
        syntax.rule_name('lex_rule_decl', lex_rule_decl(True)),
        syntax.rule_name('silent_lex_rule_decl', lex_rule_decl(False)),
        syntax.rule_name('rule_decl', rule_decl),
        syntax.rule_name(
            'ref',
            syntax.sub_syntax(
                syntax.get_token_vals('id'),
                lambda node, vals: processor.Ref(vals[0])
            )
        ),
        syntax.rule_name('literal', literal),
    )
    syntax_(node)
    return loaded_lexer, loaded_parser
