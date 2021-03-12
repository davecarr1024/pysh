from __future__ import annotations
import lexer
import parser
import syntax
from typing import List as ListType, NamedTuple
import unittest


class _Expr:
    pass


class _Int(_Expr):
    def __init__(self, val: int):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, _Int) and self.val == rhs.val

    def __repr__(self)->str:
        return f'Int({self.val})'


class _Add(_Expr):
    def __init__(self, lhs: _Expr, rhs: _Expr):
        self.lhs = lhs
        self.rhs = rhs

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, _Add) and self.lhs == rhs.lhs and self.rhs == rhs.rhs

    def __repr__(self)->str:
        return f'Add({self.lhs}, {self.rhs})'


class _List(_Expr):
    def __init__(self, vals: ListType[_Expr]):
        self.vals = vals

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, _List) and self.vals == rhs.vals

    def __repr__(self)->str:
        return f'List({self.vals})'


class _Not(_Expr):
    def __init__(self, val: _Expr):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, _Not) and self.val == rhs.val

    def __repr__(self)->str:
        return f'Not({self.val})'


class SyntaxTest(unittest.TestCase):
    @staticmethod
    def list_rule() -> syntax.Rule:
        return syntax.rule_name(
            'list',
            lambda node, exprs: _List(list(exprs)))

    @staticmethod
    def add_rule() -> syntax.Rule:
        return syntax.rule_name('add', syntax.binary(_Add))

    @staticmethod
    def not_rule() -> syntax.Rule:
        return syntax.rule_name('not', syntax.unary(_Not))

    @staticmethod
    def int_rule() -> syntax.Rule:
        return syntax.rule_name('int', syntax.terminal(lambda val: _Int(int(val))))

    def test_rulename(self):
        self.assertEqual(
            self.list_rule()(
                parser.Node(rule_name='list'),
                [_Int(1), _Int(2)]
            ),
            _List([_Int(1), _Int(2)])
        )
        self.assertEqual(
            self.list_rule()(
                parser.Node(rule_name='notlist'),
                [_Int(1), _Int(2)]
            ),
            None
        )

    def test_nary(self):
        rule = syntax.nary(2, self.list_rule())
        self.assertEqual(
            rule(
                parser.Node(rule_name='list'),
                [_Int(1), _Int(2)]
            ),
            _List([_Int(1), _Int(2)])
        )
        self.assertEqual(
            rule(
                parser.Node(rule_name='list'),
                [_Int(1)]
            ),
            None
        )

    def test_binary(self):
        self.assertEqual(
            self.add_rule()(
                parser.Node(rule_name='add'),
                [_Int(1), _Int(2)]
            ),
            _Add(_Int(1), _Int(2))
        )
        self.assertEqual(
            self.add_rule()(
                parser.Node(rule_name='add'),
                [_Int(1)]
            ),
            None
        )

    def test_unary(self):
        self.assertEqual(
            self.not_rule()(
                parser.Node(rule_name='not'),
                [_Int(1)]
            ),
            _Not(_Int(1))
        )
        self.assertEqual(
            self.not_rule()(
                parser.Node(rule_name='not'),
                [_Int(1), _Int(2)]
            ),
            None
        )

    def test_terminal(self):
        self.assertEqual(
            self.int_rule()(
                parser.Node(rule_name='int', token=lexer.Token('1', 'int')),
                []
            ),
            _Int(1)
        )
        self.assertEqual(
            self.int_rule()(
                parser.Node(rule_name='str', token=lexer.Token('abc', 'str')),
                []
            ),
            None
        )

    def test_syntax(self):
        self.assertEqual(
            syntax.Syntax({
                self.int_rule(),
                self.list_rule(),
                self.add_rule(),
                self.not_rule(),
            })(
                parser.Node(
                    rule_name='list',
                    children=[
                        parser.Node(rule_name='int',
                                    token=lexer.Token('1', 'int')),
                        parser.Node(
                            rule_name='add',
                            children=[
                                parser.Node(rule_name='int',
                                            token=lexer.Token('2', 'int')),
                                parser.Node(rule_name='int',
                                            token=lexer.Token('3', 'int')),
                            ]
                        ),
                        parser.Node(
                            rule_name='not',
                            children=[
                                parser.Node(rule_name='int',
                                            token=lexer.Token('4', 'int')),
                            ]
                        ),
                    ]
                )
            ),
            [_List([_Int(1), _Add(_Int(2), _Int(3)), _Not(_Int(4))])]
        )


if __name__ == '__main__':
    unittest.main()
