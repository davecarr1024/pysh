from __future__ import annotations
import processor
import regex
from typing import Dict, NamedTuple, Optional, Sequence, Tuple


class Location(NamedTuple):
    line: int
    col: int

    def __lt__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and (self.line < rhs.line or self.col < rhs.col)

    def advance(self, output: Output) -> Location:
        line = self.line
        col = self.col
        for token in output.toks:
            for c in token.val:
                if c == '\n':
                    line += 1
                    col = 0
                else:
                    col += 1
        return Location(line, col)


class Input(NamedTuple):
    input: str
    location: Location

    def advance(self, output: Output) -> Input:
        return Input(self.input[sum(map(len, output.toks)):], self.location.advance(output))

    @property
    def empty(self) -> bool:
        return not self.input


class Token(NamedTuple):
    val: str
    location: Location
    rule_name: Optional[str] = None

    def with_rule_name(self, rule_name: str) -> Token:
        return Token(self.val, self.location, rule_name)

    def __len__(self) -> int:
        return len(self.val)


class Output(NamedTuple):
    toks: Tuple[Token, ...]

    def with_rule_name(self, rule_name: str) -> Output:
        return Output(tuple(tok.with_rule_name(rule_name) for tok in self.toks))

    @staticmethod
    def aggregate(outputs: Sequence[Output]) -> Output:
        return Output(sum([output.toks for output in outputs], ()))


Context = processor.Context[Input, Output]
Ref = processor.Ref[Input, Output]
Rule = processor.Rule[Input, Output]


class Literal(Rule):
    def __init__(self, val: regex.Regex):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __hash__(self) -> int:
        return hash(self.val)

    def __repr__(self) -> str:
        return f'Literal({self.val})'

    def __call__(self, context: Context) -> Output:
        try:
            return Output((Token(self.val.process(context.input.input), context.input.location),))
        except processor.Error as e:
            raise context.error(f'failed to apply regex {self.val}: {e.msg}')


class Lexer(processor.Processor[Input, Output]):
    def __init__(self, **regexes: regex.Regex):
        rules: Dict[str, Rule] = {
            '_root': processor.UntilEmpty(processor.Or(*[Ref(name) for name in regexes.keys()]))}
        for name, regex in regexes.items():
            if name.startswith('_'):
                raise processor.Error(
                    f'regex name {repr(name)} can\'t start with _')
            rules[name] = Literal(regex)
        super().__init__(rules, '_root')

    def advance(self, input: Input, output: Output) -> Input:
        return input.advance(output)

    def aggregate(self, context: Context, outputs: Sequence[Output]) -> Output:
        return Output.aggregate(outputs)

    def empty(self, input: Input) -> bool:
        return input.empty

    def with_rule_name(self, output: Output, rule_name: str) -> Output:
        return output if rule_name.startswith('_') else output.with_rule_name(rule_name)

    def aggregate_error_keys(self, context: Context, keys: Sequence[Input]) -> Input:
        return max(keys, key=lambda key: key.location)

    def lex(self, input: str) -> Sequence[Token]:
        return self.process(Input(input, Location(0, 0))).toks
