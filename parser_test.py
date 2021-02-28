from __future__ import annotations
import lexer
import parser
from typing import Sequence, Set, Tuple
import unittest
import unittest.util

unittest.util._MAX_LENGTH = 1000


class ParserTest(unittest.TestCase):
    def test_node_eq(self):
        self.assertEqual(parser.Node(tok=lexer.Token('id', 'a')),
                         parser.Node(tok=lexer.Token('id', 'a')))
        self.assertNotEqual(parser.Node(tok=lexer.Token(
            'id', 'a')), parser.Node(tok=lexer.Token('id', 'b')))
        self.assertEqual(parser.Node(rule_name='a'),
                         parser.Node(rule_name='a'))
        self.assertNotEqual(parser.Node(rule_name='a'),
                            parser.Node(rule_name='b'))
        self.assertEqual(
            parser.Node(children=[parser.Node(rule_name='a')]),
            parser.Node(children=[parser.Node(rule_name='a')]))
        self.assertNotEqual(
            parser.Node(children=[parser.Node(rule_name='a')]),
            parser.Node(children=[parser.Node(rule_name='b')]))

    def test_node_len(self):
        self.assertEqual(
            2,
            len(parser.Node(
                tok=lexer.Token('id', 'a'),
                children=[
                    parser.Node(rule_name='b'),
                    parser.Node(tok=lexer.Token('id', 'c')),
                ]
            )))

    def test_node_descendants(self):
        self.assertEqual(
            [parser.Node(rule_name='a')],
            parser.Node(children=[
                parser.Node(rule_name='a'),
                parser.Node(rule_name='b'),
            ]).descendants('a'))

    def test_node_nary_descendants(self):
        self.assertEqual([parser.Node(rule_name='a'),
                          parser.Node(rule_name='a'),
                          parser.Node(rule_name='a')],
                         parser.Node(children=[
                             parser.Node(rule_name='a'),
                             parser.Node(rule_name='a'),
                             parser.Node(rule_name='a'),
                             parser.Node(rule_name='b'),
                         ]).nary_descendants('a', 3))
        with self.assertRaisesRegex(
                Exception,
                'unexpected number of descendants'):
            parser.Node(children=[
                parser.Node(rule_name='a'),
                parser.Node(rule_name='a'),
                parser.Node(rule_name='a'),
                parser.Node(rule_name='b'),
            ]).nary_descendants('a', 4)

    def test_node_binary_descendants(self):
        a = parser.Node(rule_name='r', tok=lexer.Token('id', 'a'))
        b = parser.Node(rule_name='r', tok=lexer.Token('id', 'b'))
        self.assertEqual(
            (a, b),
            parser.Node(
                children=[
                    a,
                    b,
                    parser.Node(rule_name='q'),
                ]).binary_descendants('r'))

    def test_node_desendant(self):
        a = parser.Node(rule_name='r', tok=lexer.Token('id', 'a'))
        self.assertEqual(a, parser.Node(
            children=[a, parser.Node(rule_name='q')]).descendant('r'))

    def test_tok_val(self):
        self.assertEqual('a', parser.Node(
            tok=lexer.Token('id', 'a')).tok_val())
        with self.assertRaisesRegex(Exception, 'expected tok'):
            parser.Node().tok_val()

    def test_literal(self):
        self.assertEqual(
            parser.literal('id')(
                parser.Parser({}, ''),
                [lexer.Token('id', 'a')],
            ),
            {parser.Node(tok=lexer.Token('id', 'a'), rule_name='id')})

    def test_ref(self):
        self.assertEqual(
            parser.ref('idref')(
                parser.Parser({'idref': parser.literal('id')}, ''),
                [lexer.Token('id', 'a')],
            ),
            {parser.Node(
                rule_name='idref',
                children=[
                    parser.Node(
                        tok=lexer.Token('id', 'a'),
                        rule_name='id'
                    )])})

    def rule_cases(
        self,
        rule: parser.Rule,
        cases: Sequence[Tuple[Sequence[lexer.Token], Set[parser.Node]]],
    ):
        for i, o in cases:
            with self.subTest(i=i, o=o):
                self.assertEqual(rule(parser.Parser({}, ''), i), o)

    def test_and(self):
        self.rule_cases(
            parser.and_(
                parser.literal('id'),
                parser.literal('='),
            ),
            [
                (
                    [lexer.Token('id', 'a'), lexer.Token('=', '=')],
                    {parser.Node(
                        children=[
                            parser.Node(tok=lexer.Token(
                                'id', 'a'), rule_name='id'),
                            parser.Node(tok=lexer.Token(
                                '=', '='), rule_name='='),
                        ]
                    )}
                ),
                (
                    [lexer.Token('(', '(')],
                    set()
                )
            ]
        )

    def test_or(self):
        self.rule_cases(
            parser.or_(
                parser.literal('a'),
                parser.literal('b'),
            ),
            [
                (
                    [lexer.Token('b', 'b')],
                    {parser.Node(
                        children=[parser.Node(
                            tok=lexer.Token('b', 'b'), rule_name='b')],
                    )}
                ),
                (
                    [lexer.Token('c', 'c')],
                    set(),
                ),
            ]
        )

    def test_zero_or_more(self):
        self.rule_cases(
            parser.zero_or_more(
                parser.literal('id')
            ),
            [
                (
                    [lexer.Token('id', 'a')],
                    {parser.Node(
                        children=[
                            parser.Node(rule_name='id',
                                        tok=lexer.Token('id', 'a')),
                        ]
                    )}
                ),
                (
                    [],
                    {parser.Node()}
                )
            ]
        )

    def test_one_or_more(self):
        self.rule_cases(
            parser.one_or_more(
                parser.literal('id')
            ),
            [
                (
                    [lexer.Token('id', 'a')],
                    {parser.Node(
                        children=[
                            parser.Node(rule_name='id',
                                        tok=lexer.Token('id', 'a')),
                        ]
                    )}
                ),
                (
                    [lexer.Token('id', 'a'), lexer.Token('id', 'a')],
                    {parser.Node(
                        children=[
                            parser.Node(rule_name='id',
                                        tok=lexer.Token('id', 'a')),
                            parser.Node(rule_name='id',
                                        tok=lexer.Token('id', 'a')),
                        ]
                    )}
                ),
                (
                    [],
                    set()
                ),
            ]
        )

    def test_zero_or_one(self):
        self.rule_cases(
            parser.zero_or_one(
                parser.literal('id')
            ),
            [
                (
                    [lexer.Token('id', 'a')],
                    {parser.Node(
                        children=[
                            parser.Node(rule_name='id',
                                        tok=lexer.Token('id', 'a')),
                        ]
                    )}
                ),
                (
                    [],
                    {parser.Node()}
                ),
            ]
        )

    def test_parser(self):
        self.assertEqual(
            parser.Parser(
                {
                    'idref': parser.literal('id'),
                },
                'idref'
            )([lexer.Token('id', 'a')]),
            parser.Node(
                rule_name='idref',
                children=[
                    parser.Node(rule_name='id', tok=lexer.Token('id', 'a')),
                ]
            )
        )


if __name__ == '__main__':
    unittest.main()
