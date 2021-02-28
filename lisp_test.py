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

    def test_eval(self):
        for input, scope, expected_output in [
            ('-123', None, lisp.IntVal(-123)),
        ]:
            with self.subTest(input=input, scope=scope, expected_output=expected_output):
                self.assertEqual(lisp.eval(input, scope), expected_output)


if __name__ == '__main__':
    unittest.main()
