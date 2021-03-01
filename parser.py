from __future__ import annotations
from abc import ABC, abstractmethod
import lexer
from typing import Any, Callable, cast, Dict, List, NamedTuple, Optional, Set, Sequence, Tuple


class Error(Exception):
    pass


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
        return self._repr(0)

    def _repr(self, tabs: int = 0) -> str:
        return '\n%sNode(rule_name=%r, tok=%r)%s' % ('  ' * tabs, self.rule_name, self.tok, ''.join([child._repr(tabs+1) for child in self.children]))

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
    def __contains__(self, rule_name: str) -> bool: pass

    @abstractmethod
    def apply_rule(self, rule_name: str, state: State) -> Set[Result]: pass


class StackEntry(NamedTuple):
    pos: int
    rule_name: str

    def __str__(self)->str:
        return '%s@%d' % (self.rule_name, self.pos)


class Stack(NamedTuple):
    entries: List[StackEntry]

    def __str__(self)->str:
        return ','.join(map(str, self.entries))

    def __hash__(self)->int:
        return hash(tuple(self.entries))

    def has_entry(self, stack_entry: StackEntry)->bool:
        return stack_entry in self.entries

    def with_entry(self, stack_entry: StackEntry)->Stack:
        return Stack(entries=self.entries + [stack_entry])


class State(NamedTuple):
    parser: IParser
    toks: Sequence[lexer.Token]
    pos: int = 0
    stack: Stack = Stack(entries=[])

    def __len__(self) -> int:
        return len(self.toks) - self.pos

    def __bool__(self) -> bool:
        return self.pos < len(self.toks)

    def __str__(self) -> str:
        return 'State(pos=%d, stack=%s)' % (self.pos, self.stack)

    def tok(self) -> lexer.Token:
        if self.pos >= len(self.toks):
            raise Error('overflow')
        return self.toks[self.pos]

    def next(self, i: int = 1) -> State:
        return State(parser=self.parser,
                     toks=self.toks,
                     pos=self.pos+i,
                     stack=self.stack)

    def with_stack_entry(self, stack_entry: StackEntry) -> State:
        return State(parser=self.parser,
                     toks=self.toks,
                     pos=self.pos,
                     stack=self.stack.with_entry(stack_entry))


class Result(ABC):
    @abstractmethod
    def num_toks(self) -> int: pass

    @abstractmethod
    def is_success(self) -> bool: pass

    @abstractmethod
    def to_node(self) -> Node: pass

    @abstractmethod
    def get_failures(self) -> Set[Result]: pass

    @abstractmethod
    def _repr(self, tabs: int)->str: pass


class Success(Result):
    def __init__(
            self,
            tok: Optional[lexer.Token] = None,
            children: Optional[Sequence[Result]] = None,
            rule_name: Optional[str] = None):
        self.tok = tok
        self.children = children or []
        self.rule_name = rule_name

    def __eq__(self, rhs: object) -> bool:
        return (
            isinstance(rhs, Success)
            and self.tok == rhs.tok
            and self.children == rhs.children
            and self.rule_name == rhs.rule_name)

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.tok, tuple(self.children), self.rule_name))

    def __repr__(self) -> str:
        return self._repr(0)

    def _repr(self, tabs: int) -> str:
        return '\n%sSuccess(rule_name=%r, tok=%r)%s' % ('  ' * tabs, self.rule_name, self.tok, ''.join([child._repr(tabs+1) for child in self.children]))

    def num_toks(self) -> int:
        return (1 if self.tok else 0) + sum([child.num_toks() for child in self.children])

    def is_success(self) -> bool:
        return all([child.is_success() for child in self.children])

    def to_node(self) -> Node:
        return Node(tok=self.tok, rule_name=self.rule_name, children=[result.to_node() for result in self.children])

    def get_failures(self) -> Set[Result]:
        return set.union(set(), *[child.get_failures() for child in self.children])


