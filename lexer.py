from __future__ import annotations
import processor
import regex
from typing import cast, Mapping, MutableMapping, NamedTuple, Optional, Sequence, Tuple


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
    include: bool = True

    def with_rule_name(self, rule_name: str) -> Token:
        return Token(self.val, self.location, rule_name, self.include)

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
Rule = processor.Rule[Input, Output]


class Literal(Rule):
    def __init__(self, val: regex.Regex, include: bool = True):
        self.val = val
        self.include = include

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __hash__(self) -> int:
        return hash(self.val)

    def __repr__(self) -> str:
        return f'Literal(val={self.val}, include={self.include})'

    def __call__(self, context: Context) -> Output:
        try:
            return Output((Token(self.val.process(context.input.input), context.input.location, include=self.include),))
        except processor.Error as e:
            raise context.error(f'failed to apply regex {self.val}', e)


class Lexer(processor.Processor[Input, Output]):
    def __init__(self, regexes: Mapping[str, regex.Regex], silent_regexes: Mapping[str, regex.Regex]):
        super().__init__({}, '_root')
        self.add_rules(regexes, True)
        self.add_rules(silent_regexes, False)

    def __repr__(self):
        # return repr(self.rules)
        def format_rule(name: str, rule: Rule) -> str:
            literal = cast(Literal, rule)
            return '\n%s %s "%s";' % (name, '=' if literal.include else '~=', repr(literal.val))
        return ''.join([
            format_rule(name, rule)
            for name, rule in self.rules.items()
            if not name.startswith('_')
        ])

    def add_rules(self, rules: Mapping[str, regex.Regex], include: bool=True)->None:
        for name, rule in rules.items():
            self.add_rule(name, rule, include)

    def add_rule(self, name: str, rule: regex.Regex, include: bool=True)->None:
        if name in self.rules:
            raise processor.Error(f'duplicate rule {name}')
        self.rules[name] = Literal(rule, include)
        self.rules[self.root] = processor.UntilEmpty(processor.Or(*[processor.Ref(rule_name) for rule_name in self.rules.keys() if not rule_name.startswith('_')]))

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

    def error(self, context: Context, msg: str) -> str:
        return f'lex error {repr(msg)} at {context.input.location}'

    def lex(self, input: str) -> Sequence[Token]:
        return [tok for tok in self.process(Input(input, Location(0, 0))).toks if tok.include]
