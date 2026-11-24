"""Postgres log sequence numbers (LSNs).

An LSN is a 64-bit byte position in the write-ahead log, written as two hexadecimal halves:
``16/B374D848``. Point-in-time recovery, backup labels and replication all speak in LSNs, so
they must be parsed, compared and subtracted exactly.
"""

from __future__ import annotations

import re
from functools import total_ordering

_LSN = re.compile(r"([0-9A-Fa-f]{1,8})/([0-9A-Fa-f]{1,8})")
_MAX = (1 << 64) - 1


@total_ordering
class Lsn:
    """A position in the write-ahead log."""

    __slots__ = ("_value",)

    def __init__(self, value: int) -> None:
        if not 0 <= value <= _MAX:
            raise ValueError("an LSN is a 64-bit unsigned position")
        self._value = value

    @classmethod
    def parse(cls, text: str) -> Lsn:
        match = _LSN.fullmatch(text.strip())
        if match is None:
            raise ValueError(f"{text!r} is not an LSN; expected the form 16/B374D848")
        return cls((int(match.group(1), 16) << 32) | int(match.group(2), 16))

    @property
    def value(self) -> int:
        return self._value

    def __int__(self) -> int:
        return self._value

    def __str__(self) -> str:
        return f"{self._value >> 32:X}/{self._value & 0xFFFFFFFF:X}"

    def __repr__(self) -> str:
        return f"Lsn({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Lsn) and self._value == other._value

    def __lt__(self, other: Lsn) -> bool:
        return self._value < other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __sub__(self, other: Lsn) -> int:
        """Return the number of WAL bytes between two LSNs (may be negative)."""
        return self._value - other._value

    def __add__(self, nbytes: int) -> Lsn:
        return Lsn(self._value + nbytes)
