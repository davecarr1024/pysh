from __future__ import annotations
import processor
import regex
from typing import NamedTuple, Optional

class Location(NamedTuple):
    line: int
    col: int

    def __lt__(self, rhs: object) -> bool:
        return isinstance(rhs, self.__class__) and (self.line < rhs.line or self.col < rhs.col)


class Token(NamedTuple):
    rule_name: str
    val: str
    location: processor.Location
