from __future__ import annotations
from abc import ABC, abstractmethod
import lexer
from typing import Callable, Dict, List, NamedTuple, Optional, Sequence, Set, Tuple


class Error(Exception, ABC):
    @abstractmethod
    def max(self) -> Tuple[Optional[lexer.Location], Sequence[Error]]: pass


class TerminalError(Error):
    def __init__(self, msg: str, loc: Optional[lexer.Location] = None):
        self.msg = msg
        self.loc = loc

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.msg == rhs.msg and self.loc == rhs.loc

    def __repr__(self):
        return 'TerminalError(msg=%r, loc=%r)' % (self.msg, self.loc)

    def max(self) -> Tuple[Optional[lexer.Location], Sequence[Error]]:
        return self.loc, [self]


class CompoundError(Error):
    def __init__(self, children: Sequence[Error]):
        self.children = children

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.children == rhs.children

    def __repr__(self) -> str:
        return 'CompoundError(%r)' % self.children

    def max(self) -> Tuple[Optional[lexer.Location], Sequence[Error]]:
        loc_to_errors: Dict[lexer.Location, List[Error]] = {}
        no_loc_errors: List[Error] = []
        for loc, errors in [child.max() for child in self.children]:
            if loc:
                loc_to_errors.setdefault(loc, []).extend(errors)
            else:
                no_loc_errors.extend(errors)
        if not loc_to_errors:
            return None, no_loc_errors
        max_loc = max(loc_to_errors.keys())
        return max_loc, loc_to_errors[max_loc]


class ContextError(Error):
    def __init__(self, msg: str, child: Error):
        self.msg = msg
        self.child = child

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.msg == rhs.msg and self.child == rhs.child

    def __repr__(self) -> str:
        return 'ContextError(%r, %r)' % (self.msg, self.child)

    def max(self) -> Tuple[Optional[lexer.Location], Sequence[Error]]:
        loc, errors = self.child.max()
        return loc, [ContextError(self.msg, error) for error in errors]


class Node:
    def __init__(self, rule_name: Optional[str] = None,
                 tok: Optional[lexer.Token] = None,
                 children: Optional[Tuple[Node, ...]] = None):
        self.rule_name = rule_name
        self.tok = tok
        self.children = children or ()
        assert isinstance(self.children, tuple)

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule_name == rhs.rule_name and self.tok == rhs.tok and self.children == rhs.children

    def __hash__(self) -> int:
        return hash((self.rule_name, self.tok, self.children))

    def __repr__(self) -> str:
        return self._repr(0)

    def _repr(self, tabs: int) -> str:
        return '\n%sNode(rule_name=%r, tok=%r)%s' % ('  ' * tabs, self.rule_name, self.tok, ''.join([child._repr(tabs+1) for child in self.children]))

    def __len__(self) -> int:
        return (1 if self.tok is not None else 0) + sum(map(len, self.children))


class State(NamedTuple):
    parser: Parser
    toks: Sequence[lexer.Token]

    def after(self, node: Node) -> State:
        return State(parser=self.parser, toks=self.toks[len(node):])


Rule = Callable[[State], Node]


class Literal:
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return 'Literal(%r)' % self.val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __call__(self, state: State) -> Node:
        if state.toks and state.toks[0].rule_name == self.val:
            return Node(rule_name=self.val, tok=state.toks[0])
        if state.toks:
            raise TerminalError('failed to find literal %r' %
                                self.val, state.toks[0].loc)
        else:
            raise TerminalError('failed to find literal %r: eof' % self.val)


class Ref:
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return 'Ref(%r)' % self.val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __call__(self, state: State) -> Node:
        return Node(children=(state.parser.apply_rule(self.val, state),))


class And:
    def __init__(self, *rules: Rule):
        self.rules = rules

    def __repr__(self) -> str:
        return 'And(%r)' % self.rules

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __call__(self, state: State) -> Node:
        node = Node()
        for rule in self.rules:
            node.children += (rule(state.after(node)),)
        return node


class Or:
    def __init__(self, *rules: Rule):
        self.rules = rules

    def __repr__(self) -> str:
        return 'Or(%r)' % self.rules

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __call__(self, state: State) -> Node:
        errors: List[Error] = []
        for rule in self.rules:
            try:
                return Node(children=(rule(state),))
            except Error as e:
                errors.append(e)
        raise CompoundError(errors)


class ZeroOrMore:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'ZeroOrMore(%r)' % self.rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, state: State) -> Node:
        node = Node()
        while True:
            try:
                node.children += (self.rule(state.after(node)),)
            except Error:
                return node


class OneOrMore:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'OneOrMore(%r)' % self.rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, state: State) -> Node:
        node = Node(children=(self.rule(state),))
        while True:
            try:
                node.children += (self.rule(state.after(node)),)
            except Error:
                return node


class ZeroOrOne:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'ZeroOrOne(%r)' % self.rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, state: State) -> Node:
        try:
            return Node(children=(self.rule(state),))
        except Error:
            return Node()


class Parser:
    def __init__(self, rules: Dict[str, Rule], root: str):
        self.rules = rules
        self.root = root

    def __call__(self, toks: Sequence[lexer.Token], repeat_on_incomplete: bool = True) -> Node:
        try:
            node = self.apply_rule(self.root, State(parser=self, toks=toks))
            if repeat_on_incomplete and len(node) < len(toks):
                node = Node(children=(node,))
                while len(node) < len(toks):
                    node.children += (self.apply_rule(self.root,
                                                    State(parser=self, toks=toks).after(node)),)
        except Error as e:
            loc, errors = e.max()
            if len(errors) == 1:
                raise errors[0]
            else:
                raise CompoundError(errors)
        return node

    def apply_rule(self, rule_name: str, state: State) -> Node:
        if rule_name not in self.rules:
            raise TerminalError('unknown rule %r' % rule_name)
        try:
            node = self.rules[rule_name](state)
        except Error as e:
            raise ContextError('failed to apply rule %r' % rule_name, e)
        node.rule_name = rule_name
        return node
