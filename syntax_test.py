from __future__ import annotations
import lexer
import parser
import syntax
from typing import List as ListType, NamedTuple
import unittest


class Int(NamedTuple):
    val: int


class List(NamedTuple):
    vals: ListType[Int]


class Add(NamedTuple):
    lhs: Int
    rhs: Int


class Not(NamedTuple):
    op: Int


class SyntaxTest(unittest.TestCase):
    def test_variadic(self):
        self.assertEqual(
            syntax.variadic('list', List)(
                parser.Node(rule_name='list'),
                [Int(1), Int(2)]
            ),
            List([Int(1), Int(2)])
        )

    def test_nary(self):
        self.assertEqual(
            syntax.nary('list', 2, List)(
                parser.Node(rule_name='list'),
                [Int(1), Int(2)]
            ),
            List([Int(1), Int(2)])
        )
        self.assertEqual(
            syntax.nary('list', 2, List)(
                parser.Node(rule_name='list'),
                [Int(1)]
            ),
            None
        )

    def test_binary(self):
        self.assertEqual(
            syntax.binary('add', Add)(
                parser.Node(rule_name='add'),
                [Int(1), Int(2)]
            ),
            Add(Int(1), Int(2))
        )
        self.assertEqual(
            syntax.binary('add', Add)(
                parser.Node(rule_name='add'),
                [Int(1)]
            ),
            None
        )

    def test_unary(self):
        self.assertEqual(
            syntax.unary('not', Not)(
                parser.Node(rule_name='not'),
                [Int(1)]
            ),
            Not(Int(1))
        )
        self.assertEqual(
            syntax.unary('not', Not)(
                parser.Node(rule_name='not'),
                [Int(1), Int(2)]
            ),
            None
        )

    def test_terminal(self):
        self.assertEqual(
            syntax.terminal('int', lambda val: Int(int(val)))(
                parser.Node(rule_name='int', tok=lexer.Token('int', '1')),
                []
            ),
            Int(1)
        )
        self.assertEqual(
            syntax.terminal('int', lambda val: Int(int(val)))(
                parser.Node(rule_name='str', tok=lexer.Token('str', 'abc')),
                []
            ),
            None
        )

    def test_node(self):
        self.assertEqual(
            syntax.node(
                'foo',
                lambda node: Int(int(node.descendant('bar').tok_val()))
            )(
                parser.Node(
                    rule_name='foo',
                    children=[
                        parser.Node(rule_name='bar',
                                    tok=lexer.Token('int', '3'))
                    ]
                ),
                []
            ),
            Int(3)
        )

    def test_syntax(self):
        self.assertEqual(
            syntax.Syntax({
                syntax.terminal('int', lambda val: Int(int(val))),
                syntax.variadic('list', List),
                syntax.binary('add', Add),
                syntax.unary('not', Not),
            })(
                parser.Node(
                    rule_name='list',
                    children=[
                        parser.Node(rule_name='int',
                                    tok=lexer.Token('int', '1')),
                        parser.Node(
                            rule_name='add',
                            children=[
                                parser.Node(rule_name='int',
                                            tok=lexer.Token('int', '2')),
                                parser.Node(rule_name='int',
                                            tok=lexer.Token('int', '3')),
                            ]
                        ),
                        parser.Node(
                            rule_name='not',
                            children=[
                                parser.Node(rule_name='int',
                                            tok=lexer.Token('int', '4')),
                            ]
                        ),
                    ]
                )
            ),
            List([Int(1), Add(Int(2), Int(3)), Not(Int(4))])
        )


if __name__ == '__main__':
    unittest.main()
