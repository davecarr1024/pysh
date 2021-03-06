from __future__ import annotations
import processor
from typing import Sequence


class Literal(processor.Rule[str, str]):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __hash__(self) -> int:
        return hash(self.val)

    def __repr__(self) -> str:
        return f'Literal({repr(self.val)})'

    def __call__(self, context: processor.Context[str, str]) -> str:
        if not context.input.startswith(self.val):
            raise processor.Error(f'failed to match {self}')
        return self.val


class Class(processor.Rule[str, str]):
    def __init__(self, min: str, max: str):
        self.min = min
        self.max = max

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.min == rhs.min and self.max == rhs.max

    def __hash__(self) -> int:
        return hash((self.min, self.max))

    def __repr__(self) -> str:
        return f'Class(min={repr(self.min)}, max={repr(self.max)})'

    def __call__(self, context: processor.Context[str, str]) -> str:
        if not context.input:
            raise processor.Error('no input')
        c = context.input[0]
        if c < self.min or c > self.max:
            raise processor.Error(f'{repr(c)} failed to match {self}')
        return c


class Regex(processor.Processor[str, str]):
    def advance(self, input: str, output: str) -> str:
        return input[len(output):]

    def aggregate(self, context: processor.Context[str, str], outputs: Sequence[str]) -> str:
        return ''.join(outputs)

    def empty(self, input: str)->bool:
        return not input
