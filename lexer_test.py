import lexer
import processor
import regex
import unittest

import unittest.util
unittest.util._MAX_LENGTH = 1000


class LocationTest(unittest.TestCase):
    def test_advance(self):
        self.assertEqual(
            lexer.Location(0, 0).advance(
                lexer.Output([
                    lexer.Token('a\n\n', lexer.Location(0, 0)),
                    lexer.Token('b', lexer.Location(0, 0)),
                ])
            ),
            lexer.Location(2, 1)
        )


class InputTest(unittest.TestCase):
    def test_advance(self):
        self.assertEqual(
            lexer.Input(
                input='abc',
                location=lexer.Location(0, 0),
            ).advance(lexer.Output([
                lexer.Token('ab', lexer.Location(0, 0)),
            ])),
            lexer.Input(
                input='c',
                location=lexer.Location(0, 2),
            )
        )

    def test_empty(self):
        self.assertTrue(lexer.Input('', lexer.Location(0, 0)).empty)
        self.assertFalse(lexer.Input('a', lexer.Location(0, 0)).empty)


class TokenTest(unittest.TestCase):
    def test_with_rule_name(self):
        self.assertEqual(
            lexer.Token('a', lexer.Location(0, 1)).with_rule_name('r'),
            lexer.Token('a', lexer.Location(0, 1), 'r')
        )

    def test_len(self):
        self.assertEqual(len(lexer.Token('abc', lexer.Location(0, 1))), 3)


class OutputTest(unittest.TestCase):
    def test_with_rule_name(self):
        self.assertEqual(
            lexer.Output((
                lexer.Token('a', lexer.Location(0, 1)),
                lexer.Token('b', lexer.Location(2, 3)),
            )).with_rule_name('r'),
            lexer.Output((
                lexer.Token('a', lexer.Location(0, 1), 'r'),
                lexer.Token('b', lexer.Location(2, 3), 'r')
            ))
        )

    def test_aggregate(self):
        self.assertEqual(
            lexer.Output.aggregate([
                lexer.Output((
                    lexer.Token('a', lexer.Location(0, 1)),
                )),
                lexer.Output((
                    lexer.Token('b', lexer.Location(2, 3)),
                )),
            ]),
            lexer.Output((
                lexer.Token('a', lexer.Location(0, 1)),
                lexer.Token('b', lexer.Location(2, 3)),
            ))
        )


class LiteralTest(unittest.TestCase):
    def test_call(self):
        self.assertEqual(
            lexer.Literal(regex.Regex(regex.Literal('a')))(
                lexer.Context(
                    lexer.Lexer({},{}), lexer.Input('a', lexer.Location(0, 1)))
            ),
            lexer.Output((lexer.Token('a', lexer.Location(0, 1)),))
        )


class LexerTest(unittest.TestCase):
    def test_lex(self):
        for input, output in [
            (
                ' aa ',
                [
                    lexer.Token(val='aa', rule_name='ar',location=lexer.Location(0, 1)),
                ]
            ),
            (
                ' baa ',
                [
                    lexer.Token(val='b', rule_name='br',
                                location=lexer.Location(0, 1)),
                    lexer.Token(val='aa', rule_name='ar',
                                location=lexer.Location(0, 2)),
                ]
            ),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(
                    lexer.Lexer(
                        {
                            'ar': regex.Regex(
                                processor.OneOrMore(regex.Literal('a'))),
                            'br': regex.Regex(regex.Literal('b')),
                        }, {
                            'ws': regex.Regex(regex.Literal(' ')),
                        }
                    ).lex(input),
                    output
                )


if __name__ == '__main__':
    unittest.main()
