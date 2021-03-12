from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Generic, List, Mapping, NamedTuple, Optional, Sequence, TypeVar


TI = TypeVar('TI')
TO = TypeVar('TO')


class Error(Exception):
    def __init__(self, msg: str, *inner_errors: Error):
        self.msg = msg
        self.inner_errors = inner_errors
        super().__init__(repr(self))

    def __eq__(self, rhs: object)->bool:
        return isinstance(rhs, self.__class__) and self.msg == rhs.msg and self.inner_errors == rhs.inner_errors

    def __hash__(self)->int:
        return hash((self.msg, self.inner_errors))

    def __repr__(self)->str:
        return self._repr(0)

    def _repr(self, tabs: int)->str:
        return '\n%s%s%s' % ('  ' * tabs, self.msg, ''.join([error._repr(tabs+1) for error in self.inner_errors]))


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

    def error(self, msg: str, *inner_errors: Error) -> Error:
        return Error(self.processor.error(self, msg), *inner_errors)

    @property
    def empty(self) -> bool:
        return self.processor.empty(self.input)


class Rule(Generic[TI, TO], ABC):
    @abstractmethod
    def __call__(self, context: Context[TI, TO]) -> TO: pass


class Ref(Rule[Any, Any]):
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
        for rule in self.rules:
            try:
                return context.aggregate([rule(context)])
            except Error as e:
                errors.append(e)
        raise context.error('or', *errors)


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
    def __init__(self, rules: Mapping[str, Rule[TI, TO]], root: str):
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

    def error(self, context: Context[TI,TO], msg: str)->str:
        return msg

    def apply_rule(self, rule_name: str, context: Context[TI, TO]) -> TO:
        if rule_name not in self.rules:
            raise context.error(f'unknown rule {repr(rule_name)}')
        try:
            output = self.rules[rule_name](context)
        except Error as error:
            raise context.error(f'while applying rule {repr(rule_name)}', error)
        return self.with_rule_name(output, rule_name)

    def process(self, input: TI) -> TO:
        return self.apply_rule(self.root, Context(self, input))
