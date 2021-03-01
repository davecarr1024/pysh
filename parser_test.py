from __future__ import annotations
import lexer
import parser
from typing import Optional, Sequence, Set, Tuple
import unittest
import unittest.util

unittest.util._MAX_LENGTH = 1000


def empty_success(*children: parser.Result) -> parser.Success:
    return parser.Success(children=list(children))


def rule_success(rule_name: str, *children: parser.Result) -> parser.Success:
    return parser.Success(rule_name=rule_name, children=list(children))


def token_success(rule_name: str, val: Optional[str] = None) -> parser.Success:
    return parser.Success(rule_name=rule_name, tok=lexer.Token(rule_name=rule_name, val=val or rule_name))


def token(rule_name: str, val: Optional[str] = None) -> lexer.Token:
    return lexer.Token(rule_name=rule_name, val=val or rule_name)


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

    def test_success(self):
        self.assertEqual(parser.Success(tok=lexer.Token('id', 'a')),
                         parser.Success(tok=lexer.Token('id', 'a')))
        self.assertNotEqual(
            parser.Success(tok=lexer.Token('id', 'a')),
            parser.Success(tok=lexer.Token('id', 'b')))
        self.assertEqual(parser.Success(rule_name='a'),
                         parser.Success(rule_name='a'))
        self.assertNotEqual(parser.Success(rule_name='a'),
                            parser.Success(rule_name='b'))
        self.assertEqual(
            parser.Success(children=[parser.Success(rule_name='a')]),
            parser.Success(children=[parser.Success(rule_name='a')]))
        self.assertNotEqual(
            parser.Success(children=[parser.Success(rule_name='a')]),
            parser.Success(children=[parser.Success(rule_name='b')]))
        self.assertEqual(
            2,
            parser.Success(
                tok=lexer.Token('id', 'a'),
                children=[
                    parser.Success(rule_name='b'),
                    parser.Success(tok=lexer.Token('id', 'c')),
                ]
            ).num_toks())
        self.assertTrue(parser.Success().is_success())
        self.assertFalse(parser.Success(
            children=[parser.Failure(0, '')]).is_success())
        self.assertEqual(
            parser.Success(
                tok=lexer.Token('id', 'a'),
                children=[
                    parser.Success(rule_name='b'),
                    parser.Success(tok=lexer.Token('id', 'c')),
                ]).to_node(),
            parser.Node(
                tok=lexer.Token('id', 'a'),
                children=[
                    parser.Node(rule_name='b'),
                    parser.Node(tok=lexer.Token('id', 'c')),
                ])
        )
        self.assertEqual(parser.Success(
            children=[
                parser.Failure(0, 'error1'),
                parser.Failure(1, 'error2'),
            ]
        ).get_failures(),
            {
            parser.Failure(0, 'error1'),
            parser.Failure(1, 'error2'),

        })

    def test_failure(self):
        self.assertEqual(parser.Failure(1, 'error'),
                         parser.Failure(1, 'error'))
        self.assertNotEqual(parser.Failure(1, 'error'),
                            parser.Failure(1, 'noterror'))
        self.assertNotEqual(parser.Failure(1, 'error'),
                            parser.Failure(2, 'error'))
        self.assertFalse(parser.Failure(1, 'error').is_success())
        self.assertEqual(parser.Failure(1, 'error').get_failures(),
                         {parser.Failure(1, 'error')})

    def test_literal(self):
        self.assertEqual(parser.Literal('a'), parser.Literal('a'))
        self.assertNotEqual(parser.Literal('a'), parser.Literal('b'))
        self.assertEqual(
            parser.Literal('id')(
                parser.State(
                    parser=parser.Parser({}, ''),
                    toks=[lexer.Token('id', 'a')],
                )
            ),
            {parser.Success(tok=lexer.Token('id', 'a'), rule_name='id')})
        self.assertEqual(
            parser.Literal('id')(
                parser.State(
                    parser=parser.Parser({}, ''),
                    toks=[lexer.Token('notid', 'a')],
                )
            ),
            {parser.Failure(0, "failed to find literal 'id'")})

    def test_ref(self):
        self.assertEqual(parser.Ref('a'), parser.Ref('a'))
        self.assertNotEqual(parser.Ref('a'), parser.Ref('b'))
        self.assertEqual(
            parser.Ref('idref')(
                parser.State(
                    parser.Parser({'idref': parser.Literal('id')}, ''),
                    [lexer.Token('id', 'a')],
                )
            ),
            {parser.Success(
                rule_name='idref',
                children=[
                    parser.Success(
                        tok=lexer.Token('id', 'a'),
                        rule_name='id'
                    )])})
        self.assertEqual(
            parser.Ref('idref')(
                parser.State(
                    parser.Parser({}, ''),
                    [],
                )
            ),
            {parser.Failure(pos=0, msg="unknown ref 'idref'")})

    def test_and(self):
        self.assertEqual(
            parser.And(parser.Literal('a'), parser.Literal('b')),
            parser.And(parser.Literal('a'), parser.Literal('b'))
        )
        self.assertNotEqual(
            parser.And(parser.Literal('a'), parser.Literal('b')),
            parser.And(parser.Literal('a'), parser.Literal('c'))
        )
        for toks, expected_result in [
            (
                [lexer.Token('a', 'a'), lexer.Token('b', 'b')],
                {parser.Success(children=[
                    parser.Success(tok=lexer.Token('a', 'a'), rule_name='a'),
                    parser.Success(tok=lexer.Token('b', 'b'), rule_name='b'),
                ])}
            ),
            (
                [lexer.Token('a', 'a'), lexer.Token('a', 'a')],
                {parser.Success(children=[
                    parser.Success(tok=lexer.Token('a', 'a'), rule_name='a'),
                    parser.Failure(pos=1, msg="failed to find literal 'b'"),
                ])}
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    parser.And(
                        parser.Literal('a'),
                        parser.Literal('b'),
                    )(parser.State(parser.Parser({}, ''), toks)),
                    expected_result
                )

    def test_or(self):
        self.assertEqual(
            parser.Or(parser.Literal('a'), parser.Literal('b')),
            parser.Or(parser.Literal('a'), parser.Literal('b'))
        )
        self.assertNotEqual(
            parser.Or(parser.Literal('a'), parser.Literal('b')),
            parser.Or(parser.Literal('a'), parser.Literal('c'))
        )
        for toks, expected_result in [
            (
                [lexer.Token('a', 'a')],
                {
                    parser.Success(tok=lexer.Token('a', 'a'), rule_name='a'),
                    parser.Failure(pos=0, msg="failed to find literal 'b'"),
                }
            ),
            (
                [lexer.Token('c', 'c')],
                {
                    parser.Failure(pos=0, msg="failed to find literal 'a'"),
                    parser.Failure(pos=0, msg="failed to find literal 'b'"),
                }
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    parser.Or(
                        parser.Literal('a'),
                        parser.Literal('b'),
                    )(parser.State(parser.Parser({}, ''), toks)),
                    expected_result
                )

    def test_zero_or_more(self):
        self.assertEqual(
            parser.ZeroOrMore(parser.Literal('a')),
            parser.ZeroOrMore(parser.Literal('a'))
        )
        self.assertNotEqual(
            parser.ZeroOrMore(parser.Literal('a')),
            parser.ZeroOrMore(parser.Literal('b'))
        )
        for toks, expected_result in [
            (
                [lexer.Token('a', 'a')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                    ]),
                }
            ),
            (
                [lexer.Token('a', 'a'), lexer.Token('b', 'b')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a',
                        )
                    ]),
                }
            ),
            (
                [lexer.Token('a', 'a'), lexer.Token('a', 'a')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                    ]),
                }
            ),
            (
                [],
                {
                    parser.Success(),
                }
            ),
            (
                [lexer.Token('b', 'b')],
                {
                    parser.Success(),
                }
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    parser.ZeroOrMore(
                        parser.Literal('a')
                    )(parser.State(parser.Parser({}, ''), toks)),
                    expected_result
                )

    def test_one_or_more(self):
        self.assertEqual(
            parser.OneOrMore(parser.Literal('a')),
            parser.OneOrMore(parser.Literal('a'))
        )
        self.assertNotEqual(
            parser.OneOrMore(parser.Literal('a')),
            parser.OneOrMore(parser.Literal('b'))
        )
        for toks, expected_result in [
            (
                [lexer.Token('a', 'a')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                    ]),
                }
            ),
            (
                [lexer.Token('a', 'a'), lexer.Token('b', 'b')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a',
                        )
                    ]),
                }
            ),
            (
                [lexer.Token('a', 'a'), lexer.Token('a', 'a')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                    ]),
                }
            ),
            (
                [],
                {
                    parser.Success(children=[parser.Failure(
                        pos=0, msg="failed to find literal 'a'")]),
                }
            ),
            (
                [lexer.Token('b', 'b')],
                {
                    parser.Success(children=[parser.Failure(
                        pos=0, msg="failed to find literal 'a'")]),
                }
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    parser.OneOrMore(
                        parser.Literal('a')
                    )(parser.State(parser.Parser({}, ''), toks)),
                    expected_result
                )

    def test_zero_or_one(self):
        self.assertEqual(
            parser.ZeroOrOne(parser.Literal('a')),
            parser.ZeroOrOne(parser.Literal('a'))
        )
        self.assertNotEqual(
            parser.ZeroOrOne(parser.Literal('a')),
            parser.ZeroOrOne(parser.Literal('b'))
        )
        for toks, expected_result in [
            (
                [lexer.Token('a', 'a')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a'
                        ),
                    ]),
                }
            ),
            (
                [lexer.Token('a', 'a'), lexer.Token('b', 'b')],
                {
                    parser.Success(children=[
                        parser.Success(
                            tok=lexer.Token('a', 'a'),
                            rule_name='a',
                        )
                    ]),
                }
            ),
            (
                [],
                {
                    parser.Success(),
                }
            ),
            (
                [lexer.Token('b', 'b')],
                {
                    parser.Success(),
                }
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    parser.ZeroOrOne(
                        parser.Literal('a')
                    )(parser.State(parser.Parser({}, ''), toks)),
                    expected_result
                )

    def test_tail_pattern(self):
        for toks, expected in [
            (
                [token('a'), token('b'), token('c')],
                {empty_success(
                    token_success('a'),
                    empty_success(
                        empty_success(
                            token_success('b'),
                            token_success('c'),
                        )
                    ),
                )}
            ),
            (
                [token('a'), token('b'), token('c'),token('b'), token('c')],
                {empty_success(
                    token_success('a'),
                    empty_success(
                        empty_success(
                            token_success('b'),
                            token_success('c'),
                        ),
                        empty_success(
                            token_success('b'),
                            token_success('c'),
                        ),
                    ),
                )}
            ),
            (
                [token('a'), token('b'), token('c'),token('b'), token('c'),token('b'), token('c')],
                {empty_success(
                    token_success('a'),
                    empty_success(
                        empty_success(
                            token_success('b'),
                            token_success('c'),
                        ),
                        empty_success(
                            token_success('b'),
                            token_success('c'),
                        ),
                        empty_success(
                            token_success('b'),
                            token_success('c'),
                        ),
                    ),
                )}
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(
                    parser.And(
                        parser.Literal('a'),
                        parser.OneOrMore(
                            parser.And(
                                parser.Literal('b'),
                                parser.Literal('c'),
                            )
                        ),
                    )(parser.State(parser.Parser({}, ''), toks=toks)),
                    expected
                )

    def test_parser_eq(self):
        self.assertEqual(
            parser.Parser({'a': parser.Literal('a')}, 'a'),
            parser.Parser({'a': parser.Literal('a')}, 'a')
        )
        self.assertNotEqual(
            parser.Parser({'a': parser.Literal('a')}, 'a'),
            parser.Parser({'a': parser.Literal('b')}, 'a')
        )
        self.assertNotEqual(
            parser.Parser({'a': parser.Literal('a')}, 'a'),
            parser.Parser({'a': parser.Literal('a')}, 'b')
        )

    def test_parser_success(self):
        def node(rule_name: Optional[str], *children: parser.Node) -> parser.Node:
            return parser.Node(rule_name=rule_name, children=list(children))

        def tok(rule_name: str, val: str) -> parser.Node:
            return parser.Node(rule_name=rule_name, tok=lexer.Token(rule_name, val))

        def int_(val: int) -> parser.Node:
            return node('expr', tok('int', str(val)))

        def paren_expr(child: parser.Node) -> parser.Node:
            return node('expr', node('paren_expr', node(None, tok(
                '(', '('), child, tok(')', ')'))))

        for toks, expected in [
            (
                [lexer.Token('int', '1')],
                int_(1)
            ),
            (
                [lexer.Token('(', '('), lexer.Token(
                    'int', '1'), lexer.Token(')', ')')],
                paren_expr(int_(1))
            ),
        ]:
            with self.subTest(toks=toks):
                self.assertEqual(parser.Parser({
                    'expr': parser.Or(
                        parser.Literal('int'),
                        parser.Ref('paren_expr'),
                    ),
                    'paren_expr': parser.And(
                        parser.Literal('('),
                        parser.Ref('expr'),
                        parser.Literal(')'),
                    ),
                }, 'expr')(toks), expected)

    def test_parser_fail(self):
        for toks, expected in [
            (
                [lexer.Token('float', '3.14')],
                'parse error at \'3.14\': "failed to find literal \'(\'" "failed to find literal \'id\'" "failed to find literal \'int\'" "failed to find literal \'str\'"'
            ),
            (
                [lexer.Token('(', '('), lexer.Token('int', '1')],
                'parse error at end of input: "failed to find literal \')\'"'
            )
        ]:
            with self.subTest(toks=toks):
                try:
                    parser.Parser({
                        'exprs': parser.OneOrMore(
                            parser.Ref('expr')
                        ),
                        'expr': parser.Or(
                            parser.Literal('id'),
                            parser.Literal('int'),
                            parser.Literal('str'),
                            parser.Ref('paren_expr'),
                        ),
                        'paren_expr': parser.And(
                            parser.Literal('('),
                            parser.OneOrMore(
                                parser.Ref('expr')
                            ),
                            parser.Literal(')'),
                        ),
                    }, 'exprs')(toks)
                    self.assertFail()
                except parser.Error as e:
                    self.assertEqual(str(e), expected)


if __name__ == '__main__':
    unittest.main()
