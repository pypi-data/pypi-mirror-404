"""LexoRank 核心实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from .lexo_decimal import LexoDecimal
from .lexo_rank_bucket import BUCKET_0, LexoRankBucket
from .numeral_systems import NUMERAL_SYSTEM_36


@dataclass(frozen=True, slots=True)
class LexoRank:
    """LexoRank：用于“可插入排序（fractional indexing）”的排序键。

    你可以把它理解为一种可比较的字符串 rank：
    - rank 字符串可用于数据库排序（按字符串排序即可得到顺序）。
    - 在两个 rank 之间可以生成一个新的 rank（`between`），用于插入元素而不需要全量重排。

    典型用法：
    - 列表初始化：`min()/max()/middle()`。
    - 插入：`left.between(right)`。
    - 追加/前插：`rank.gen_next()` / `rank.gen_prev()`（注意边界行为见对应方法说明）。
    """

    bucket: LexoRankBucket
    decimal: LexoDecimal
    value: str

    _NUMERAL_SYSTEM: ClassVar = NUMERAL_SYSTEM_36

    _ZERO_DECIMAL: ClassVar[LexoDecimal | None] = None
    _ONE_DECIMAL: ClassVar[LexoDecimal | None] = None
    _EIGHT_DECIMAL: ClassVar[LexoDecimal | None] = None
    _MIN_DECIMAL: ClassVar[LexoDecimal | None] = None
    _MAX_DECIMAL: ClassVar[LexoDecimal | None] = None
    _MID_DECIMAL: ClassVar[LexoDecimal | None] = None
    _INITIAL_MIN_DECIMAL: ClassVar[LexoDecimal | None] = None
    _INITIAL_MAX_DECIMAL: ClassVar[LexoDecimal | None] = None

    @classmethod
    def _zero_decimal(cls) -> LexoDecimal:
        """返回常量 0（base36）对应的 LexoDecimal（缓存）。"""
        if cls._ZERO_DECIMAL is None:
            cls._ZERO_DECIMAL = LexoDecimal.parse("0", cls._NUMERAL_SYSTEM)
        return cls._ZERO_DECIMAL

    @classmethod
    def _one_decimal(cls) -> LexoDecimal:
        """返回常量 1（base36）对应的 LexoDecimal（缓存）。"""
        if cls._ONE_DECIMAL is None:
            cls._ONE_DECIMAL = LexoDecimal.parse("1", cls._NUMERAL_SYSTEM)
        return cls._ONE_DECIMAL

    @classmethod
    def _eight_decimal(cls) -> LexoDecimal:
        """返回常量 8（base36）对应的 LexoDecimal（缓存）。

        说明：
        - 版本的 LexoRank 使用 +/-8 作为 `gen_next/gen_prev` 的默认步进单位，
          这是一个工程折中：在常见场景下能在不“膨胀字符串”的前提下留出足够插入空间。
        """
        if cls._EIGHT_DECIMAL is None:
            cls._EIGHT_DECIMAL = LexoDecimal.parse("8", cls._NUMERAL_SYSTEM)
        return cls._EIGHT_DECIMAL

    @classmethod
    def _min_decimal(cls) -> LexoDecimal:
        """返回 bucket 内的最小 decimal（缓存）。"""
        if cls._MIN_DECIMAL is None:
            cls._MIN_DECIMAL = cls._zero_decimal()
        return cls._MIN_DECIMAL

    @classmethod
    def _max_decimal(cls) -> LexoDecimal:
        """返回 bucket 内的最大 decimal（缓存）。

        说明：
        - 这里的上界不是 Python 的“无穷大”，而是一个固定的哨兵上界（sentinel）。
        - 对应 base36 下：`zzzzzz:`（字符串格式化后）。
        """
        if cls._MAX_DECIMAL is None:
            cls._MAX_DECIMAL = LexoDecimal.parse(
                "1000000", cls._NUMERAL_SYSTEM
            ).subtract(cls._one_decimal())
        return cls._MAX_DECIMAL

    @classmethod
    def _mid_decimal(cls) -> LexoDecimal:
        """返回 bucket 内 min/max 的中间值（缓存）。"""
        if cls._MID_DECIMAL is None:
            cls._MID_DECIMAL = cls.between_decimals(
                cls._min_decimal(), cls._max_decimal()
            )
        return cls._MID_DECIMAL

    @classmethod
    def _initial_min_decimal(cls) -> LexoDecimal:
        """返回 bucket 的“初始最小附近”decimal（缓存）。"""
        if cls._INITIAL_MIN_DECIMAL is None:
            cls._INITIAL_MIN_DECIMAL = LexoDecimal.parse("100000", cls._NUMERAL_SYSTEM)
        return cls._INITIAL_MIN_DECIMAL

    @classmethod
    def _initial_max_decimal(cls) -> LexoDecimal:
        """返回 bucket 的“初始最大附近”decimal（缓存）。"""
        if cls._INITIAL_MAX_DECIMAL is None:
            ch = cls._NUMERAL_SYSTEM.to_char(cls._NUMERAL_SYSTEM.get_base() - 2)
            cls._INITIAL_MAX_DECIMAL = LexoDecimal.parse(
                f"{ch}00000", cls._NUMERAL_SYSTEM
            )
        return cls._INITIAL_MAX_DECIMAL

    @classmethod
    def min(cls) -> "LexoRank":
        """返回全局最小 rank（bucket=0）。

        该 rank 通常作为列表“最前”的哨兵值（sentinel）。

        Returns:
            LexoRank: 最小 rank。
        """
        return cls.from_parts(BUCKET_0, cls._min_decimal())

    @classmethod
    def max(cls, bucket: LexoRankBucket = BUCKET_0) -> "LexoRank":
        """返回某个 bucket 内的最大 rank（默认 bucket=0）。

        注意：这是“该 bucket 的上界哨兵值”，通常不建议给真实元素直接使用 max，
        否则在其后追加时可用空间会非常有限。

        Args:
            bucket: 分桶标识（0/1/2）。

        Returns:
            LexoRank: 最大 rank。
        """
        return cls.from_parts(bucket, cls._max_decimal())

    @classmethod
    def middle(cls) -> "LexoRank":
        """返回一个“居中”的 rank（bucket=0），用于初始化列表的第一个元素。

        Returns:
            LexoRank: 中间 rank。
        """
        min_rank = cls.min()
        return min_rank.between(cls.max(min_rank.bucket))

    @classmethod
    def initial(cls, bucket: LexoRankBucket) -> "LexoRank":
        """返回 bucket 的“初始可用 rank”。

        这是一个工程取舍：在 min 与 max 之间预留空间，便于后续 `gen_next/gen_prev`
        生成更密集的 rank 时减少 rank 变长的概率。

        Args:
            bucket: 分桶标识（0/1/2）。

        Returns:
            LexoRank: bucket 对应的初始 rank。
        """
        if bucket.equals(BUCKET_0):
            return cls.from_parts(bucket, cls._initial_min_decimal())
        return cls.from_parts(bucket, cls._initial_max_decimal())

    @classmethod
    def parse(cls, text: str) -> "LexoRank":
        """从字符串解析 LexoRank。

        字符串格式：`<bucket>|<decimal>`，例如：`0|0i0000:`
        - bucket：'0' / '1' / '2'
        - decimal：36 进制数字 + 可选 ':' 表示小数点（本实现使用 ':' 作为 radix char）

        Args:
            text: rank 字符串。

        Returns:
            LexoRank: 解析得到的 rank。

        Raises:
            ValueError: 格式不合法或 bucket 非法。
        """
        parts = text.split("|")
        if len(parts) != 2:
            raise ValueError(f"Invalid LexoRank: {text!r}")
        bucket = LexoRankBucket.from_str(parts[0])
        decimal = LexoDecimal.parse(parts[1], cls._NUMERAL_SYSTEM)
        return cls.from_parts(bucket, decimal)

    @classmethod
    def from_parts(cls, bucket: LexoRankBucket, decimal: LexoDecimal) -> "LexoRank":
        """用 bucket + decimal 直接构造 LexoRank，并生成可比较的 `value` 字符串。

        你通常不需要手动调用它；更常见的入口是 `min/max/middle/parse/between`。
        """
        if decimal.get_system().get_base() != cls._NUMERAL_SYSTEM.get_base():
            raise ValueError("Expected same numeral system")
        value = f"{bucket.format()}|{cls._format_decimal(decimal)}"
        return LexoRank(bucket=bucket, decimal=decimal, value=value)

    @staticmethod
    def between_decimals(o_left: LexoDecimal, o_right: LexoDecimal) -> LexoDecimal:
        """计算两个 decimal 之间的“中间值”。

        这是 LexoRank 的核心：在不改变两侧元素 rank 的情况下生成一个新的可排序 key。
        该方法仅处理数值层面，不关心 bucket 拼接与字符串格式化。
        """
        if o_left.get_system().get_base() != o_right.get_system().get_base():
            raise ValueError("Expected same system")

        left = o_left
        right = o_right

        if o_left.get_scale() < o_right.get_scale():
            n_left = o_right.set_scale(o_left.get_scale(), ceiling=False)
            if o_left.compare_to(n_left) >= 0:
                return LexoRank._mid(o_left, o_right)
            right = n_left

        if o_left.get_scale() > right.get_scale():
            n_left = o_left.set_scale(right.get_scale(), ceiling=True)
            if n_left.compare_to(right) >= 0:
                return LexoRank._mid(o_left, o_right)
            left = n_left

        scale = left.get_scale()
        while scale > 0:
            n_scale1 = scale - 1
            n_left1 = left.set_scale(n_scale1, ceiling=True)
            n_right = right.set_scale(n_scale1, ceiling=False)
            cmp = n_left1.compare_to(n_right)
            if cmp == 0:
                return LexoRank._check_mid(o_left, o_right, n_left1)
            if n_left1.compare_to(n_right) > 0:
                break

            scale = n_scale1
            left = n_left1
            right = n_right

        mid = LexoRank._middle_internal(o_left, o_right, left, right)

        m_scale = mid.get_scale()
        while m_scale > 0:
            n_scale = m_scale - 1
            n_mid = mid.set_scale(n_scale)
            if o_left.compare_to(n_mid) >= 0 or n_mid.compare_to(o_right) >= 0:
                break
            mid = n_mid
            m_scale = n_scale

        return mid

    @staticmethod
    def _middle_internal(
        lbound: LexoDecimal, rbound: LexoDecimal, left: LexoDecimal, right: LexoDecimal
    ) -> LexoDecimal:
        """在给定边界/裁剪后的左右值之间计算候选中间值，并做边界校验。"""
        mid = LexoRank._mid(left, right)
        return LexoRank._check_mid(lbound, rbound, mid)

    @staticmethod
    def _check_mid(
        lbound: LexoDecimal, rbound: LexoDecimal, mid: LexoDecimal
    ) -> LexoDecimal:
        """确保 mid 严格落在 (lbound, rbound) 内；否则退回重新取中间值。"""
        if lbound.compare_to(mid) >= 0:
            return LexoRank._mid(lbound, rbound)
        if mid.compare_to(rbound) >= 0:
            return LexoRank._mid(lbound, rbound)
        return mid

    @staticmethod
    def _mid(left: LexoDecimal, right: LexoDecimal) -> LexoDecimal:
        """返回 left 与 right 的中间值（尝试在不增加小数位的前提下取中）。"""
        summed = left.add(right)
        mid = summed.multiply(LexoDecimal.half(left.get_system()))
        scale = max(left.get_scale(), right.get_scale())

        if mid.get_scale() > scale:
            round_down = mid.set_scale(scale, ceiling=False)
            if round_down.compare_to(left) > 0:
                return round_down
            round_up = mid.set_scale(scale, ceiling=True)
            if round_up.compare_to(right) < 0:
                return round_up

        return mid

    @classmethod
    def _format_decimal(cls, decimal: LexoDecimal) -> str:
        """把 LexoDecimal 格式化为固定宽度的字符串（与 lexorank-ts 行为对齐）。

        关键点：
        - 确保小数点（radix）之前至少 6 位（不足左侧补 0）。
        - 去掉小数部分末尾的 0，避免 rank 字符串无意义膨胀。
        """
        formatted = decimal.format()
        radix = cls._NUMERAL_SYSTEM.get_radix_point_char()
        zero = cls._NUMERAL_SYSTEM.to_char(0)

        partial_index = formatted.find(radix)
        if partial_index < 0:
            partial_index = len(formatted)
            formatted = formatted + radix

        while partial_index < 6:
            formatted = zero + formatted
            partial_index += 1

        # 与 lexorank-ts 的目标逻辑一致：去掉小数部分末尾 0，避免 rank 字符串无意义膨胀。
        while formatted.endswith(zero):
            formatted = formatted[:-1]

        return formatted

    def gen_prev(self) -> "LexoRank":
        """生成“更小”的 rank（用于把元素移动到当前元素之前）。

        行为约定（方案A）：
        - 对 `LexoRank.max()`：返回该 bucket 的“初始最大附近”rank（等价于 TS 实现的特殊分支）。
        - 对 `LexoRank.min()`：抛出异常，避免出现“生成失败但静默返回自身”的模糊行为。

        Returns:
            LexoRank: 一个小于当前 rank 的 rank（同 bucket）。

        Raises:
            ValueError: 当前 rank 为 `LexoRank.min()` 时。
        """
        if self.is_max():
            return LexoRank.from_parts(self.bucket, self._initial_max_decimal())
        if self.is_min():
            raise ValueError("Cannot generate previous rank from LexoRank.min()")

        floor_integer = self.decimal.floor()
        floor_decimal = LexoDecimal.from_integer(floor_integer)
        next_decimal = floor_decimal.subtract(self._eight_decimal())
        if next_decimal.compare_to(self._min_decimal()) <= 0:
            next_decimal = LexoRank.between_decimals(self._min_decimal(), self.decimal)
        return LexoRank.from_parts(self.bucket, next_decimal)

    def gen_next(self) -> "LexoRank":
        """生成“更大”的 rank（用于把元素移动到当前元素之后）。

        行为约定（方案A）：
        - 对 `LexoRank.min()`：返回该 bucket 的“初始最小附近”rank（等价于 TS 实现的特殊分支）。
        - 对 `LexoRank.max()`：抛出异常，避免出现“生成失败但静默返回自身”的模糊行为。

        Returns:
            LexoRank: 一个大于当前 rank 的 rank（同 bucket）。

        Raises:
            ValueError: 当前 rank 为 `LexoRank.max()` 时。
        """
        if self.is_min():
            return LexoRank.from_parts(self.bucket, self._initial_min_decimal())
        if self.is_max():
            raise ValueError("Cannot generate next rank from LexoRank.max()")

        ceil_integer = self.decimal.ceil()
        ceil_decimal = LexoDecimal.from_integer(ceil_integer)
        next_decimal = ceil_decimal.add(self._eight_decimal())
        if next_decimal.compare_to(self._max_decimal()) >= 0:
            next_decimal = LexoRank.between_decimals(self.decimal, self._max_decimal())
        return LexoRank.from_parts(self.bucket, next_decimal)

    def between(self, other: "LexoRank") -> "LexoRank":
        """在两个 rank 之间生成一个新的 rank（用于插入）。

        要求两侧 rank 必须属于同一 bucket；如果 left/right 顺序传反也没关系，
        会自动在更小与更大之间取中间值。

        Args:
            other: 另一侧 rank。

        Returns:
            LexoRank: 一个严格位于两者之间的 rank（同 bucket）。

        Raises:
            ValueError: bucket 不同，或两者完全相等（无法再细分）。
        """
        if not self.bucket.equals(other.bucket):
            raise ValueError("Between works only within the same bucket")

        cmp = self.decimal.compare_to(other.decimal)
        if cmp > 0:
            return LexoRank.from_parts(
                self.bucket, LexoRank.between_decimals(other.decimal, self.decimal)
            )
        if cmp == 0:
            raise ValueError(
                "Try to rank between issues with same rank "
                f"this={self} other={other} this.decimal={self.decimal} other.decimal={other.decimal}"
            )
        return LexoRank.from_parts(
            self.bucket, LexoRank.between_decimals(self.decimal, other.decimal)
        )

    def in_next_bucket(self) -> "LexoRank":
        """返回相同 decimal 但切换到下一个 bucket 的 rank（很少用）。

        说明：
        - bucket 主要用于“粗分组隔离排序空间”，避免某个列表 rank 过度膨胀。
        - 你们项目目前通常只用 bucket=0，不需要调用这个方法。
        """
        return LexoRank.from_parts(self.bucket.next(), self.decimal)

    def in_prev_bucket(self) -> "LexoRank":
        """返回相同 decimal 但切换到上一个 bucket 的 rank（很少用）。"""
        return LexoRank.from_parts(self.bucket.prev(), self.decimal)

    def is_min(self) -> bool:
        """当前 rank 是否为 bucket 内的最小哨兵值。"""
        return self.decimal.equals(self._min_decimal())

    def is_max(self) -> bool:
        """当前 rank 是否为 bucket 内的最大哨兵值。"""
        return self.decimal.equals(self._max_decimal())

    def get_bucket(self) -> LexoRankBucket:
        """返回 bucket（分桶标识）。"""
        return self.bucket

    def get_decimal(self) -> LexoDecimal:
        """返回内部 decimal（用于计算/比较）。"""
        return self.decimal

    def compare_to(self, other: "LexoRank") -> int:
        """比较两个 rank 的大小。

        返回值：
        - -1：self < other
        -  0：self == other
        -  1：self > other

        说明：
        - LexoRank 的可比较性来自 `value` 字符串：bucket + 格式化后的 decimal。
        - 在数据库里直接 `ORDER BY value ASC`（或你存储的 order_index 字段）即可得到正确顺序。
        """
        if self is other:
            return 0
        if other is None:
            return 1
        if self.value < other.value:
            return -1
        if self.value > other.value:
            return 1
        return 0

    def equals(self, other: object) -> bool:
        """判断两个 rank 字符串表示是否完全一致。"""
        return isinstance(other, LexoRank) and self.value == other.value

    def __str__(self) -> str:
        """返回用于排序/存储的 LexoRank 字符串表示。"""
        return self.value
