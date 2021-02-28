from __future__ import annotations
import lisp
import unittest


class LispTest(unittest.TestCase):
    def test_int_val(self):
        self.assertEqual(lisp.IntVal(1), lisp.IntVal(1))
        self.assertNotEqual(lisp.IntVal(1), lisp.IntVal(2))
        with self.assertRaisesRegex(lisp.Error, 'int not callable'):
            lisp.IntVal(1).apply(lisp.Scope(), [])

    def test_int_expr(self):
        self.assertEqual(lisp.IntExpr(1), lisp.IntExpr(1))
        self.assertNotEqual(lisp.IntExpr(1), lisp.IntExpr(2))
        self.assertEqual(lisp.IntExpr(1).eval(lisp.Scope()), lisp.IntVal(1))

    def test_str_val(self):
        self.assertEqual(lisp.StrVal('a'), lisp.StrVal('a'))
        self.assertNotEqual(lisp.StrVal('a'), lisp.StrVal('b'))
        with self.assertRaisesRegex(lisp.Error, 'str not callable'):
            lisp.StrVal('a').apply(lisp.Scope(), [])

    def test_str_expr(self):
        self.assertEqual(lisp.StrExpr('a'), lisp.StrExpr('a'))
        self.assertNotEqual(lisp.StrExpr('a'), lisp.StrExpr('b'))
        self.assertEqual(
            lisp.StrExpr('a').eval(lisp.Scope()),
            lisp.StrVal('a'))

    def test_eval(self):
        for input, scope, expected_output in [
            ('-123', None, lisp.IntVal(-123)),
            ("'foo'", None, lisp.StrVal('foo')),
        ]:
            with self.subTest(input=input, scope=scope, expected_output=expected_output):
                self.assertEqual(lisp.eval(input, scope), expected_output)


if __name__ == '__main__':
    unittest.main()
