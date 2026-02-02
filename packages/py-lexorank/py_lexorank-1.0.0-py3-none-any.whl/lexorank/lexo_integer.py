"""LexoRank 内部：大整数实现（LexoInteger）。"""

from __future__ import annotations

from dataclasses import dataclass

from .numeral_systems import ILexoNumeralSystem


@dataclass(frozen=True, slots=True)
class LexoInteger:
    """LexoRank 内部的大整数实现（LexoInteger）。

    说明：
    - 这是对 Python `int` 的轻量封装，同时携带“进制系统”（base、符号字符、数字字符集等）。
    - 所有运算都会检查“进制系统一致”，避免把不同进制的数混在一起计算。
    """

    system: ILexoNumeralSystem
    value: int

    @staticmethod
    def parse(text: str, system: ILexoNumeralSystem) -> "LexoInteger":
        """从进制字符串解析 LexoInteger。"""
        if text is None:
            raise ValueError("text is None")

        s = text
        sign = 1
        if s.startswith(system.get_positive_char()):
            s = s[1:]
        elif s.startswith(system.get_negative_char()):
            s = s[1:]
            sign = -1

        if s == "":
            return LexoInteger.zero(system)

        base = system.get_base()
        magnitude = 0
        for ch in s:
            magnitude = magnitude * base + system.to_digit(ch)

        val = sign * magnitude
        if val == 0:
            return LexoInteger.zero(system)
        return LexoInteger(system, val)

    @staticmethod
    def zero(system: ILexoNumeralSystem) -> "LexoInteger":
        """返回给定进制系统下的 0。"""
        return LexoInteger(system, 0)

    @staticmethod
    def one(system: ILexoNumeralSystem) -> "LexoInteger":
        """返回给定进制系统下的 1。"""
        return LexoInteger(system, 1)

    def is_zero(self) -> bool:
        """是否为 0。"""
        return self.value == 0

    def is_one(self) -> bool:
        """是否为 1。"""
        return self.value == 1

    def negate(self) -> "LexoInteger":
        """取相反数（0 仍返回 0）。"""
        if self.value == 0:
            return self
        return LexoInteger(self.system, -self.value)

    def add(self, other: "LexoInteger") -> "LexoInteger":
        """同一进制系统下相加。"""
        self._check_system(other)
        return LexoInteger(self.system, self.value + other.value)

    def subtract(self, other: "LexoInteger") -> "LexoInteger":
        """同一进制系统下相减。"""
        self._check_system(other)
        return LexoInteger(self.system, self.value - other.value)

    def multiply(self, other: "LexoInteger") -> "LexoInteger":
        """同一进制系统下相乘。"""
        self._check_system(other)
        return LexoInteger(self.system, self.value * other.value)

    def shift_left(self, times: int = 1) -> "LexoInteger":
        """左移 times 位（按 base^times 乘法语义）。"""
        if times == 0 or self.value == 0:
            return self
        if times < 0:
            return self.shift_right(-times)

        base = self.system.get_base()
        return LexoInteger(self.system, self.value * (base**times))

    def shift_right(self, times: int = 1) -> "LexoInteger":
        """右移 times 位（按 base^times 整除语义）。"""
        if times <= 0:
            return self.shift_left(-times)
        if self.value == 0:
            return self

        base = self.system.get_base()
        divisor = base**times
        magnitude = abs(self.value) // divisor
        if magnitude == 0:
            return LexoInteger.zero(self.system)
        return LexoInteger(self.system, magnitude if self.value > 0 else -magnitude)

    def get_mag(self, index: int) -> int:
        """返回在 base 进制下第 `index` 位（0-based）的数字。"""
        if index < 0:
            raise ValueError("index must be >= 0")
        base = self.system.get_base()
        return (abs(self.value) // (base**index)) % base

    def compare_to(self, other: "LexoInteger") -> int:
        """同一进制系统下比较大小。"""
        self._check_system(other)
        if self.value < other.value:
            return -1
        if self.value > other.value:
            return 1
        return 0

    def equals(self, other: object) -> bool:
        """进制 base 与数值都一致则视为相等。"""
        if not isinstance(other, LexoInteger):
            return False
        return (
            self.system.get_base() == other.system.get_base()
            and self.value == other.value
        )

    def format(self) -> str:
        """按进制系统的数字字符集格式化为字符串。"""
        if self.value == 0:
            return self.system.to_char(0)

        base = self.system.get_base()
        magnitude = abs(self.value)
        digits: list[str] = []
        while magnitude > 0:
            magnitude, rem = divmod(magnitude, base)
            digits.append(self.system.to_char(rem))
        out = "".join(reversed(digits))
        return out if self.value > 0 else f"{self.system.get_negative_char()}{out}"

    def __str__(self) -> str:
        """返回格式化后的字符串表示。"""
        return self.format()

    def _check_system(self, other: "LexoInteger") -> None:
        if self.system.get_base() != other.system.get_base():
            raise ValueError("Expected numbers of same numeral system")
