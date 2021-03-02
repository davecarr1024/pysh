from __future__ import annotations
import lexer
import parser
from typing import Callable, Optional, Set
import unittest

import unittest.util
unittest.util._MAX_LENGTH = 1000


def node(*children: parser.Node) -> parser.Node:
    return parser.Node(children=children)


def rule_node(rule_name: Optional[str], *children: parser.Node) -> parser.Node:
    return parser.Node(rule_name=rule_name, children=children)


def token(rule_name: str, val: Optional[str] = None, loc: Optional[lexer.Location] = None) -> lexer.Token:
    return lexer.Token(rule_name=rule_name, val=val or rule_name, loc=loc)


def token_node(rule_name: str, tok: Optional[lexer.Token] = None) -> parser.Node:
    return parser.Node(rule_name=rule_name, tok=tok or token(rule_name))


def apply_rule_parser(rule: parser.Rule, parser_: parser.Parser, *toks: lexer.Token) -> parser.Node:
    return rule(parser.State(parser=parser_, toks=list(toks)))


def apply_rule(rule: parser.Rule, *toks: lexer.Token) -> parser.Node:
    return apply_rule_parser(rule, parser.Parser({}, ''), *toks)


class ParserTest(unittest.TestCase):
    def test_node(self):
        self.assertEqual(
            node(rule_node('a', token_node('b', 'c'))),
            node(rule_node('a', token_node('b', 'c'))))
        self.assertNotEqual(
            node(rule_node('a', token_node('b', 'c'))),
            node(rule_node('d', token_node('b', 'c'))))
        self.assertNotEqual(
            node(rule_node('a', token_node('b', 'c'))),
            node(rule_node('a', token_node('d', 'c'))))
        self.assertNotEqual(
            node(rule_node('a', token_node('b', 'c'))),
            node(rule_node('a', token_node('b', 'd'))))
        self.assertEqual(len(node()), 0)
        self.assertEqual(len(node(token_node('a'))), 1)

    def test_terminal_error(self):
        self.assertEqual(
            parser.TerminalError('a', lexer.Location(0, 1)),
            parser.TerminalError('a', lexer.Location(0, 1)))
        self.assertNotEqual(
            parser.TerminalError('a', lexer.Location(0, 1)),
            parser.TerminalError('b', lexer.Location(0, 1)))
        self.assertNotEqual(
            parser.TerminalError('a', lexer.Location(0, 1)),
            parser.TerminalError('a', lexer.Location(2, 1)))
        self.assertNotEqual(
            parser.TerminalError('a', lexer.Location(0, 1)),
            parser.TerminalError('a', lexer.Location(0, 2)))
        self.assertEqual(
            parser.TerminalError('a', lexer.Location(0, 1)).max(),
            (lexer.Location(0, 1), [parser.TerminalError('a', lexer.Location(0, 1))]))

    def test_compound_error(self):
        self.assertEqual(
            parser.CompoundError([parser.TerminalError('a')]),
            parser.CompoundError([parser.TerminalError('a')])
        )
        self.assertNotEqual(
            parser.CompoundError([parser.TerminalError('a')]),
            parser.CompoundError([parser.TerminalError('b')])
        )
        self.assertEqual(
            parser.CompoundError([
                parser.TerminalError('a', lexer.Location(0, 0)),
                parser.TerminalError('b', lexer.Location(1, 0)),
                parser.TerminalError('c', lexer.Location(1, 0)),
                parser.TerminalError('d'),
            ]).max(),
            (lexer.Location(1, 0), [
                parser.TerminalError('b', lexer.Location(1, 0)),
                parser.TerminalError('c', lexer.Location(1, 0)),
            ])
        )
        self.assertEqual(
            parser.CompoundError([
                parser.TerminalError('a'),
                parser.TerminalError('b'),
            ]).max(),
            (None, [
                parser.TerminalError('a'),
                parser.TerminalError('b'),
            ])
        )

    def test_context_error(self):
        self.assertEqual(
            parser.ContextError('a', parser.TerminalError('b')),
            parser.ContextError('a', parser.TerminalError('b')),
        )
        self.assertNotEqual(
            parser.ContextError('a', parser.TerminalError('b')),
            parser.ContextError('c', parser.TerminalError('b')),
        )
        self.assertNotEqual(
            parser.ContextError('a', parser.TerminalError('b')),
            parser.ContextError('a', parser.TerminalError('c')),
        )
        self.assertEqual(
            parser.ContextError(
                'a',
                parser.TerminalError('b', lexer.Location(0, 1))
            ).max(),
            (lexer.Location(0, 1), [
                parser.ContextError(
                    'a',
                    parser.TerminalError('b', lexer.Location(0, 1))
                )
            ])
        )
        self.assertEqual(
            parser.ContextError(
                'a',
                parser.CompoundError([
                    parser.TerminalError('b', lexer.Location(0, 1)),
                    parser.TerminalError('c', lexer.Location(0, 1)),
                ])
            ).max(),
            (
                lexer.Location(0, 1),
                [
                    parser.ContextError(
                        'a',
                        parser.TerminalError('b', lexer.Location(0, 1))
                    ),
                    parser.ContextError(
                        'a',
                        parser.TerminalError('c', lexer.Location(0, 1))
                    ),
                ]
            )
        )

    def assert_error(self,
                     f: Callable[[], None],
                     expected: parser.Error) -> None:
        try:
            f()
            self.fail('expected error')
        except parser.Error as e:
            self.assertEqual(e, expected)

    def test_literal(self):
        def literal(*toks: lexer.Token) -> parser.Node:
            return apply_rule(parser.Literal('a'), *toks)
        self.assertEqual(literal(token('a')), token_node('a'))
        self.assert_error(
            lambda: literal(token('b', loc=lexer.Location(0, 0))),
            parser.TerminalError('failed to find literal \'a\'', lexer.Location(0, 0)))
        self.assert_error(
            lambda: literal(),
            parser.TerminalError('failed to find literal \'a\': eof'))

    def test_ref(self):
        def ref(*toks: lexer.Token) -> parser.Node:
            return apply_rule_parser(
                parser.Ref('a'),
                parser.Parser({'a': parser.Literal('b')}, 'a'),
                *toks
            )
        self.assertEqual(
            ref(token('b')),
            node(token_node('a', token('b'))))
        self.assert_error(
            lambda: apply_rule(parser.Ref('a')),
            parser.TerminalError('unknown rule \'a\'')
        )
        self.assert_error(
            lambda: ref(token('c')),
            parser.ContextError(
                'failed to apply rule \'a\'',
                parser.TerminalError('failed to find literal \'b\'')
            )
        )

    def test_and(self):
        def and_(*toks: lexer.Token) -> parser.Node:
            return apply_rule(parser.And(
                parser.Literal('a'),
                parser.Literal('b'),
            ), *toks)
        self.assertEqual(
            and_(token('a'), token('b')),
            node(token_node('a'), token_node('b'))
        )
        self.assert_error(
            lambda: and_(token('a')),
            parser.TerminalError('failed to find literal \'b\': eof')
        )
        self.assert_error(
            lambda: and_(token('a'), token('c')),
            parser.TerminalError('failed to find literal \'b\'')
        )

    def test_or(self):
        def or_(*toks: lexer.Token) -> parser.Node:
            return apply_rule(parser.Or(
                parser.Literal('a'),
                parser.Literal('b'),
            ), *toks)
        self.assertEqual(
            or_(token('a')),
            node(token_node('a'))
        )
        self.assertEqual(
            or_(token('b')),
            node(token_node('b'))
        )
        self.assert_error(
            lambda: or_(token('c')),
            parser.CompoundError([
                parser.TerminalError('failed to find literal \'a\''),
                parser.TerminalError('failed to find literal \'b\''),
            ])
        )

    def test_zero_or_more(self):
        for toks, expected in [
            ([], node()),
            ([token('b')], node()),
            ([token('a')], node(token_node('a'))),
            ([token('a'), token('b')], node(token_node('a'))),
            ([token('a'), token('a')], node(token_node('a'), token_node('a'))),
            (
                [token('a'), token('a'), token('b')],
                node(token_node('a'), token_node('a'))
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    apply_rule(parser.ZeroOrMore(parser.Literal('a')), *toks),
                    expected)

    def test_one_or_more(self):
        def one_or_more(*toks: lexer.Token) -> parser.Node:
            return apply_rule(parser.OneOrMore(parser.Literal('a')), *toks)
        for toks, expected in [
            ([token('a')], node(token_node('a'))),
            ([token('a'), token('b')], node(token_node('a'))),
            ([token('a'), token('a')], node(token_node('a'), token_node('a'))),
            ([token('a'), token('a'), token('b')],
             node(token_node('a'), token_node('a'))),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(one_or_more(*toks), expected)
        for toks, error in [
            ([], parser.TerminalError('failed to find literal \'a\': eof')),
            ([token('b')], parser.TerminalError('failed to find literal \'a\'')),
        ]:
            with self.subTest(toks=toks):
                self.assert_error(lambda: one_or_more(*toks), error)

    def test_zero_or_one(self):
        for toks, expected in [
            ([], node()),
            ([token('b')], node()),
            ([token('a')], node(token_node('a'))),
            ([token('a'), token('a')], node(token_node('a'))),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    apply_rule(parser.ZeroOrOne(parser.Literal('a')), *toks),
                    expected
                )

    def test_parser(self):
        def run(*toks: lexer.Token) -> parser.Node:
            return parser.Parser({
                'a': parser.OneOrMore(
                    parser.Ref('b')
                ),
                'b': parser.Or(
                    parser.Ref('c'),
                    parser.Literal('d'),
                ),
                'c': parser.Literal('e'),
            }, 'a')(list(toks))
        for toks, expected in [
            (
                [token('d')],
                rule_node('a', node(rule_node('b', token_node('d'))))
            ),
            (
                [token('e')],
                rule_node(
                    'a',
                    node(
                        rule_node(
                            'b',
                            node(
                                token_node('c', token('e')))))),
            ),
            (
                [token('d'), token('d')],
                rule_node('a',
                          node(rule_node('b', token_node('d'))),
                          node(rule_node('b', token_node('d'))))
            )
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(run(*toks), expected)
        for toks, error in [
            (
                [
                token('d', loc=lexer.Location(1, 0)),
                token('f', loc=lexer.Location(2, 0)),
                ],
                parser.CompoundError([
                    parser.ContextError(
                        "failed to apply rule 'a'",
                        parser.ContextError(
                            "failed to apply rule 'b'",
                            parser.ContextError(
                                "failed to apply rule 'c'",
                                parser.TerminalError(
                                    msg="failed to find literal 'e'",
                                    loc=lexer.Location(line=2, col=0))))),
                    parser.ContextError(
                        "failed to apply rule 'a'",
                        parser.ContextError(
                            "failed to apply rule 'b'",
                            parser.TerminalError(
                                msg="failed to find literal 'd'",
                                loc=lexer.Location(line=2, col=0))))])
            ),
        ]:
            with self.subTest(toks=toks):
                self.assert_error(lambda: run(*toks), error)


if __name__ == '__main__':
    unittest.main()
