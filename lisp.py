from __future__ import annotations
import lexer
import parser
import syntax
import loader
from abc import ABC, abstractmethod
from typing import Callable, cast, Dict, Optional, Sequence


class Error(Exception):
    pass


class Val(ABC):
    @abstractmethod
    def apply(self, scope: Scope, vals: Sequence[Val]) -> Val: pass


class Scope:
    def __init__(self, parent: Optional[Scope] = None, vals: Optional[Dict[str, Val]] = None):
        self.parent = parent
        self.vals = vals or {}

    def __contains__(self, key: str) -> bool:
        return key in self.vals or (self.parent is not None and key in self.parent)

    def __getitem__(self, key: str) -> Val:
        if key in self.vals:
            return self.vals[key]
        elif self.parent:
            return self.parent[key]
        else:
            raise KeyError(key)

    def __setitem__(self, key: str, val: Val):
        self.vals[key] = val

    def __repr__(self) -> str:
        return 'Scope(vals=%r, parent=%r)' % (self.vals, self.parent)


class Expr(ABC):
    @abstractmethod
    def eval(self, scope: Scope) -> Val: pass


class IntVal(Val):
    def __init__(self, val: int):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'IntVal(%d)' % self.val

    def apply(self, scope: Scope, vals: Sequence[Val]) -> Val:
        raise Error('int not callable')


class IntExpr(Expr):
    def __init__(self, val: int):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'IntExpr(%d)' % self.val

    def eval(self, scope: Scope) -> Val:
        return IntVal(self.val)


class StrVal(Val):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'StrVal(%r)' % self.val

    def apply(self, scope: Scope, vals: Sequence[Val]) -> Val:
        raise Error('str not callable')


class Add(Val):
    def apply(self, scope: Scope, vals: Sequence[Val]) -> Val:
        if len(vals) == 0:
            raise Error('underflow')
        elif len(vals) == 1:
            return vals[0]
        elif not all([type(val) == type(vals[0]) for val in vals[1:]]):
            raise Error('mismatched args %r' % vals)
        elif isinstance(vals[0], IntVal):
            return IntVal(sum([cast(IntVal, val).val for val in vals]))
        elif isinstance(vals[0], StrVal):
            return StrVal(''.join([cast(StrVal, val).val for val in vals]))
        else:
            raise Error('unknown arg type %r' % type(vals[0]))


class StrExpr(Expr):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'StrExpr(%r)' % self.val

    def eval(self, scope: Scope) -> Val:
        return StrVal(self.val)


class Ref(Expr):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'RefExpr(%r)' % self.val

    def eval(self, scope: Scope) -> Val:
        if self.val not in scope:
            raise Error('unknown var %r in %s' % (self.val, scope))
        else:
            return scope[self.val]


class Call(Expr):
    def __init__(self, op: Expr, args: Sequence[Expr]):
        self.op = op
        self.args = args

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.op == rhs.op and self.args == rhs.args

    def __repr__(self) -> str:
        return 'Call(op=%r, args=%r)' % (self.op, self.args)

    def eval(self, scope: Scope) -> Val:
        return self.op.eval(scope).apply(Scope(parent=scope), [arg.eval(scope) for arg in self.args])


def builtins() -> Scope:
    return Scope(vals={
        '+': Add(),
    })


def eval(input: str, scope: Optional[Scope] = None) -> Val:
    lexer_, parser_ = loader.lexer_and_parser(r'''
    id = "([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*";
    int = "-?[0-9]+";
    str = "'(^')*'";
    op = "\+";
    ws ~= " +";
    expr -> int | str | id | op | call;
    call -> "\(" expr+ "\)";
    ''')
    expr: Expr = syntax.Syntax({
        syntax.rule_name('int', syntax.terminal(
            lambda val: IntExpr(int(val)))),
        syntax.rule_name('str', syntax.terminal(
            lambda val: StrExpr(val[1:-1]))),
        syntax.rule_name('id', syntax.terminal(Ref)),
        syntax.rule_name('op', syntax.terminal(Ref)),
        syntax.rule_name('call', lambda node, exprs: Call(exprs[0], exprs[1:])),
    })(parser_(lexer_(input)))
    return expr.eval(scope or builtins())
