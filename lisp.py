from __future__ import annotations
import lexer
import parser
import syntax
import loader
from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional, Sequence


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


class StrExpr(Expr):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'StrExpr(%r)' % self.val

    def eval(self, scope: Scope) -> Val:
        return StrVal(self.val)


class RefExpr(Expr):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __repr__(self) -> str:
        return 'RefExpr(%r)' % self.val

    def eval(self, scope: Scope) -> Val:
        if self.val not in scope:
            raise Error('unknown var %r' % self.val)
        else:
            return scope[self.val]


def builtins() -> Scope:
    return Scope()


def eval(input: str, scope: Optional[Scope] = None) -> Val:
    lexer_, parser_ = loader.lexer_and_parser(r'''
    id = "([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*";
    int = "-?[0-9]+";
    str = "'(^')*'";
    expr -> int | str | id;
    ''')
    expr: Expr = syntax.Syntax({
        syntax.rule_name('int', syntax.terminal(
            lambda val: IntExpr(int(val)))),
        syntax.rule_name('str', syntax.terminal(
            lambda val: StrExpr(val[1:-1]))),
        syntax.rule_name('id', syntax.terminal(RefExpr)),
    })(parser_(lexer_(input)))
    return expr.eval(scope or builtins())
