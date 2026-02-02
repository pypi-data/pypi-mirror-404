"""LexoRank 内部：定点小数实现（LexoDecimal）。"""

from __future__ import annotations

from dataclasses import dataclass

from .lexo_integer import LexoInteger
from .numeral_systems import ILexoNumeralSystem


@dataclass(frozen=True, slots=True)
class LexoDecimal:
    """LexoRank 内部使用的“定点小数”表示。

    这里的 decimal = mag * base^(-sig)
    - `mag` 是一个 LexoInteger（本实现底层用 Python int 表示大整数）。
    - `sig` 是小数位数（以进制 base 为基数的“小数位”）。

    它主要服务于 LexoRank 的 `between` 运算，用于在两个 rank 之间计算中值。
    """

    mag: LexoInteger
    sig: int

    @staticmethod
    def half(system: ILexoNumeralSystem) -> "LexoDecimal":
        """返回给定进制系统下的 1/2（作为 LexoDecimal）。"""
        mid = int(system.get_base() / 2)  # match TS: (base/2)|0
        return LexoDecimal.make(LexoInteger(system, mid), 1)

    @staticmethod
    def parse(text: str, system: ILexoNumeralSystem) -> "LexoDecimal":
        """从字符串解析 LexoDecimal。"""
        if text is None:
            raise ValueError("text is None")

        radix = system.get_radix_point_char()
        partial_index = text.find(radix)
        if text.rfind(radix) != partial_index:
            raise ValueError(f"More than one {radix}")

        if partial_index < 0:
            return LexoDecimal.make(LexoInteger.parse(text, system), 0)

        int_str = text[:partial_index] + text[partial_index + 1 :]
        sig = len(text) - 1 - partial_index
        return LexoDecimal.make(LexoInteger.parse(int_str, system), sig)

    @staticmethod
    def from_integer(integer: LexoInteger) -> "LexoDecimal":
        """从 LexoInteger 构造 LexoDecimal（scale=0）。"""
        return LexoDecimal.make(integer, 0)

    @staticmethod
    def make(integer: LexoInteger, sig: int) -> "LexoDecimal":
        """从整数幅值 + scale 构造并标准化 LexoDecimal。"""
        if integer.is_zero():
            return LexoDecimal(integer, 0)

        zero_count = 0
        while zero_count < sig and integer.get_mag(zero_count) == 0:
            zero_count += 1

        if zero_count == 0:
            return LexoDecimal(integer, sig)

        new_integer = integer.shift_right(zero_count)
        new_sig = sig - zero_count
        return LexoDecimal(new_integer, new_sig)

    def get_system(self) -> ILexoNumeralSystem:
        """返回该小数所使用的进制系统。"""
        return self.mag.system

    def add(self, other: "LexoDecimal") -> "LexoDecimal":
        """对齐 scale 后相加。"""
        tmag = self.mag
        tsig = self.sig
        omag = other.mag
        osig = other.sig

        while tsig < osig:
            tmag = tmag.shift_left()
            tsig += 1

        while tsig > osig:
            omag = omag.shift_left()
            osig += 1

        return LexoDecimal.make(tmag.add(omag), tsig)

    def subtract(self, other: "LexoDecimal") -> "LexoDecimal":
        """对齐 scale 后相减。"""
        this_mag = self.mag
        this_sig = self.sig
        other_mag = other.mag
        other_sig = other.sig

        while this_sig < other_sig:
            this_mag = this_mag.shift_left()
            this_sig += 1

        while this_sig > other_sig:
            other_mag = other_mag.shift_left()
            other_sig += 1

        return LexoDecimal.make(this_mag.subtract(other_mag), this_sig)

    def multiply(self, other: "LexoDecimal") -> "LexoDecimal":
        """相乘（scale 相加）。"""
        return LexoDecimal.make(self.mag.multiply(other.mag), self.sig + other.sig)

    def floor(self) -> LexoInteger:
        """向下取整（丢弃小数部分）。"""
        return self.mag.shift_right(self.sig)

    def ceil(self) -> LexoInteger:
        """向上取整（有小数部分则进位）。"""
        if self.is_exact():
            return self.mag
        floor = self.floor()
        return floor.add(LexoInteger.one(floor.system))

    def is_exact(self) -> bool:
        """是否为整数（没有小数部分）。"""
        if self.sig == 0:
            return True
        base = self.mag.system.get_base()
        return abs(self.mag.value) % (base**self.sig) == 0

    def get_scale(self) -> int:
        """返回 scale（以 base 为单位的小数位数）。"""
        return self.sig

    def set_scale(self, nsig: int, ceiling: bool = False) -> "LexoDecimal":
        """将小数位数（scale）从 `self.sig` 缩减到 `nsig`。

        语义与 TS 实现保持一致，但修复了一个常见隐患：
        - 当 `ceiling=True` 时，不是“无条件 +1”，而是“仅当缩减 scale 会丢弃非 0 部分才进位”。

        举例（base=10）：
        - 12.3400 -> scale=2：丢弃的是 0，所以不应进位，结果 12.34
        - 12.3401 -> scale=2：丢弃的是 01，应进位，结果 12.35

        Args:
            nsig: 目标 scale（小数位数），小于 0 会被视作 0。
            ceiling: 是否采用“向上取整”语义。

        Returns:
            LexoDecimal: 缩减后的 decimal。
        """
        if nsig >= self.sig:
            return self

        if nsig < 0:
            nsig = 0

        diff = self.sig - nsig
        nmag = self.mag.shift_right(diff)
        if ceiling and diff > 0:
            # Only round up if we are actually discarding non-zero digits.
            base = self.mag.system.get_base()
            discarded = abs(self.mag.value) % (base**diff)
            if discarded != 0:
                nmag = nmag.add(LexoInteger.one(nmag.system))

        return LexoDecimal.make(nmag, nsig)

    def compare_to(self, other: "LexoDecimal") -> int:
        """对齐 scale 后比较大小。"""
        if self is other:
            return 0
        if other is None:
            return 1

        tmag = self.mag
        omag = other.mag
        if self.sig > other.sig:
            omag = omag.shift_left(self.sig - other.sig)
        elif self.sig < other.sig:
            tmag = tmag.shift_left(other.sig - self.sig)

        return tmag.compare_to(omag)

    def format(self) -> str:
        """按当前进制系统的小数点字符格式化为字符串。"""
        int_str = self.mag.format()
        if self.sig == 0:
            return int_str

        positive = self.mag.system.get_positive_char()
        negative = self.mag.system.get_negative_char()
        radix = self.mag.system.get_radix_point_char()

        head = int_str[0]
        special_head = head == positive or head == negative
        digits = int_str[1:] if special_head else int_str

        while len(digits) < self.sig + 1:
            digits = self.mag.system.to_char(0) + digits

        insert_at = len(digits) - self.sig
        digits = digits[:insert_at] + radix + digits[insert_at:]

        if insert_at == 0:
            digits = self.mag.system.to_char(0) + digits

        return (head + digits) if special_head else digits

    def equals(self, other: object) -> bool:
        """幅值与 scale 都一致则视为相等。"""
        if not isinstance(other, LexoDecimal):
            return False
        return self.mag.equals(other.mag) and self.sig == other.sig

    def __str__(self) -> str:
        """返回格式化后的字符串表示。"""
        return self.format()
