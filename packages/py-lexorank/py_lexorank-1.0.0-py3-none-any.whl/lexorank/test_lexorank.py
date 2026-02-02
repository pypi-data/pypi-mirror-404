"""可直接运行的自测脚本（unittest）。

运行方式（任选其一）：
- 在 `app/utils` 目录下：`python -m lexorank.test_lexorank`
- 直接运行文件：`python app/utils/lexorank/test_lexorank.py`
"""

from __future__ import annotations

import pathlib
import sys
import unittest

if __package__ in (None, ""):
    # 允许用 `python app/utils/lexorank/test_lexorank.py` 直接运行：
    # 把包的父目录（app/utils）加入到 sys.path，确保能 import lexorank / lexorank_key。
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import lexorank as lx  # noqa: E402
from lexorank_key import LexoRankKey  # noqa: E402


class TestLexoRank(unittest.TestCase):
    """LexoRank 的基础回归测试。"""

    def test_min(self):
        """min() 生成的 rank 应为全局最小哨兵值。"""
        self.assertEqual(str(lx.LexoRank.min()), "0|000000:")

    def test_max(self):
        """max() 生成的 rank 应为 bucket 内最大哨兵值。"""
        self.assertEqual(str(lx.LexoRank.max()), "0|zzzzzz:")

    def test_between_min_max(self):
        """between(min, max) 应落在两者之间，且字符串比较顺序正确。"""
        min_rank = lx.LexoRank.min()
        max_rank = lx.LexoRank.max()
        between = min_rank.between(max_rank)
        self.assertEqual(str(between), "0|hzzzzz:")
        self.assertLess(min_rank.compare_to(between), 0)
        self.assertGreater(max_rank.compare_to(between), 0)

    def test_between_min_next(self):
        """between(min, min.gen_next) 应生成一个介于两者之间的新 rank。"""
        min_rank = lx.LexoRank.min()
        next_rank = min_rank.gen_next()
        between = min_rank.between(next_rank)
        self.assertEqual(str(between), "0|0i0000:")
        self.assertLess(min_rank.compare_to(between), 0)
        self.assertGreater(next_rank.compare_to(between), 0)

    def test_between_max_prev(self):
        """between(max, max.gen_prev) 应生成一个介于两者之间的新 rank。"""
        max_rank = lx.LexoRank.max()
        prev_rank = max_rank.gen_prev()
        between = max_rank.between(prev_rank)
        self.assertEqual(str(between), "0|yzzzzz:")
        self.assertGreater(max_rank.compare_to(between), 0)
        self.assertLess(prev_rank.compare_to(between), 0)

    def test_gen_prev_from_min_raises(self):
        """对最小哨兵值调用 gen_prev 应抛错。"""
        with self.assertRaises(ValueError):
            lx.LexoRank.min().gen_prev()

    def test_gen_next_from_max_raises(self):
        """对最大哨兵值调用 gen_next 应抛错。"""
        with self.assertRaises(ValueError):
            lx.LexoRank.max().gen_next()

    def test_move_to_cases(self):
        """多个步进组合下 between 的预期输出（回归用例）。"""
        cases = [
            (0, 1, "0|0i0000:"),
            (1, 0, "0|0i0000:"),
            (3, 5, "0|10000o:"),
            (5, 3, "0|10000o:"),
            (15, 30, "0|10004s:"),
            (31, 32, "0|10006s:"),
            (100, 200, "0|1000x4:"),
            (200, 100, "0|1000x4:"),
        ]

        for prev_step, next_step, expected in cases:
            with self.subTest(prev_step=prev_step, next_step=next_step):
                prev_rank = lx.LexoRank.min()
                for _ in range(prev_step):
                    prev_rank = prev_rank.gen_next()

                next_rank = lx.LexoRank.min()
                for _ in range(next_step):
                    next_rank = next_rank.gen_next()

                self.assertEqual(str(prev_rank.between(next_rank)), expected)

    def test_order_index_init_and_insert_between(self):
        """LexoRankKey 在空列表、追加、两者之间插入的基本可用性。"""
        start = LexoRankKey.init_for_empty_list()
        nxt = LexoRankKey.insert_after(start)
        mid = LexoRankKey.insert_between(start, nxt)
        self.assertIsInstance(start, str)
        self.assertIsInstance(nxt, str)
        self.assertIsInstance(mid, str)
        self.assertLess(lx.LexoRank.parse(start).compare_to(lx.LexoRank.parse(mid)), 0)
        self.assertLess(lx.LexoRank.parse(mid).compare_to(lx.LexoRank.parse(nxt)), 0)

    def test_order_index_insert_before_after(self):
        """LexoRankKey 的前插/后插应保持严格有序。"""
        anchor = LexoRankKey.init_for_empty_list()
        before = LexoRankKey.insert_before(anchor)
        after = LexoRankKey.insert_after(anchor)
        self.assertLess(
            lx.LexoRank.parse(before).compare_to(lx.LexoRank.parse(anchor)), 0
        )
        self.assertLess(
            lx.LexoRank.parse(anchor).compare_to(lx.LexoRank.parse(after)), 0
        )

    def test_order_index_insert_general(self):
        """LexoRankKey.insert(prev,nxt) 的边界行为应与专用方法一致。"""
        self.assertEqual(LexoRankKey.insert(None, None), str(lx.LexoRank.middle()))
        self.assertEqual(
            LexoRankKey.insert(None, "0|100000:"),
            LexoRankKey.insert_between("0|000000:", "0|100000:"),
        )
        self.assertEqual(
            LexoRankKey.insert("0|yzzzzz:", None),
            LexoRankKey.insert_after("0|yzzzzz:"),
        )

    def test_order_index_next_prev_and_validate(self):
        """LexoRankKey 的 next/prev/validate 边界与异常行为。"""
        self.assertEqual(
            LexoRankKey.next_of("0|000000:"), str(lx.LexoRank.min().gen_next())
        )
        self.assertEqual(
            LexoRankKey.prev_of("0|zzzzzz:"), str(lx.LexoRank.max().gen_prev())
        )

        with self.assertRaises(ValueError):
            LexoRankKey.prev_of("0|000000:")
        with self.assertRaises(ValueError):
            LexoRankKey.next_of("0|zzzzzz:")

        self.assertEqual(LexoRankKey.validate("0|000000:"), "0|000000:")
        with self.assertRaises(ValueError):
            LexoRankKey.validate("not-a-rank")
        with self.assertRaises(ValueError):
            LexoRankKey.validate(123)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            LexoRankKey.insert_after(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
