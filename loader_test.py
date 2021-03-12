from __future__ import annotations
import lexer
import loader
import parser
import processor
import regex
import unittest
import unittest.util

unittest.util._MAX_LENGTH = 1000


class LoaderTest(unittest.TestCase):
    def test_load_regex(self):
        for input, expected in [
            ('a', regex.Regex(regex.Literal('a'))),
            (
                'a*',
                regex.Regex(
                    processor.ZeroOrMore(
                        regex.Literal('a')
                    )
                )
            ),
            (
                'a+',
                regex.Regex(
                    processor.OneOrMore(
                        regex.Literal('a')
                    )
                )
            ),
            (
                'a?',
                regex.Regex(
                    processor.ZeroOrOne(
                        regex.Literal('a')
                    )
                )
            ),
            (
                'a!',
                regex.Regex(
                    processor.UntilEmpty(
                        regex.Literal('a')
                    )
                )
            ),
            (
                '^a',
                regex.Regex(
                    regex.Not(
                        regex.Literal('a')
                    )
                )
            ),
            (
                '(a)',
                regex.Regex(
                    regex.Literal('a')
                )
            ),
            (
                'ab',
                regex.Regex(
                    processor.And(
                        regex.Literal('a'),
                        regex.Literal('b'),
                    )
                )
            ),
            (
                'a|b',
                regex.Regex(
                    processor.Or(
                        regex.Literal('a'),
                        regex.Literal('b'),
                    )
                )
            ),
            (
                '[a-z]',
                regex.Regex(
                    regex.Class('a', 'z')
                )
            ),
            (
                '\\(',
                regex.Regex(
                    regex.Literal('(')
                )
            )
        ]:
            with self.subTest(input=input, expected=expected):
                self.assertEqual(loader.load_regex(input), expected)

    def test_load_lexer_and_parser(self):
        for input, expected_lexer, expected_parser in [
            (
                'id = "a";',
                lexer.Lexer({'id': loader.load_regex('a')}, {}),
                parser.Parser({}, '')
            ),
            (
                'id ~= "a";',
                lexer.Lexer({}, {'id': loader.load_regex('a')}),
                parser.Parser({}, '')
            ),
            (
                'a -> b;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.Ref('b')}, 'a')
            ),
            (
                'a -> "b";',
                lexer.Lexer({'b': loader.load_regex('b')}, {}),
                parser.Parser({'a': parser.Literal('b')}, 'a')
            ),
            (
                'a -> b*;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.ZeroOrMore(processor.Ref('b'))}, 'a')
            ),
            (
                'a -> b+;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.OneOrMore(processor.Ref('b'))}, 'a')
            ),
            (
                'a -> b?;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.ZeroOrOne(processor.Ref('b'))}, 'a')
            ),
            (
                'a -> b!;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.UntilEmpty(processor.Ref('b'))}, 'a')
            ),
            (
                'a -> (b);',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.Ref('b')}, 'a')
            ),
            (
                'a -> b c;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.And(processor.Ref('b'),processor.Ref('c'))}, 'a')
            ),
            (
                'a -> b | c;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': processor.Or(processor.Ref('b'),processor.Ref('c'))}, 'a')
            ),
        ]:
            with self.subTest(input=input):
                actual_lexer, actual_parser = loader.load_lexer_and_parser(
                    input)
                self.assertEqual(actual_lexer, expected_lexer)
                self.assertEqual(actual_parser, expected_parser)


if __name__ == '__main__':
    unittest.main()
