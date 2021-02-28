from __future__ import annotations
from abc import ABC, abstractmethod
import lexer
from typing import Callable, Dict, List, Optional, Set, Sequence, Tuple


class Node:
    def __init__(
            self,
            tok: Optional[lexer.Token] = None,
            children: Optional[Sequence[Node]] = None,
            rule_name: Optional[str] = None):
        self.tok = tok
        self.children = children or []
        self.rule_name = rule_name

    def __eq__(self, rhs: object) -> bool:
        return (
            isinstance(rhs, Node)
            and self.tok == rhs.tok
            and self.children == rhs.children
            and self.rule_name == rhs.rule_name)

    def __hash__(self) -> int:
        return hash((self.tok, tuple(self.children), self.rule_name))

    def __len__(self) -> int:
        return (1 if self.tok else 0) + sum(map(len, self.children))

    def __repr__(self) -> str:
        return 'Node(%s)' % ', '.join([
            '%s=%s' % (name, repr(val))
            for name, val in [
                (name, getattr(self, name))
                for name in dir(self)
                if not name.startswith('_')
            ]
            if val and not callable(val)
        ])

    def descendants(self, rule_name: str) -> Sequence[Node]:
        return sum(
            [child.descendants(rule_name) for child in self.children],
            [self] if self.rule_name == rule_name else [])

    def nary_descendants(self, rule_name: str, n: int) -> Sequence[Node]:
        descendants = self.descendants(rule_name)
        assert len(descendants) == n, (
            'unexpected number of descendants: got %d expected %d, rule_name %s in %s'
            % (len(descendants), n, rule_name, self))
        return descendants

    def binary_descendants(self, rule_name) -> Tuple[Node, Node]:
        descendants = self.nary_descendants(rule_name, 2)
        return descendants[0], descendants[1]

    def descendant(self, rule_name) -> Node:
        return self.nary_descendants(rule_name, 1)[0]

    def tok_val(self) -> str:
        assert self.tok, 'expected tok'
        return self.tok.val


class IParser(ABC):
    @abstractmethod
    def apply_rule(self, rule_name: str,
                   toks: Sequence[lexer.Token]) -> Set[Node]: pass


Rule = Callable[[IParser, Sequence[lexer.Token]], Set[Node]]


class Literal:
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return 'Literal(%s)' % repr(self.val)

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        if toks and toks[0].rule_name == self.val:
            return {Node(tok=toks[0], rule_name=self.val)}
        else:
            return set()


class Ref:
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return 'Ref(%s)' % repr(self.val)

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        return {
            Node(rule_name=self.val, children=[node])
            for node in parser.apply_rule(self.val, toks)
        }


class And:
    def __init__(self, rule: Rule, *rest_rules: Rule):
        self.rules = [rule] + list(rest_rules)

    def __repr__(self) -> str:
        return 'And(%s)' % ', '.join(map(str, self.rules))

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        def iter(
            rules: Sequence[Rule],
            toks: Sequence[lexer.Token],
        ) -> List[List[Node]]:
            return [
                [node]
                for node in rules[0](parser, toks)
            ] if len(rules) == 1 else [
                [node] + rest
                for node in rules[0](parser, toks)
                for rest in iter(rules[1:], toks[len(node):])
            ]
        return {Node(children=nodes) for nodes in iter(self.rules, toks)}


class Or:
    def __init__(self, *rules: Rule):
        self.rules = rules

    def __repr__(self) -> str:
        return 'Or(%s)' % ', '.join(map(str, self.rules))

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        return set.union(
            set(),
            *[
                {Node(children=[node])}
                for rule in self.rules
                for node in rule(parser, toks)
            ]
        )


class ZeroOrMore:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'ZeroOrMore(%s)' % self.rule

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        def iter(toks: Sequence[lexer.Token]) -> List[List[Node]]:
            nodes = self.rule(parser, toks)
            return [
                [node] + rest
                for node in nodes
                for rest in iter(toks[len(node):])
            ] if nodes else [[]]
        nodess = iter(toks)
        return {
            Node(children=nodes)
            for nodes in
            nodess
        } if nodess else {Node()}


class OneOrMore:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'OneOrMore(%s)' % self.rule

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        def iter(toks: Sequence[lexer.Token]) -> List[List[Node]]:
            nodes = self.rule(parser, toks)
            return [
                [node] + rest
                for node in nodes
                for rest in iter(toks[len(node):])
            ] if nodes else [[]]
        return {
            Node(children=[node]+rest)
            for node in self.rule(parser, toks)
            for rest in iter(toks[len(node):])
        }


class ZeroOrOne:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'ZeroOrOne(%s)' % self.rule

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, parser: IParser, toks: Sequence[lexer.Token]) -> Set[Node]:
        nodes = self.rule(parser, toks)
        return {Node(children=[node]) for node in nodes} if nodes else {Node()}


class Parser(IParser):
    def __init__(self, rules: Dict[str, Rule], root: str):
        self.rules = rules
        self.root = root

    def __repr__(self):
        return 'Parser(rules=%s, root=%s)' % (self.rules, repr(self.root))

    def __eq__(self, rhs: object):
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules and self.root == rhs.root

    def apply_rule(
        self,
        rule_name: str,
        toks: Sequence[lexer.Token],
    ) -> Set[Node]:
        assert rule_name in self.rules, 'unknown rule %s' % repr(rule_name)
        return self.rules[rule_name](self, toks)

    def __call__(self, toks: Sequence[lexer.Token]) -> Node:
        nodes = {node for node in Ref(self.root)(
            self, toks) if len(node) == len(toks)}
        assert nodes, 'parse error in %s' % toks
        return list(nodes)[0]