class Failure(Result):
    def __init__(self, pos: int, msg: str):
        self.pos = pos
        self.msg = msg

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, Failure) and self.pos == rhs.pos and self.msg == rhs.msg

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.pos, self.msg))

    def __repr__(self) -> str:
        return self._repr(0)

    def _repr(self, tabs: int)->str:
        return '\n%sFailure(pos=%r, msg=%r)' % ('  ' * tabs, self.pos, self.msg)

    def num_toks(self) -> int:
        raise NotImplementedError()

    def is_success(self) -> bool:
        return False

    def to_node(self) -> Node:
        raise NotImplementedError()

    def get_failures(self) -> Set[Result]:
        return {self}


Rule = Callable[[State], Set[Result]]


enable_rule_logging = False


class RuleLogger:
    def __init__(self):
        self.tabs = 0

    def print(self, *s: Any)->None:
        if enable_rule_logging:
            print('%s%s' % ('  ' * self.tabs, ' '.join(map(str, s))))

    def indent(self):
        self.tabs += 1

    def dedent(self):
        self.tabs -= 1

    def start_rule(self, rule: Rule)->None:
        self.indent()
        self.print('start', rule)

    def end_rule(self, rule: Rule)->None:
        self.print('end', rule)
        self.dedent()

rule_logger = RuleLogger()        

class RuleLoggerContext:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __enter__(self)->RuleLoggerContext:
        rule_logger.start_rule(self.rule)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        rule_logger.end_rule(self.rule)

    def print(self, *s: Any)->None:
        rule_logger.print(*s)

class Literal:
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return 'Literal(%s)' % repr(self.val)

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            if state and state.tok().rule_name == self.val:
                return {Success(tok=state.tok(), rule_name=self.val)}
            else:
                return {Failure(state.pos, 'failed to find literal %r' % self.val)}


class Ref:
    def __init__(self, val: str):
        self.val = val

    def __repr__(self) -> str:
        return 'Ref(%s)' % repr(self.val)

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.val == rhs.val

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            if self.val in state.parser:
                return {
                    Success(rule_name=self.val, children=[result])
                    for result in state.parser.apply_rule(self.val, state)
                }
            else:
                return {Failure(state.pos, 'unknown ref %r' % self.val)}


class And:
    def __init__(self, rule: Rule, *rest_rules: Rule):
        self.rules = [rule] + list(rest_rules)

    def __repr__(self) -> str:
        return 'And(%s)' % ', '.join(map(str, self.rules))

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            resultss: List[List[Result]] = [
                [result] for result in self.rules[0](state)
            ]
            for rule in self.rules[1:]:
                next_resultss: List[List[Result]] = []
                for results in resultss:
                    if results[-1].is_success():
                        advance = sum([result.num_toks() for result in results])
                        if advance > 0:
                            for rule_result in rule(state.next(advance)):
                                next_resultss.append(results + [rule_result])
                    else:
                        next_resultss.append(results)
                resultss = next_resultss
            return {Success(children=results) for results in resultss}


class Or:
    def __init__(self, *rules: Rule):
        self.rules = rules

    def __repr__(self) -> str:
        return 'Or(%s)' % ', '.join(map(str, self.rules))

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            return set.union(set(), *[rule(state) for rule in self.rules])


class ZeroOrMore:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'ZeroOrMore(%s)' % self.rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            pending_resultss: Set[Tuple[Result, ...]] = set()
            pending_resultss.add(())
            final_resultss: Set[Tuple[Result, ...]] = set()
            while pending_resultss:
                next_resultss: Set[Tuple[Result, ...]] = set()
                for results in pending_resultss:
                    for rule_result in self.rule(state.next(sum([result.num_toks() for result in results]))):
                        if rule_result.is_success():
                            next_resultss.add(results + (rule_result,))
                        else:
                            final_resultss.add(results)
                pending_resultss = next_resultss
            return {Success(children=list(results)) for results in final_resultss}


