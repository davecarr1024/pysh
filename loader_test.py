from __future__ import annotations
import lexer
import parser
import loader
from typing import Callable
import unittest
import unittest.util

unittest.util._MAX_LENGTH = 1000


class LoaderTest(unittest.TestCase):
    def test_lexer_rule(self):
        for rule_str, expected_rule in [
            ('[a-z]', loader.LexerClass('a', 'z')),
            ('abc', lexer.Literal('abc')),
            ('\|', lexer.Literal('|')),
            ('a*', lexer.ZeroOrMore(lexer.Literal('a'))),
            ('a+', lexer.OneOrMore(lexer.Literal('a'))),
            ('a?', lexer.ZeroOrOne(lexer.Literal('a'))),
            ('^a', lexer.Not(lexer.Literal('a'))),
            ('(a)(b)', lexer.And(lexer.Literal('a'), lexer.Literal('b'))),
            ('(a|b)', lexer.Or(lexer.Literal('a'), lexer.Literal('b'))),
            ('a|b|c', lexer.Or(lexer.Literal('a'), lexer.Literal('b'), lexer.Literal('c'))),
        ]:
            with self.subTest(rule_str=rule_str, expected_rule=expected_rule):
                self.assertEqual(loader.lexer_rule(rule_str), expected_rule)

    def test_lexer_and_parser(self):
        for input, expected_lexer, expected_parser in [
            (
                r'id = "abc";',
                lexer.Lexer({'id': lexer.Literal('abc')}, {}),
                parser.Parser({}, '')
            ),
            (
                r'id ~= "abc";',
                lexer.Lexer({}, {'id': lexer.Literal('abc')}),
                parser.Parser({}, '')
            ),
            (
                r'a -> b;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': parser.Ref('b')}, 'a')
            ),
            (
                r'id = "abc"; a -> id;',
                lexer.Lexer({'id': lexer.Literal('abc')}, {}),
                parser.Parser({'a': parser.Literal('id')}, 'a')
            ),
            (
                r'a -> "abc";',
                lexer.Lexer({'abc': lexer.Literal('abc')}, {}),
                parser.Parser({'a': parser.Literal('abc')}, 'a')
            ),
            (
                r'a -> b | c;',
                lexer.Lexer({}, {}),
                parser.Parser(
                    {'a': parser.Or(parser.Ref('b'), parser.Ref('c'))}, 'a')
            ),
            (
                r'a -> b c;',
                lexer.Lexer({}, {}),
                parser.Parser(
                    {'a': parser.And(parser.Ref('b'), parser.Ref('c'))}, 'a')
            ),
            (
                r'a -> b+;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': parser.OneOrMore(parser.Ref('b'))}, 'a')
            ),
            (
                r'a -> b*;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': parser.ZeroOrMore(parser.Ref('b'))}, 'a')
            ),
            (
                r'a -> b?;',
                lexer.Lexer({}, {}),
                parser.Parser({'a': parser.ZeroOrOne(parser.Ref('b'))}, 'a')
            ),
            (
                r'a -> (b c)+ (d | e);',
                lexer.Lexer({}, {}),
                parser.Parser({
                    'a': parser.And(
                        parser.OneOrMore(
                            parser.And(
                                parser.Ref('b'),
                                parser.Ref('c'),
                            )
                        ),
                        parser.Or(
                            parser.Ref('d'),
                            parser.Ref('e'),
                        )
                    )
                }, 'a')
            )
        ]:
            with self.subTest(input=input, expected_lexer=expected_lexer, expected_parser=expected_parser):
                actual_lexer, actual_parser = loader.lexer_and_parser(input)
                self.assertEqual(actual_lexer, expected_lexer)
                self.assertEqual(actual_parser, expected_parser)


if __name__ == '__main__':
    unittest.main()
