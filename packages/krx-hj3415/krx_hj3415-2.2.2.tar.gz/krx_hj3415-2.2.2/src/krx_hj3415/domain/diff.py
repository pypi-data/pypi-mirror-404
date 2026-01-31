# krx_hj3415/domain/diff.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable
from .types import UniverseDiff, CodeItem


def _to_code_map(items: Iterable[CodeItem]) -> dict[str, CodeItem]:
    return {it.code: it for it in items}


def diff_universe(
    *,
    universe: str,
    asof: datetime,
    new_items: list[CodeItem],
    old_items: list[CodeItem],
) -> UniverseDiff:
    new_map = _to_code_map(new_items)
    old_map = _to_code_map(old_items)

    added = [new_map[c] for c in sorted(new_map.keys() - old_map.keys())]
    removed = [old_map[c] for c in sorted(old_map.keys() - new_map.keys())]
    kept = len(new_map.keys() & old_map.keys())

    return UniverseDiff(
        universe=universe,
        asof=asof,
        added=added,
        removed=removed,
        kept_count=kept,
    )
