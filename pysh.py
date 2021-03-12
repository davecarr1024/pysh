from __future__ import annotations
from typing import MutableMapping, Optional


class Error(Exception):
    pass


class Type:
    def __init__(self, name: str, parent: Optional[Type] = None):
        self.name = name
        self.parent = parent
        self.scope = Scope()

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.name == rhs.name and self.parent == rhs.parent and self.scope == rhs.scope

    def __hash__(self) -> int:
        return hash((self.name, self.parent, self.scope))

    def __repr__(self) -> str:
        return f'Type(name={self.name}, parent={self.parent}, scope={self.scope})'

    def compatible_with(self, type: Type) -> bool:
        return self == type or (self.parent.compatible_with(type) if self.parent else False)


class Var:
    def __init__(self, type: Type, val: Val):
        self.type = type
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.type == rhs.type and self.val == rhs.val

    def __hash__(self) -> int:
        return hash((self.type, self.val))

    def __repr__(self) -> str:
        return f'Var(type={self.type}, val={self.val})'

    def set(self, val):
        if not val.type.compatible_with(self.type):
            raise Error(f'val {val} incompatible with var {self}')
        self.val = val


class Val:
    def __init__(self, type: Type):
        self.type = type
        self.scope = Scope()

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.type == rhs.type and self.scope == rhs.scope

    def __hash__(self) -> int:
        return hash((self.type, self.scope))

    def __repr__(self) -> str:
        return f'Var(type={self.type}, scope={self.scope})'


class Scope:
    def __init__(self, parent: Optional[Scope] = None):
        self.vars: MutableMapping[str, Var] = {}
        self.parent = parent

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.vars == rhs.vars and self.parent == rhs.parent

    def __hash__(self) -> int:
        return hash((self.vars, self.parent))

    def __repr__(self) -> str:
        return f'Scope(vars={self.vars}, parent={repr(self.parent)})'

    def __contains__(self, key: str) -> bool:
        return key in self.vars or (key in self.parent if self.parent else False)

    def __getitem__(self, key: str) -> Val:
        if key in self.vars:
            return self.vars[key].val
        elif self.parent:
            return self.parent[key]
        else:
            raise Error(f'unknown var {repr(key)}')

    def __setitem__(self, key: str, val: Val):
        if key not in self.vars:
            self.vars[key] = Var(val.type, val)
        else:
            self.vars[key].set(val)
