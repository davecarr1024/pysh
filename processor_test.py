from __future__ import annotations
import processor
from typing import Dict, NamedTuple, Optional, Sequence
import unittest

import unittest.util
unittest.util._MAX_LENGTH = 1000


class LocationTest(unittest.TestCase):
    def test_lt(self):
        self.assertLess(processor.Location(0, 0), processor.Location(0, 1))
        self.assertLess(processor.Location(0, 1), processor.Location(1, 0))


class ErrorTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(processor.Error('a'), processor.Error('a'))
        self.assertNotEqual(processor.Error('a'), processor.Error('b'))
        self.assertEqual(
            processor.Error('a', processor.Location(0, 0)),
            processor.Error('a', processor.Location(0, 0)))
        self.assertNotEqual(
            processor.Error('a', processor.Location(0, 0)),
            processor.Error('a', processor.Location(0, 1)))

    def test_aggregate(self):
        self.assertEqual(processor.Error.aggregate(
            []), processor.Error('unknown error'))
        self.assertEqual(
            processor.Error.aggregate([processor.Error('a')]),
            processor.Error('a'))
        self.assertEqual(
            processor.Error.aggregate(
                [processor.Error('a'), processor.Error('b')]),
            processor.Error('[a, b]'))
        self.assertEqual(
            processor.Error.aggregate(
                [processor.Error('a', processor.Location(0, 1))]),
            processor.Error('a', processor.Location(0, 1)))
        self.assertEqual(
            processor.Error.aggregate([
                processor.Error('a', processor.Location(0, 1)),
                processor.Error('b', processor.Location(0, 1)),
            ]),
            processor.Error('[a, b]', processor.Location(0, 1)))
        self.assertEqual(
            processor.Error.aggregate([
                processor.Error('a', processor.Location(0, 1)),
                processor.Error('b', processor.Location(0, 1)),
                processor.Error('c', processor.Location(0, 2)),
                processor.Error('d', processor.Location(0, 2)),
            ]),
            processor.Error('[c, d]', processor.Location(0, 2)))
        self.assertEqual(
            processor.Error.aggregate([
                processor.Error('a', processor.Location(0, 1)),
                processor.Error('b', processor.Location(0, 1)),
                processor.Error('c', processor.Location(0, 2)),
                processor.Error('d', processor.Location(0, 2)),
                processor.Error('e'),
            ]),
            processor.Error('[c, d]', processor.Location(0, 2)))


class ContextTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(
            processor.Context(IntFilter({}, 'a'), Input([1])),
            processor.Context(IntFilter({}, 'a'), Input([1]))
        )
        self.assertNotEqual(
            processor.Context(IntFilter({}, 'a'), Input([1])),
            processor.Context(IntFilter({}, 'a'), Input([2]))
        )
        self.assertNotEqual(
            processor.Context(IntFilter({}, 'a'), Input([1])),
            processor.Context(IntFilter({}, 'b'), Input([1]))
        )

    def test_advance(self):
        self.assertEqual(
            processor.Context(
                IntFilter({}, ''),
                Input([1, 2])).advance(Output([1])),
            processor.Context(IntFilter({}, ''), Input([2])))

    def test_aggregate(self):
        self.assertEqual(
            processor.Context(
                IntFilter({}, ''),
                Input([])).aggregate([Output([1]), Output([2])]),
            Output([1, 2])
        )

    def test_empty(self):
        self.assertTrue(processor.Context(IntFilter({}, ''), Input([])).empty)
        self.assertFalse(processor.Context(
            IntFilter({}, ''), Input([1])).empty)

    def test_location(self):
        self.assertEqual(
            processor.Context(
                IntFilter({}, ''),
                Input([], processor.Location(0, 1))).location,
            processor.Location(0, 1))
        self.assertIsNone(processor.Context(
            IntFilter({}, ''), Input([])).location)


