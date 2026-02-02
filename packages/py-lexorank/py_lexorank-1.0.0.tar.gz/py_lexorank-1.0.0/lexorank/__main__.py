"""LexoRank CLI（开发/调试用）。"""

from __future__ import annotations

import argparse
import sys

from .lexo_rank import LexoRank


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lexorank", description="LexoRank CLI (no deps)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("min")
    sub.add_parser("middle")

    p_max = sub.add_parser("max")
    p_max.add_argument("--bucket", default="0")

    p_next = sub.add_parser("next")
    p_next.add_argument("rank")

    p_prev = sub.add_parser("prev")
    p_prev.add_argument("rank")

    p_between = sub.add_parser("between")
    p_between.add_argument("left")
    p_between.add_argument("right")

    return parser


def main(argv: list[str] | None = None) -> int:
    """运行 LexoRank CLI（开发/调试工具）。"""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "min":
        print(LexoRank.min())
        return 0
    if args.cmd == "middle":
        print(LexoRank.middle())
        return 0
    if args.cmd == "max":
        bucket = LexoRank.parse(f"{args.bucket}|000000:").get_bucket()
        print(LexoRank.max(bucket))
        return 0
    if args.cmd == "next":
        print(LexoRank.parse(args.rank).gen_next())
        return 0
    if args.cmd == "prev":
        print(LexoRank.parse(args.rank).gen_prev())
        return 0
    if args.cmd == "between":
        left = LexoRank.parse(args.left)
        right = LexoRank.parse(args.right)
        print(left.between(right))
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
