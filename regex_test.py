from __future__ import annotations
import regex
import processor
import unittest


class LiteralTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(regex.Literal('a'), regex.Literal('a'))
        self.assertNotEqual(regex.Literal('a'), regex.Literal('b'))

    def test_call(self):
        self.assertEqual(regex.Literal('a')(
            processor.Context(regex.Regex({}, ''), 'a')), 'a')
        with self.assertRaisesRegex(processor.Error, r"failed to match Literal\('a'\) at \'b\'"):
            regex.Literal('a')(processor.Context(regex.Regex({}, ''), 'b'))


class ClassTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(regex.Class('a', 'b'), regex.Class('a', 'b'))
        self.assertNotEqual(regex.Class('a', 'b'), regex.Class('c', 'b'))
        self.assertNotEqual(regex.Class('a', 'b'), regex.Class('a', 'c'))

    def test_call_success(self):
        for input in ['a', 'm', 'z']:
            with self.subTest(input=input):
                self.assertEqual(regex.Class('a', 'z')(
                    processor.Context(regex.Regex({}, ''), input)), input)

    def test_call_fail(self):
        with self.subTest(input=input):
            with self.assertRaisesRegex(processor.Error,
                                        r"failed to match Class\(min='a', max='z'\) at \'0\'"):
                regex.Class('a', 'z')(
                    processor.Context(regex.Regex({}, ''), '0'))


class RegexTest(unittest.TestCase):
    regex_ = regex.Regex({
        'root': processor.UntilEmpty(
            processor.And(
                regex.Literal('a'),
                regex.Class('0', '9'),
            )
        )
    }, 'root')

    def test_call_success(self):
        for input, output in [
            ('', ''),
            ('a0', 'a0'),
            ('a0a1', 'a0a1'),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(
                    self.regex_(input),
                    output
                )

    def test_call_failure(self):
        for input in [
            'b',
            'aa',
            'a0b',
        ]:
            with self.subTest(input=input):
                with self.assertRaises(processor.Error):
                    self.regex_(input)


if __name__ == '__main__':
    unittest.main()
