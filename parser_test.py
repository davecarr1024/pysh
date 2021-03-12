from __future__ import annotations
import parser
import lexer
import unittest
import processor
from typing import Optional

import unittest.util
unittest.util._MAX_LENGTH = 1000


def token(val: str, location: Optional[lexer.Location] = None, rule_name: Optional[str] = None) -> lexer.Token:
    return lexer.Token(val, location or lexer.Location(0, 0), rule_name or val)


def token_output(token: lexer.Token) -> parser.Node:
    return parser.Node(token=token)


def rule_output(rule_name: str, *children: parser.Node) -> parser.Node:
    return parser.Node(rule_name=rule_name, children=children)


def output(*children: parser.Node) -> parser.Node:
    return parser.Node(children=children)


class InputTest(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(parser.Input([]).empty())
        self.assertFalse(parser.Input([token('a')]).empty())

    def test_advance(self):
        self.assertEqual(
            parser.Input([token('a'), token('b')]).advance(
                token_output(token('a'))
            ),
            parser.Input([token('b')])
        )

    def test_max_location(self):
        self.assertEqual(
            parser.Input([
                token('a', lexer.Location(0, 1)),
                token('b', lexer.Location(1, 0)),
            ]).max_location(),
            lexer.Location(1, 0)
        )


class NodeTest(unittest.TestCase):
    def test_len(self):
        self.assertEqual(
            len(
                output(
                    token_output(token('a')),
                    token_output(token('b')),
                    rule_output('c',
                                token_output(token('d'))
                                )
                )
            ),
            3
        )

    def test_with_rule_name(self):
        self.assertEqual(output().with_rule_name('a'), rule_output('a'))


def context(*toks: lexer.Token) -> parser.Context:
    return parser.Context(parser.Parser({}, ''), parser.Input(list(toks)))


class LiteralTest(unittest.TestCase):
    def test_call_no_input(self):
        with self.assertRaisesRegex(processor.Error, 'no input'):
            parser.Literal('a')(context())

    def test_call_mismatch(self):
        with self.assertRaisesRegex(processor.Error, 'failed to match Token'):
            parser.Literal('a')(context(token('b')))

    def test_call_success(self):
        self.assertEqual(
            parser.Literal('a')(context(token('a'))),
            parser.Node(token=token('a'))
        )


class ParserTest(unittest.TestCase):
    def test_parse(self):
        for input, expected in [
            (
                [token('c')], 
                rule_output('a', 
                    output(
                        rule_output('b',
                            token_output(token('c'))
                        )
                    )
                )
            ),
            (
                [token('d')], 
                rule_output('a', 
                    output(
                        rule_output('b',
                            token_output(token('d'))
                        )
                    )
                )
            ),
            (
                [
                    token('c'),
                    token('d'),
                ],
                rule_output(
                    'a',
                    output(
                        rule_output('b',
                            token_output(token('c'))
                        )
                    ),
                    output(
                        rule_output('b',
                            token_output(token('d'))
                        )
                    ),
                )
            ),
        ]:
            with self.subTest(input=input, expected=expected):
                self.assertEqual(
                    parser.Parser(
                        {
                            'a': processor.UntilEmpty(
                                processor.Ref('b')
                            ),
                            'b': processor.Or(
                                parser.Literal('c'),
                                parser.Literal('d'),
                            ),
                        },
                        'a'
                    ).parse(input),
                    expected
                )


if __name__ == '__main__':
    unittest.main()
