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
            ('[a-z]', loader.LexerClass('a','z')),
            ('abc', lexer.Literal('abc')),
            ('\|', lexer.Literal('|')),
            ('a*', lexer.ZeroOrMore(lexer.Literal('a'))),
            ('a+', lexer.OneOrMore(lexer.Literal('a'))),
            ('a?', lexer.ZeroOrOne(lexer.Literal('a'))),
            ('^a', lexer.Not(lexer.Literal('a'))),
            ('(a)(b)', lexer.And(lexer.Literal('a'),lexer.Literal('b'))),
            ('(a|b)', lexer.Or(lexer.Literal('a'),lexer.Literal('b'))),
        ]:
            with self.subTest(rule_str=rule_str, expected_rule=expected_rule):
                self.assertEqual(loader.lexer_rule(rule_str), expected_rule)

    def test_lexer_and_parser(self):
        for s, cases in [
            (r'''
                id = "([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*";
                ws ~= " +";
                expr -> id | paren_expr;
                paren_expr -> "\(" expr+ "\)";
            ''', [
                # (
                #     'abc',
                #     parser.Node(
                #         rule_name='expr',
                #         children=[
                #             parser.Node(rule_name='id',
                #                         tok=lexer.Token('id', 'abc')),
                #         ]
                #     )
                # ),
            ]),
        ]:
            l, p = loader.lexer_and_parser(s)

            for i, o in cases:
                with self.subTest(parser=p, input=i):
                    self.assertEqual(p(l(i)), o)


if __name__ == '__main__':
    unittest.main()

