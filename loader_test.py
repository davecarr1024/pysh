import lexer
import parser
import loader
import unittest
import unittest.util

unittest.util._MAX_LENGTH = 1000


class LoaderTest(unittest.TestCase):
    def test_lexer_rule(self):
        for rule_str, i, o in [
            ('[a-z]', 'pA', 'p'),
            ('[0-9]', '3', '3'),
            ('[0-9]', 'a', None),
            ('[a-z]*', 'abcd0', 'abcd'),
            ('[a-z][A-Z]*', 'bA0', 'bA'),
            ('([a-z][A-Z])*', 'aBcD123', 'aBcD'),
            ('[a-z]+', 'abc0', 'abc'),
            ('[a-z]+', '123', None),
            ('abc', 'abc', 'abc'),
            ('(a|[0-9])+', 'a3ab', 'a3a'),
            ('(a|[0-9])+', 'b', None),
            ('"(^")*"', '"foo"', '"foo"'),
            ('a(^a)*a', 'abc', None),
            ('\\[', '[a', '['),
            ('\\[', ']', None),
            ('a?', 'a', 'a'),
            ('[0-9]+', '20', '20'),
            ('-?', '-', '-'),
            ('-?', '', ''),
            ('-?[0-9]+', '-20', '-20'),
            ('-?[0-9]+', '20', '20'),
            ('-?[0-9]+', 'abc', None),
            ('([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*', '_a1D_', '_a1D_'),
        ]:
            with self.subTest(rule_str=rule_str, i=i, o=0):
                self.assertEqual(loader.lexer_rule(rule_str)(i), o)

    def test_lexer_and_parser(self):
        for s, cases in [
            (r'''
                id = "([a-z]|[A-Z]|_)([a-z]|[A-Z]|[0-9]|_)*";
                ws ~= " +";
                expr -> id;
            ''', [
                (
                    'abc',
                    parser.Node(
                        rule_name='expr',
                        children=[
                            parser.Node(rule_name='id',
                                        tok=lexer.Token('id', 'abc')),
                        ]
                    )
                ),
            ]),
        ]:
            l, p = loader.lexer_and_parser(s)
            for i, o in cases:
                with self.subTest(s=s, i=i, o=o):
                    self.assertEqual(p(l(i)), o)


if __name__ == '__main__':
    unittest.main()
