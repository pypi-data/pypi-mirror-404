"""LexoRank-Python: Lightweight, dependency-free Python implementation of LexoRank algorithm for fractional indexing.

This package provides the core implementation of LexoRank: `LexoRank` and `LexoRankBucket`.
The business layer typically only needs to use `LexoRankKey` from `lexorank_key.py` to generate sort fields.

For fractional indexing that enables efficient drag-and-drop sorting, dynamic list reordering,
and insertion at any position without full list rebalancing.
"""

from .lexo_rank import LexoRank
from .lexo_rank_bucket import LexoRankBucket

__all__ = [
    "LexoRank",
    "LexoRankBucket",
]

__version__ = "1.0.0"
__author__ = "ixfcao"
__email__ = "2717176337@qq.com"