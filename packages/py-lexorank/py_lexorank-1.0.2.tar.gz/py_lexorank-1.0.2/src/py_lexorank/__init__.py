"""py-lexorank: dependency-free LexoRank for fractional indexing.

PyPI distribution name: `py-lexorank`
Python import name: `py_lexorank`

Recommended business API:
    from py_lexorank.lexorank_key import LexoRankKey
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("py-lexorank")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["LexoRankKey", "LexoRank", "LexoRankBucket", "__version__"]


def __getattr__(name: str):
    if name == "LexoRankKey":
        from .lexorank_key import LexoRankKey

        return LexoRankKey
    if name == "LexoRank":
        from .lexorank import LexoRank

        return LexoRank
    if name == "LexoRankBucket":
        from .lexorank import LexoRankBucket

        return LexoRankBucket
    raise AttributeError(name)
