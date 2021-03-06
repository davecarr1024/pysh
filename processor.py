from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Generic, List, NamedTuple, Optional, Sequence, TypeVar


class Location(NamedTuple):
    line: int
    col: int

    def __lt__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and (self.line < rhs.line or self.col < rhs.col)


class Error(Exception):
    def __init__(self, msg: str, location: Optional[Location] = None):
        super().__init__(f'{msg} at {location}' if location else msg)
        self.msg = msg
        self.location = location

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.msg == rhs.msg and self.location == rhs.location

    def __hash__(self) -> int:
        return hash((self.msg, self.location))

    def __repr__(self) -> str:
        return f'Error(msg={repr(self.msg)}, location={self.location})'

    @staticmethod
    def aggregate(errors: Sequence[Error]) -> Error:
        loc_errors: Dict[Location, List[Error]] = {}
        non_loc_errors: List[Error] = []
        for error in errors:
            if error.location is None:
                non_loc_errors.append(error)
            else:
                loc_errors.setdefault(error.location, []).append(error)

        def msg(errors: Sequence[Error]) -> str:
            if not errors:
                return 'unknown error'
            elif len(errors) == 1:
                return errors[0].msg
            else:
                return '[%s]' % ', '.join([error.msg for error in errors])
        if loc_errors:
            max_loc = max(loc_errors.keys())
            return Error(msg(loc_errors[max_loc]), max_loc)
        else:
            return Error(msg(non_loc_errors))


TI = TypeVar('TI')
TO = TypeVar('TO')


class Rule(Generic[TI, TO], ABC):
    @abstractmethod
    def __call__(self, context: Context[TI, TO]) -> TO: pass


class Context(Generic[TI, TO]):
    def __init__(self, processor: Processor[TI, TO], input: TI):
        self.processor = processor
        self.input = input

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.processor == rhs.processor and self.input == rhs.input

    def __hash__(self) -> int:
        return hash((self.processor, self.input))

    def __repr__(self) -> str:
        return f'Context(processor={self.processor}, input={self.input})'

    def advance(self, output: TO) -> Context[TI, TO]:
        return Context(self.processor, self.processor.advance(self.input, output))

    def aggregate(self, outputs: Sequence[TO]) -> TO:
        return self.processor.aggregate(self, outputs)

    @property
    def empty(self) -> bool:
        return self.processor.empty(self.input)

    @property
    def location(self) -> Optional[Location]:
        return self.processor.location_of(self.input)


class Ref(Rule[TI, TO]):
    def __init__(self, val: str):
        self.val = val

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __hash__(self) -> int:
        return hash(self.val)

    def __repr__(self) -> str:
        return f'Ref({self.val})'

    def __call__(self, context: Context) -> TO:
        return context.aggregate([context.processor.apply_rule(self.val, context)])


class And(Rule[TI, TO]):
    def __init__(self, *rules: Rule[TI, TO]):
        self.rules = rules

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __hash__(self) -> int:
        return hash(self.rules)

    def __repr__(self) -> str:
        return f'And({self.rules})'

    def __call__(self, context: Context[TI, TO]) -> TO:
        outputs: List[TO] = []
        for rule in self.rules:
            output = rule(context)
            outputs.append(output)
            context = context.advance(output)
        return context.aggregate(outputs)


class Or(Rule[TI, TO]):
    def __init__(self, *rules: Rule[TI, TO]):
        self.rules = rules

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __hash__(self) -> int:
        return hash(self.rules)

    def __repr__(self) -> str:
        return f'Or({self.rules})'

    def __call__(self, context: Context[TI, TO]) -> TO:
        errors: List[Error] = []
        outputs: List[TO] = []
        for rule in self.rules:
            try:
                outputs.append(rule(context))
            except Error as e:
                errors.append(e)
        if len(outputs) > 1:
            raise Error(f'ambiguous or result: {outputs}', context.location)
        elif len(outputs) == 1:
            return outputs[0]
        else:
            raise Error.aggregate(errors)


class ZeroOrMore(Rule[TI, TO]):
    def __init__(self, rule: Rule[TI, TO]):
        self.rule = rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __hash__(self) -> int:
        return hash(self.rule)

    def __repr__(self) -> str:
        return f'ZeroOrMore({self.rule})'

    def __call__(self, context: Context[TI, TO]) -> TO:
        outputs: List[TO] = []
        while True:
            try:
                output = self.rule(context)
                outputs.append(output)
                context = context.advance(output)
            except Error:
                return context.aggregate(outputs)


class OneOrMore(Rule[TI, TO]):
    def __init__(self, rule: Rule[TI, TO]):
        self.rule = rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __hash__(self) -> int:
        return hash(self.rule)

    def __repr__(self) -> str:
        return f'OneOrMore({self.rule})'

    def __call__(self, context: Context[TI, TO]) -> TO:
        output = self.rule(context)
        outputs = [output]
        context = context.advance(output)
        while True:
            try:
                output = self.rule(context)
                outputs.append(output)
                context = context.advance(output)
            except Error:
                return context.aggregate(outputs)


class ZeroOrOne(Rule[TI, TO]):
    def __init__(self, rule: Rule[TI, TO]):
        self.rule = rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __hash__(self) -> int:
        return hash(self.rule)

    def __repr__(self) -> str:
        return f'ZeroOrOne({self.rule})'

    def __call__(self, context: Context[TI, TO]) -> TO:
        try:
            return self.rule(context)
        except Error:
            return context.aggregate([])


class UntilEmpty(Rule[TI, TO]):
    def __init__(self, rule: Rule[TI, TO]):
        self.rule = rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __hash__(self) -> int:
        return hash(self.rule)

    def __repr__(self) -> str:
        return f'UntilEmpty({self.rule})'

    def __call__(self, context: Context[TI, TO]) -> TO:
        outputs: List[TO] = []
        while not context.empty:
            output = self.rule(context)
            outputs.append(output)
            context = context.advance(output)
        return context.aggregate(outputs)


class Processor(Generic[TI, TO], ABC):
    def __init__(self, rules: Dict[str, Rule[TI, TO]], root: str):
        self.rules = rules
        self.root = root

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules and self.root == rhs.root

    def __hash__(self) -> int:
        return hash((self.rules, self.root))

    def __repr__(self) -> str:
        return f'Processor(rules={self.rules}, root={repr(self.root)})'

    @abstractmethod
    def advance(self, input: TI, output: TO) -> TI: pass

    @abstractmethod
    def aggregate(self, context: Context[TI, TO],
                  outputs: Sequence[TO]) -> TO: pass

    @abstractmethod
    def empty(self, input: TI) -> bool: pass

    def with_rule_name(self, output: TO, rule_name: str) -> TO:
        return output

    def location_of(self, input: TI) -> Optional[Location]:
        return None

    def apply_rule(self, rule_name: str, context: Context[TI, TO]) -> TO:
        if rule_name not in self.rules:
            raise Error(f'unknown rule {repr(rule_name)}', context.location)
        try:
            return self.rules[rule_name](context)
        except Error as e:
            raise Error(
                f'error while applying rule {repr(rule_name)}: {e}', e.location or context.location)

    def __call__(self, input: TI) -> TO:
        return self.apply_rule(self.root, Context(self, input))