class OneOrMore:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'OneOrMore(%s)' % self.rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            rule_results = self.rule(state)
            success_rule_results = {
                result for result in rule_results if result.is_success()}
            pending_resultss: Set[Tuple[Result, ...]] = {(result,) for result in success_rule_results}
            final_resultss: Set[Tuple[Result, ...]] = set()
            while pending_resultss:
                next_resultss: Set[Tuple[Result, ...]] = set()
                for results in pending_resultss:
                    advance = sum([result.num_toks() for result in results])
                    if advance > 0:
                        for rule_result in self.rule(state.next(advance)):
                            if rule_result.is_success() and rule_result.num_toks():
                                next_resultss.add(results + (rule_result,))
                            else:
                                final_resultss.add(results)
                    else:
                        final_resultss.add(results)
                        next_resultss.add(results)
                pending_resultss = next_resultss
            return {Success(children=list(results)) for results in final_resultss} | {Success(children=[result]) for result in rule_results - success_rule_results}


class ZeroOrOne:
    def __init__(self, rule: Rule):
        self.rule = rule

    def __repr__(self) -> str:
        return 'ZeroOrOne(%s)' % self.rule

    def __eq__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and self.rule == rhs.rule

    def __call__(self, state: State) -> Set[Result]:
        with RuleLoggerContext(self) as logger:
            results = {result for result in self.rule(
                state) if result.is_success()}
            return {Success(children=[result]) for result in results} if results else {Success()}


class HistoryEntry(NamedTuple):
    pos: int
    rule_name: str
    stack: Stack


class Parser(IParser):
    def __init__(self, rules: Dict[str, Rule], root: str):
        self.rules = rules
        self.root = root
        self.history: Set[HistoryEntry] = set()

    def __repr__(self):
        return 'Parser(rules=%s, root=%s)' % (self.rules, repr(self.root))

    def __eq__(self, rhs: object):
        return isinstance(rhs, self.__class__) and self.rules == rhs.rules and self.root == rhs.root

    def __contains__(self, rule_name: str) -> bool:
        return rule_name in self.rules

    def apply_rule(
        self,
        rule_name: str,
        state: State,
    ) -> Set[Result]:
        if rule_name not in self.rules:
            raise Error('unknown rule %r' % rule_name)
        history_entry = HistoryEntry(pos=state.pos,rule_name=rule_name, stack=state.stack)
        if history_entry in self.history:
            raise Error('history loop detected while applying rule %r state %s' % (rule_name, state))
        self.history.add(history_entry)
        stack_entry = StackEntry(pos=state.pos,rule_name=rule_name)
        if stack_entry in state.stack:
            raise Error('stack loop detected while applying rule %r state %s' % (rule_name, stack_entry))
        state = state.with_stack_entry(stack_entry)
        return self.rules[rule_name](state)

    def __call__(self, toks: Sequence[lexer.Token]) -> Node:
        self.history = set()
        results = Ref(self.root)(State(self, toks))
        successes = {result for result in results if result.is_success(
        ) and result.num_toks() == len(toks)}
        if len(successes) == 1:
            return list(successes)[0].to_node()
        elif len(successes) > 1:
            raise Error('ambiguous result %r' % successes)
        else:
            failures = {cast(Failure, result) for result in set.union(
                *[result.get_failures() for result in results])}
            if not failures:
                raise Error('unknown parse error')
            else:
                max_pos = max([failure.pos for failure in failures])
                max_failures = {
                    failure for failure in failures if failure.pos == max_pos}

                def format_pos(pos: int) -> str:
                    return repr(' '.join(
                        [tok.val for tok in toks[max_pos:min(len(toks), max_pos + 5)]])) if pos < len(toks) else 'end of input'
                raise Error('parse error at %s: %s' % (
                    format_pos(max_pos),
                    ' '.join(
                        map(repr, sorted([failure.msg for failure in max_failures])))
                ))
