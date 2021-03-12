from __future__ import annotations
import lexer
import loader
import parser
import processor
import regex
import unittest
import unittest.util

unittest.util._MAX_LENGTH = 1000


class LoaderTest(unittest.TestCase):
    def test_load_regex(self):
        for input, expected in [
            ('a', regex.Regex(regex.Literal('a'))),
            (
                'a*',
                regex.Regex(
                    processor.ZeroOrMore(
                        regex.Literal('a')
                    )
                )
            ),
            (
                'a+',
                regex.Regex(
                    processor.OneOrMore(
                        regex.Literal('a')
                    )
                )
            ),
            (
                'a?',
                regex.Regex(
                    processor.ZeroOrOne(
                        regex.Literal('a')
                    )
                )
            ),
            (
                'a!',
                regex.Regex(
                    processor.UntilEmpty(
                        regex.Literal('a')
                    )
                )
            ),
            (
                '^a',
                regex.Regex(
                    regex.Not(
                        regex.Literal('a')
                    )
                )
            ),
            (
                '(a)',
                regex.Regex(
                    regex.Literal('a')
                )
            ),
            (
                'ab',
                regex.Regex(
                    processor.And(
                        regex.Literal('a'),
                        regex.Literal('b'),
                    )
                )
            ),
            (
                'a|b',
                regex.Regex(
                    processor.Or(
                        regex.Literal('a'),
                        regex.Literal('b'),
                    )
                )
            ),
            (
                '[a-z]',
                regex.Regex(
                    regex.Class('a', 'z')
                )
            ),
            (
                '\\(',
                regex.Regex(
                    regex.Literal('(')
                )
            )
        ]:
            with self.subTest(input=input, expected=expected):
                self.assertEqual(loader.load_regex(input), expected)


if __name__ == '__main__':
    unittest.main()
