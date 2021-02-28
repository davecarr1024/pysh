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

    def test_ref(self):
        self.assertEqual(lisp.Ref('a'), lisp.Ref('a'))
        self.assertNotEqual(lisp.Ref('a'), lisp.Ref('b'))
        self.assertEqual(
            lisp.Ref('a').eval(lisp.Scope(vals={'a': lisp.StrVal('b')})),
            lisp.StrVal('b'))
        with self.assertRaisesRegex(lisp.Error, 'unknown var \'a\''):
            lisp.Ref('a').eval(lisp.Scope())

    def test_add(self):
        self.assertEqual(
            lisp.Add().apply(lisp.Scope(), [lisp.IntVal(1)]),
            lisp.IntVal(1))
        self.assertEqual(
            lisp.Add().apply(lisp.Scope(), [lisp.IntVal(1), lisp.IntVal(2)]),
            lisp.IntVal(3))
        self.assertEqual(
            lisp.Add().apply(lisp.Scope(), [
                lisp.StrVal('a'), lisp.StrVal('b')]),
            lisp.StrVal('ab'))
        with self.assertRaisesRegex(lisp.Error, 'underflow'):
            lisp.Add().apply(lisp.Scope(), [])
        with self.assertRaisesRegex(lisp.Error, 'mismatched args'):
            lisp.Add().apply(lisp.Scope(), [lisp.StrVal('a'), lisp.IntVal(1)])

    def test_call(self):
        self.assertEqual(
            lisp.Call(lisp.Ref('a'),[lisp.Ref('b')]),
            lisp.Call(lisp.Ref('a'),[lisp.Ref('b')]))
        self.assertNotEqual(
            lisp.Call(lisp.Ref('a'),[lisp.Ref('b')]),
            lisp.Call(lisp.Ref('c'),[lisp.Ref('b')]))
        self.assertNotEqual(
            lisp.Call(lisp.Ref('a'),[lisp.Ref('b')]),
            lisp.Call(lisp.Ref('a'),[lisp.Ref('c')]))
        self.assertEqual(
            lisp.Call(lisp.Ref('+'), [lisp.IntExpr(1), lisp.IntExpr(2)]).eval(
                lisp.builtins()),
            lisp.IntVal(3))

    def test_eval(self):
        for input, scope, expected_output in [
            ('-123', None, lisp.IntVal(-123)),
            ("'foo'", None, lisp.StrVal('foo')),
            ('a', lisp.Scope(vals={'a': lisp.StrVal('b')}), lisp.StrVal('b')),
            ('(+ 1 (+ 2))', None, lisp.IntVal(3)),
        ]:
            with self.subTest(input=input, scope=scope, expected_output=expected_output):
                self.assertEqual(lisp.eval(input, scope), expected_output)


if __name__ == '__main__':
    unittest.main()
