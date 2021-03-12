from __future__ import annotations
import processor
import lexer
from typing import Dict, NamedTuple, Optional, Sequence, Tuple


class Input(NamedTuple):
    tokens: Sequence[lexer.Token]

    def empty(self) -> bool:
        return not self.tokens

    def advance(self, output: Node) -> Input:
        return Input(self.tokens[len(output):])

    def max_location(self) -> lexer.Location:
        return max([token.location for token in self.tokens])


class Node:
    def __init__(self, token: Optional[lexer.Token] = None, rule_name: Optional[str] = None, children: Optional[Tuple[Node, ...]] = None):
        self.token = token
        self.rule_name = rule_name
        self.children = children or ()

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.token == rhs.token and self.rule_name == rhs.rule_name and self.children == rhs.children

    def __hash__(self) -> int:
        return hash((self.token, self.rule_name, self.children))

    def __repr__(self) -> str:
        return self._repr(0)

    def _repr(self, tabs: int) -> str:
        return f'\n{"  " * tabs}Node(token={self.token}, rule_name={repr(self.rule_name)}' + ''.join([child._repr(tabs+1) for child in self.children])

    def __len__(self) -> int:
        return (1 if self.token else 0) + sum(map(len, self.children))

    def with_rule_name(self, rule_name: str) -> Node:
        return Node(self.token, rule_name, self.children)


Context = processor.Context[Input, Node]
Rule = processor.Rule[Input, Node]
Ref = processor.Ref[Input, Node]


class Literal(Rule):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __hash__(self) -> int:
        return hash(self.val)

    def __repr__(self) -> str:
        return f'Literal({repr(self.val)})'

    def __call__(self, context: Context) -> Node:
        if not context.input.tokens:
            raise context.error(f'no input')
        tok = context.input.tokens[0]
        if tok.rule_name != self.val:
            raise context.error(f'failed to match {tok}')
        return Node(token=tok)


class Parser(processor.Processor[Input, Node]):
    def advance(self, input: Input, output: Node) -> Input:
        return input.advance(output)

    def aggregate(self, context: Context, outputs: Sequence[Node]) -> Node:
        return Node(children=tuple(outputs))

    def empty(self, input: Input) -> bool:
        return input.empty()

    def with_rule_name(self, output: Node, rule_name: str) -> Node:
        return output.with_rule_name(rule_name)

    def aggregate_error_keys(self, context: Context, keys: Sequence[Input]) -> Input:
        return max(keys, key=Input.max_location)

    def parse(self, toks: Sequence[lexer.Token]) -> Node:
        return self.process(Input(toks))
