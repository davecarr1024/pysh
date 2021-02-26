from __future__ import annotations
from typing import Callable, Sequence, Tuple, TypeVar

I = TypeVar('I')
O = TypeVar('O')
def test(f: Callable[[I],O], i: I, o: O)->None:
  try:
    r = f(i)
    assert r == o, 'unexpected output %s' % repr(r)
  except Exception as e:
    raise AssertionError('test of %s failed: input %s got exception: %s' % (repr(f), repr(i), e))

def test_cases(f: Callable[[I],O], vals: Sequence[Tuple[I,O]]):
  for i, o in vals:
    test(f, i, o)
