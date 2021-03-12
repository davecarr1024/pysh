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
            processor.Context(regex.Regex(None), 'a')), 'a')
        with self.assertRaisesRegex(processor.Error, "regex error \"failed to match 'a'\" at 'b'"):
            regex.Literal('a')(processor.Context(regex.Regex(None), 'b'))


class ClassTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(regex.Class('a', 'b'), regex.Class('a', 'b'))
        self.assertNotEqual(regex.Class('a', 'b'), regex.Class('c', 'b'))
        self.assertNotEqual(regex.Class('a', 'b'), regex.Class('a', 'c'))

    def test_call_success(self):
        for input in ['a', 'm', 'z']:
            with self.subTest(input=input):
                self.assertEqual(regex.Class('a', 'z')(
                    processor.Context(regex.Regex(None), input)), input)

    def test_call_fail(self):
        with self.subTest(input=input):
            with self.assertRaisesRegex(processor.Error,
                                        "regex error 'failed to match \[a\-z\]' at '0'"):
                regex.Class('a', 'z')(
                    processor.Context(regex.Regex(None), '0'))


class NotTest(unittest.TestCase):
    def test_eq(self):
        self.assertEqual(regex.Not(regex.Literal('a')),regex.Not(regex.Literal('a')))
        self.assertNotEqual(regex.Not(regex.Literal('a')),regex.Not(regex.Literal('b')))

    def test_call_success(self):
        self.assertEqual(regex.Not(regex.Literal('a'))(regex.Context(regex.Regex(None), 'b')),'b')

    def test_call_fail(self):
        with self.assertRaisesRegex(processor.Error, "regex error \"failed to match \^'a'\" at 'a'"):
            regex.Not(regex.Literal('a'))(regex.Context(regex.Regex(None), 'a'))


class RegexTest(unittest.TestCase):
    regex_ = regex.Regex(
        processor.And(
            regex.Literal('a'),
            regex.Class('0', '9'),
        )
    )

    def test_call_success(self):
        for input, output in [
            ('a3', 'a3'),
            ('a4b', 'a4'),
        ]:
            with self.subTest(input=input, output=output):
                self.assertEqual(
                    self.regex_.process(input),
                    output
                )

    def test_call_failure(self):
        for input in [
            '',
            'b',
            'aa',
        ]:
            with self.subTest(input=input):
                with self.assertRaises(processor.Error):
                    self.regex_.process(input)


if __name__ == '__main__':
    unittest.main()
