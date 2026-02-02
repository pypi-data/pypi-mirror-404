"""LexoRank 分桶（bucket）实现。"""

from __future__ import annotations

from dataclasses import dataclass

from .lexo_integer import LexoInteger
from .numeral_systems import NUMERAL_SYSTEM_36


@dataclass(frozen=True, slots=True)
class LexoRankBucket:
    """LexoRank 的分桶（bucket）概念。

    在一些实现中 bucket 可用于把“不同大分组”的排序隔离开，避免 rank 过度变长。
    本实现，提供 0/1/2 三个 bucket，并可 next/prev 循环切换。
    """

    id: int

    @staticmethod
    def max() -> "LexoRankBucket":
        """返回最大 bucket（BUCKET_2）。"""
        return BUCKET_2

    @staticmethod
    def from_str(text: str) -> "LexoRankBucket":
        """从字符串解析 bucket。

        Args:
            text: '0'/'1'/'2'

        Returns:
            LexoRankBucket: 对应 bucket
        """
        val = LexoInteger.parse(text, NUMERAL_SYSTEM_36).value
        if val == 0:
            return BUCKET_0
        if val == 1:
            return BUCKET_1
        if val == 2:
            return BUCKET_2
        raise ValueError(f"Unknown bucket: {text}")

    @staticmethod
    def resolve(bucket_id: int) -> "LexoRankBucket":
        """根据 bucket_id 返回对应 bucket（0/1/2）。"""
        if bucket_id == 0:
            return BUCKET_0
        if bucket_id == 1:
            return BUCKET_1
        if bucket_id == 2:
            return BUCKET_2
        raise ValueError(f"No bucket found with id {bucket_id}")

    def format(self) -> str:
        """格式化为 bucket 字符串（'0'/'1'/'2'）。"""
        return str(self.id)

    def next(self) -> "LexoRankBucket":
        """返回下一个 bucket（0->1->2->0 循环）。"""
        if self.id == 0:
            return BUCKET_1
        if self.id == 1:
            return BUCKET_2
        return BUCKET_0

    def prev(self) -> "LexoRankBucket":
        """返回上一个 bucket（0<-1<-2<-0 循环）。"""
        if self.id == 0:
            return BUCKET_2
        if self.id == 1:
            return BUCKET_0
        return BUCKET_1

    def equals(self, other: object) -> bool:
        """判断 bucket 是否相等。"""
        return isinstance(other, LexoRankBucket) and self.id == other.id

    def __str__(self) -> str:
        """返回 bucket 的字符串表示。"""
        return self.format()


BUCKET_0 = LexoRankBucket(0)
BUCKET_1 = LexoRankBucket(1)
BUCKET_2 = LexoRankBucket(2)
