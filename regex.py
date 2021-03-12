from __future__ import annotations
import processor
from typing import Sequence

Context = processor.Context[str, str]
Rule = processor.Rule[str, str]


class Literal(Rule):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __hash__(self) -> int:
        return hash(self.val)

    def __repr__(self) -> str:
        return f'Literal({repr(self.val)})'

    def __call__(self, context: Context) -> str:
        if not context.input.startswith(self.val):
            raise context.error(f'failed to match {self}')
        return self.val


class Class(Rule):
    def __init__(self, min: str, max: str):
        self.min = min
        self.max = max

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.min == rhs.min and self.max == rhs.max

    def __hash__(self) -> int:
        return hash((self.min, self.max))

    def __repr__(self) -> str:
        return f'Class(min={repr(self.min)}, max={repr(self.max)})'

    def __call__(self, context: Context) -> str:
        if not context.input:
            raise context.error('no input')
        c = context.input[0]
        if c < self.min or c > self.max:
            raise context.error(f'failed to match {self}')
        return c


class Not(Rule):
    def __init__(self, rule: Rule):
        self.rule = rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __hash__(self) -> int:
        return hash(self.rule)

    def __repr__(self) -> str:
        return f'Not({self.rule})'

    def __call__(self, context: Context) -> str:
        if not context.input:
            raise context.error('no input')
        try:
            self.rule(context)
        except processor.Error:
            return context.input[0]
        raise context.error(f'failed to match {self}')


class Regex(processor.Processor[str, str]):
    def __init__(self, *rules: Rule):
        super().__init__({'root': processor.And(*rules)}, 'root')

    def advance(self, input: str, output: str) -> str:
        return input[len(output):]

    def aggregate(self, context: Context, outputs: Sequence[str]) -> str:
        return ''.join(outputs)

    def empty(self, input: str) -> bool:
        return not input
