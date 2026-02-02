"""手动调用示例（不走 unittest）。

运行：
- 支持直接运行：`python app/utils/lexorank/demo.py`

用途：
- 这是“演示脚本”，用于你在开发阶段快速生成一些 LexoRank 字符串，方便造假数据写入数据库。
- 注意：rank 字符串里包含 `|`，在 zsh 里运行命令时要用引号包起来，否则会被当作管道符。
"""

from __future__ import annotations

import argparse
import pathlib
import sys

if __package__ in (None, ""):
    # 允许用 `python app/utils/lexorank/demo.py` 直接运行：
    # 把包的父目录（app/utils）加入到 sys.path，确保能 import lexorank_key。
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from lexorank_key import LexoRankKey  # noqa: E402


def demo_basic_scenarios() -> None:
    """演示：最常见的几种插入场景。"""
    print("=== Demo 1: 空列表插入第一条 ===")
    first = LexoRankKey.init_for_empty_list()
    print("first =", first)

    print("\n=== Demo 2: 追加到末尾（连续追加） ===")
    second = LexoRankKey.insert_after(first)
    third = LexoRankKey.insert_after(second)
    print("second =", second)
    print("third  =", third)

    print("\n=== Demo 3: 插入到两条之间（中间插入/拖拽排序常用） ===")
    mid = LexoRankKey.insert_between(first, second)
    print("between(first, second) =", mid)

    print("\n=== Demo 4: 插到最前（前插） ===")
    before_first = LexoRankKey.insert_before(first)
    print("before_first =", before_first)

    print("\n=== Demo 5: 通用入口 insert(prev, nxt)（推荐业务层只用这个，因为DB查出“目标位置”的前一条/后一条（可能为空）） ===")
    print("insert(None, None)        =", LexoRankKey.insert(None, None))
    print("insert(None, first)       =", LexoRankKey.insert(None, first))
    print("insert(first, None)       =", LexoRankKey.insert(first, None))
    print("insert(first, second)     =", LexoRankKey.insert(first, second))


def demo_generate_next_batch(start: str, count: int) -> list[str]:
    """演示：基于一个起点，批量生成多个递增的 rank（便于一次性造 N 条假数据）。

    适用场景：
    - 你要往数据库里批量插入脚本/场景，且希望它们都“按顺序排在某条记录之后”。
    - 例如：给某个 script 新建 50 个 scene，就可以用这个批量生成 50 个 order_index。

    Args:
        start: 起始 rank（通常是“当前最后一条”的 order_index）。
        count: 要生成的数量（>=1）。

    Returns:
        list[str]: 递增的 rank 字符串列表（长度为 count）。
    """
    if count <= 0:
        raise ValueError("count must be >= 1")

    out: list[str] = []
    current = start
    for _ in range(count):
        current = LexoRankKey.insert_after(current)
        out.append(current)
    return out


def main() -> None:
    """手动运行示例入口。"""
    parser = argparse.ArgumentParser(description="LexoRank 演示脚本（造假数据用）")
    parser.add_argument(
        "--start",
        default=None,
        help=(
            "起始 rank（用于批量生成 next）。示例：'0|hzzzzz:'。"
            "注意：包含 |，在 zsh 里必须用引号包起来。"
        ),
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="批量生成 next 的数量（默认 5）。",
    )
    args = parser.parse_args()

    # Demo 1~5：常见场景
    demo_basic_scenarios()

    # Demo 6：批量 next（造假数据时使用的工具，实际业务时不想需要批量生成，在app/utils/lexorank_key.py中也无此方法）
    print("\n=== Demo 6: 批量生成多个 next（相当于多次 insert_after） ===")
    start = args.start or LexoRankKey.init_for_empty_list()
    batch = demo_generate_next_batch(start, args.count)
    print("start =", start)
    print(f"generated_next(count={args.count}) =")
    for i, v in enumerate(batch, start=1):
        print(f"  {i}. {v}")

if __name__ == "__main__":
    main()