class Input(NamedTuple):
    vals: Sequence[int]
    location: Optional[processor.Location] = None

    def empty(self) -> bool:
        return not self.vals

    def advance(self, output: Output) -> Input:
        return Input(self.vals[len(output.vals):],
                     processor.Location(self.location.line,
                                        self.location.col + len(output.vals)) if self.location else None)


class InputTest(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(Input([]).empty())
        self.assertFalse(Input([1]).empty())

    def test_advance(self):
        self.assertEqual(Input([1, 2]).advance(Output([1])), Input([2]))
        self.assertEqual(
            Input([1, 2], processor.Location(1, 1)).advance(Output([1])),
            Input([2], processor.Location(1, 2))
        )


class Output(NamedTuple):
    vals: Sequence[int]
    rule_name: Optional[str] = None

    def with_rule_name(self, rule_name):
        return Output(self.vals, rule_name)

    @staticmethod
    def aggregate(outputs: Sequence[Output]) -> Output:
        return Output(sum([output.vals for output in outputs], []))


class OutputTest(unittest.TestCase):
    def test_with_rule_name(self):
        self.assertEqual(Output([]).with_rule_name('a'), Output([], 'a'))

    def test_aggregate(self):
        self.assertEqual(
            Output.aggregate([Output([1]), Output([2])]),
            Output([1, 2])
        )


class Equals(processor.Rule[Input, Output]):
    def __init__(self, val: int):
        self.val = val

    def __call__(self, context: processor.Context[Input, Output]) -> Output:
        if not context.input.vals:
            raise processor.Error('no input', context.location)
        elif context.input.vals[0] != self.val:
            raise processor.Error(
                f'{context.input.vals[0]} != {self.val}', context.location)
        else:
            return Output([self.val])


class EqualsTest(unittest.TestCase):
    def test_call(self):
        def call(vals: Sequence[int]) -> Output:
            return Equals(1)(processor.Context(IntFilter({}, ''), Input(vals)))
        self.assertEqual(call([1]), Output([1]))
        with self.assertRaisesRegex(processor.Error, 'no input'):
            call([])
        with self.assertRaisesRegex(processor.Error, '2 != 1'):
            call([2])


class IntFilter(processor.Processor[Input, Output]):
    def __init__(self, rules: Dict[str, processor.Rule[Input, Output]], root: str):
        super().__init__(rules, root)

    def advance(self, input: Input, output: Output) -> Input:
        return input.advance(output)

    def aggregate(self, context: processor.Context[Input, Output], outputs: Sequence[Output]) -> Output:
        return Output.aggregate(outputs)

    def empty(self, input: Input) -> bool:
        return input.empty()

    def with_rule_name(self, output: Output, rule_name: str) -> Output:
        return output.with_rule_name(rule_name)

    def location_of(self, input: Input) -> Optional[processor.Location]:
        return input.location


class AndTest(unittest.TestCase):
    @staticmethod
    def call(vals: Sequence[int]) -> Output:
        return processor.And(Equals(1), Equals(2))(processor.Context(IntFilter({}, ''), Input(vals)))

    def test_call_success(self):
        for input, output in [
            ([1, 2], [1, 2]),
            ([1, 2, 3], [1, 2]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))

    def test_call_failure(self):
        for input in [[], [1], [2], [3]]:
            with self.subTest(input=input):
                with self.assertRaises(processor.Error):
                    self.call(input)


class OrTest(unittest.TestCase):
    @staticmethod
    def call(input_vals: Sequence[int], equals_vals: Optional[Sequence[int]] = None):
        return processor.Or(
            *[Equals(val) for val in equals_vals or [1, 2]])(
                processor.Context(IntFilter({}, ''), Input(input_vals)))

    def test_call_success(self):
        for input, output in [
            ([1], [1]),
            ([1, 2], [1]),
            ([2], [2]),
            ([2, 1], [2]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))

    def test_call_ambiguous_failure(self):
        with self.assertRaisesRegex(processor.Error, 'ambiguous or result'):
            self.call([1], [1, 1])

    def test_call_failure(self):
        with self.assertRaisesRegex(processor.Error, '[3 != 1, 3 != 2]'):
            self.call([3])


class ZeroOrMoreTest(unittest.TestCase):
    @staticmethod
    def call(vals: Sequence[int]) -> Output:
        return processor.ZeroOrMore(Equals(1))(processor.Context(IntFilter({}, ''), Input(vals)))

    def test_call(self):
        for input, output in [
            ([], []),
            ([2], []),
            ([1], [1]),
            ([1, 2], [1]),
            ([1, 1], [1, 1]),
            ([1, 1, 2], [1, 1]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))


class OneOrMoreTest(unittest.TestCase):
    @staticmethod
    def call(vals: Sequence[int]) -> Output:
        return processor.OneOrMore(Equals(1))(processor.Context(IntFilter({}, ''), Input(vals)))

    def test_call_success(self):
        for input, output in [
            ([1], [1]),
            ([1, 2], [1]),
            ([1, 1], [1, 1]),
            ([1, 1, 2], [1, 1]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))

    def test_call_failure(self):
        for input in [[], [2]]:
            with self.subTest(input=input):
                with self.assertRaises(processor.Error):
                    self.call(input)


class ZeroOrOneTest(unittest.TestCase):
    @staticmethod
    def call(vals: Sequence[int]) -> Output:
        return processor.ZeroOrOne(Equals(1))(processor.Context(IntFilter({}, ''), Input(vals)))

    def test_call(self):
        for input, output in [
            ([], []),
            ([2], []),
            ([1], [1]),
            ([1, 2], [1]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))


class UntilEmptyTest(unittest.TestCase):
    @staticmethod
    def call(vals: Sequence[int]) -> Output:
        return processor.UntilEmpty(Equals(1))(processor.Context(IntFilter({}, ''), Input(vals)))

    def test_call_success(self):
        for input, output in [
            ([], []),
            ([1], [1]),
            ([1], [1]),
            ([1, 1], [1, 1]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))

    def test_call_failure(self):
        for input in [[1, 2], [1, 1, 2]]:
            with self.subTest(input=input):
                with self.assertRaises(processor.Error):
                    self.call(input)


class RefTest(unittest.TestCase):
    @staticmethod
    def call(vals: Sequence[int]) -> Output:
        return processor.Ref('a')(processor.Context(IntFilter({
            'a': Equals(1),
        }, ''), Input(vals)))

    def test_call_success(self):
        for input, output in [
            ([1], [1]),
            ([1, 2], [1]),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(self.call(input), Output(output))

    def test_call_failure(self):
        for input in [[], [2]]:
            with self.subTest(input=input):
                with self.assertRaises(processor.Error):
                    self.call(input)

    def test_call_unknown_rule(self):
        with self.assertRaisesRegex(processor.Error, 'unknown rule \'a\''):
            processor.Ref('a')(processor.Context(IntFilter({}, ''), Input([])))


class ProcessorTest(unittest.TestCase):
    def test_apply_rule_success(self):
        self.assertEqual(
            IntFilter({'a': Equals(1)}, '').apply_rule(
                'a', processor.Context(IntFilter({}, ''), Input([1]))),
            Output([1])
        )

    def test_apply_rule_unknown_rule(self):
        with self.assertRaisesRegex(processor.Error, 'unknown rule \'a\''):
            IntFilter({}, '').apply_rule(
                'a', processor.Context(IntFilter({}, ''), Input([1])))

    def test_apply_rule_error(self):
        with self.assertRaisesRegex(processor.Error, 'error while applying rule \'a\': 2 != 1'):
            IntFilter({'a': Equals(1)}, '').apply_rule(
                'a', processor.Context(IntFilter({}, ''), Input([2])))

    def test_call(self):
        self.assertEqual(
            IntFilter({'a': Equals(1)}, 'a')(Input([1])),
            Output([1])
        )


if __name__ == '__main__':
    unittest.main()
