import lexer
import unittest


# class LexerTest(unittest.TestCase):
#     def test_take_while(self):
#         self.assertEqual(lexer.take_while(str.isalpha)('a1'), 'a')
#         self.assertEqual(lexer.take_while(str.isalpha)('1'), None)

#     def test_literal(self):
#         self.assertEqual(lexer.Literal('a'), lexer.Literal('a'))
#         self.assertNotEqual(lexer.Literal('a'), lexer.Literal('b'))
#         self.assertEqual(lexer.Literal('a')('ab'), 'a')
#         self.assertEqual(lexer.Literal('a')('b'), None)

#     def test_zero_or_more(self):
#         self.assertEqual(lexer.ZeroOrMore(lexer.Literal('a')),
#                          lexer.ZeroOrMore(lexer.Literal('a')))
#         self.assertNotEqual(
#             lexer.ZeroOrMore(lexer.Literal('a')),
#             lexer.ZeroOrMore(lexer.Literal('b')))
#         self.assertEqual(lexer.ZeroOrMore(lexer.Literal('a'))('b'), '')
#         self.assertEqual(lexer.ZeroOrMore(lexer.Literal('a'))('ab'), 'a')
#         self.assertEqual(lexer.ZeroOrMore(lexer.Literal('a'))('aab'), 'aa')

#     def test_one_or_more(self):
#         self.assertEqual(lexer.OneOrMore(lexer.Literal('a')),
#                          lexer.OneOrMore(lexer.Literal('a')))
#         self.assertNotEqual(lexer.OneOrMore(lexer.Literal('a')),
#                             lexer.OneOrMore(lexer.Literal('b')))
#         self.assertEqual(lexer.OneOrMore(lexer.Literal('a'))('b'), None)
#         self.assertEqual(lexer.OneOrMore(lexer.Literal('a'))('ab'), 'a')
#         self.assertEqual(lexer.OneOrMore(lexer.Literal('a'))('aab'), 'aa')

#     def test_zero_or_one(self):
#         self.assertEqual(lexer.ZeroOrOne(lexer.Literal('a')),
#                          lexer.ZeroOrOne(lexer.Literal('a')))
#         self.assertNotEqual(lexer.ZeroOrOne(lexer.Literal('a')),
#                             lexer.ZeroOrOne(lexer.Literal('b')))
#         self.assertEqual(lexer.ZeroOrOne(lexer.Literal('a'))('b'), '')
#         self.assertEqual(lexer.ZeroOrOne(lexer.Literal('a'))('ab'), 'a')

#     def test_and(self):
#         self.assertEqual(
#             lexer.And(lexer.Literal('a'), lexer.Literal('b')),
#             lexer.And(lexer.Literal('a'), lexer.Literal('b')))
#         self.assertNotEqual(
#             lexer.And(lexer.Literal('a'), lexer.Literal('b')),
#             lexer.And(lexer.Literal('a'), lexer.Literal('c')))
#         self.assertEqual(
#             lexer.And(lexer.Literal('a'), lexer.Literal('b'))('abc'),
#             'ab')
#         self.assertEqual(
#             lexer.And(lexer.Literal('a'), lexer.Literal('b'))('ac'),
#             None)

#     def test_or(self):
#         self.assertEqual(
#             lexer.Or(lexer.Literal('a'), lexer.Literal('b')),
#             lexer.Or(lexer.Literal('a'), lexer.Literal('b')))
#         self.assertNotEqual(
#             lexer.Or(lexer.Literal('a'), lexer.Literal('b')),
#             lexer.Or(lexer.Literal('a'), lexer.Literal('c')))
#         self.assertEqual(
#             lexer.Or(lexer.Literal('a'), lexer.Literal('b'))('b'),
#             'b')
#         self.assertEqual(
#             lexer.Or(lexer.Literal('a'), lexer.Literal('b'))('c'),
#             None)

#     def test_not(self):
#         self.assertEqual(lexer.Not(lexer.Literal('a')),
#                          lexer.Not(lexer.Literal('a')))
#         self.assertNotEqual(lexer.Not(lexer.Literal('a')),
#                             lexer.Not(lexer.Literal('b')))
#         self.assertEqual(lexer.Not(lexer.Literal('a'))('b'), 'b')
#         self.assertEqual(lexer.Not(lexer.Literal('a'))('a'), None)

#     def test_lexer(self):
#         self.assertEqual(
#             lexer.Lexer({'a': lexer.Literal('a')},{}),
#             lexer.Lexer({'a': lexer.Literal('a')},{}),
#         )
#         self.assertNotEqual(
#             lexer.Lexer({'a': lexer.Literal('a')},{}),
#             lexer.Lexer({'a': lexer.Literal('b')},{}),
#         )
#         toks = lexer.Lexer(
#             {'id': lexer.take_while(str.isalpha)},
#             {'ws': lexer.take_while(str.isspace)})(' a\nb ')
#         self.assertEqual([lexer.Token('id', 'a'), lexer.Token('id', 'b')], toks)
#         self.assertEqual(
#             [lexer.Location(line=0,col=1),lexer.Location(line=1,col=0)],
#             [tok.loc for tok in toks]
#         )
#         with self.assertRaisesRegex(Exception, 'lex error at 0'):
#             lexer.Lexer({'id': lexer.take_while(str.isalpha)}, {
#                         'ws': lexer.take_while(str.isspace)})('(a)')


if __name__ == '__main__':
    unittest.main()
