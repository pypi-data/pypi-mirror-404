from __future__ import annotations

from typing import Iterable

LAZY_WHERE_INFO = tuple[str, str | float | int, str, bool]


def purge_where_info(to_conjunct: Iterable[LAZY_WHERE_INFO | AndLazyWhereInfo | OrLazyWhereInfo], to_flatten: type[AndLazyWhereInfo | OrLazyWhereInfo]):
    not_to_flatten = AndLazyWhereInfo if to_flatten == OrLazyWhereInfo else OrLazyWhereInfo
    purged = []
    for c in to_conjunct:
        if isinstance(c, not_to_flatten):
            purged.append(c.info)
        elif isinstance(c, to_flatten):
            purged += c.info
        else:
            purged.append(c)

    return purged


def recursive_transpose(t):
    if not t or not isinstance(t[0], tuple | AndLazyWhereInfo | OrLazyWhereInfo):
        return t
    return tuple(zip(*[
        recursive_transpose(x.info)
        if isinstance(x, AndLazyWhereInfo | OrLazyWhereInfo)
        else recursive_transpose(x)
        for x in t
    ]))


class OrLazyWhereInfo:
    def __init__(self, info: tuple[LAZY_WHERE_INFO]):
        self.info = info


class AndLazyWhereInfo:
    def __init__(self, info: tuple[LAZY_WHERE_INFO]):
        self.info = info
