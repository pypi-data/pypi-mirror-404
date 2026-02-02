"""LexoRank 内部：进制系统（默认 base36）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ILexoNumeralSystem(Protocol):
    """LexoRank 使用的“进制系统”协议。"""

    def get_base(self) -> int:
        """返回进制 base（例如 36）。"""

    def get_positive_char(self) -> str:
        """返回正号字符（默认 '+'）。"""

    def get_negative_char(self) -> str:
        """返回负号字符（默认 '-'）。"""

    def get_radix_point_char(self) -> str:
        """返回小数点字符（本实现使用 ':' 作为 radix）。"""

    def to_digit(self, ch: str) -> int:
        """把单个字符转换为数字（0 <= digit < base）。"""

    def to_char(self, digit: int) -> str:
        """把数字转换为单个字符（0 <= digit < base）。"""


@dataclass(frozen=True, slots=True)
class LexoNumeralSystem36(ILexoNumeralSystem):
    """base36 的进制系统实现。"""

    _digits: str = "0123456789abcdefghijklmnopqrstuvwxyz"

    def get_base(self) -> int:
        """返回 base36 的 base 值：36。"""
        return 36

    def get_positive_char(self) -> str:
        """返回正号字符。"""
        return "+"

    def get_negative_char(self) -> str:
        """返回负号字符。"""
        return "-"

    def get_radix_point_char(self) -> str:
        """返回小数点字符（':'）。"""
        return ":"

    def to_digit(self, ch: str) -> int:
        """把字符转换为 base36 的数字值。"""
        if "0" <= ch <= "9":
            return ord(ch) - ord("0")
        if "a" <= ch <= "z":
            return ord(ch) - ord("a") + 10
        raise ValueError(f"Not valid digit: {ch!r}")

    def to_char(self, digit: int) -> str:
        """把 base36 的数字值转换为字符。"""
        if digit < 0 or digit >= self.get_base():
            raise ValueError(f"Digit out of range for base {self.get_base()}: {digit}")
        return self._digits[digit]


NUMERAL_SYSTEM_36 = LexoNumeralSystem36()
