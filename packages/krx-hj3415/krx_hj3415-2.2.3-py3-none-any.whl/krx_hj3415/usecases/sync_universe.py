# krx_hj3415/usecases/sync_universe.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, cast
from pymongo.asynchronous.database import AsyncDatabase

from domain_hj3415.common.time import utcnow

from db2_hj3415.nfs.repo import delete_codes_from_nfs
from db2_hj3415.universe.repo import (
    upsert_latest as upsert_universe_latest,
    insert_snapshot as insert_universe_snapshot,
)
from db2_hj3415.universe.repo import get_latest as get_universe_latest

from contracts_hj3415.universe.dto import UniverseItemDTO, UniversePayloadDTO
from contracts_hj3415.universe.types import UniverseNames

from krx_hj3415.domain.types import CodeItem, UniverseDiff
from krx_hj3415.domain.diff import diff_universe
from krx_hj3415.domain.universe import UniverseKind
from krx_hj3415.provider.krx300_samsungfund_excel import fetch_krx300_items


def _payload_dto_to_items(dto: UniversePayloadDTO) -> list[CodeItem]:
    if dto is None:
        return []

    data = dto["items"]

    out: list[CodeItem] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        code = str(row.get("code") or "").strip()
        if not code:
            continue
        name = str(row.get("name") or "").strip()
        market = row.get("market")
        asof = utcnow()
        out.append(CodeItem(code=code, name=name, asof=asof, market=market))
    return out


async def refresh_krx300(*, max_days: int = 15) -> tuple[datetime, list[CodeItem]]:
    # 현재는 KRX300만 구현. 다른 universe도 늘리면 여기서 분기
    return fetch_krx300_items(max_days=max_days)


def to_universe_item_dtos(
    items: Iterable[Any], *, market: str = "KRX"
) -> list[UniverseItemDTO]:
    out: list[UniverseItemDTO] = []
    for it in items:
        if it is None:
            continue

        if isinstance(it, dict):
            code = (it.get("code") or "").strip()
            name = it.get("name")
        else:
            code = (getattr(it, "code", "") or "").strip()
            name = getattr(it, "name", None)

        if not code:
            continue

        dto: UniverseItemDTO = {"code": code, "market": market}
        if isinstance(name, str) and name.strip():
            dto["name"] = name.strip()

        out.append(dto)
    return out


async def run_sync(
    db: AsyncDatabase,
    *,
    universe: UniverseKind = UniverseKind.KRX300,
    max_days: int = 15,
    snapshot: bool = True,
) -> UniverseDiff:
    """
    1) 외부에서 최신 유니버스 수집
    2) DB에서 이전 latest 조회
    3) diff 계산
    4) latest upsert + (선택) snapshots insert
    """
    # --- 1) fetch ---
    asof, new_items = await refresh_krx300(max_days=max_days)

    # --- 2) load old ---
    old_payload_dto = await get_universe_latest(
        db, universe=cast(UniverseNames, universe.value)
    )
    old_items = _payload_dto_to_items(old_payload_dto)

    # --- 3) diff ---
    d = diff_universe(
        universe=universe.value, asof=asof, new_items=new_items, old_items=old_items
    )

    # --- 4) save ---
    await upsert_universe_latest(
        db,
        universe=cast(UniverseNames, universe.value),
        items=to_universe_item_dtos(new_items, market="KRX"),
        asof=asof,
        source="samsungfund",
    )
    if snapshot:
        await insert_universe_snapshot(
            db,
            universe=cast(UniverseNames, universe.value),
            items=to_universe_item_dtos(new_items, market="KRX"),
            asof=asof,
            source="samsungfund",
        )

    return d


async def apply_removed(
    db: AsyncDatabase,
    *,
    removed_codes: Iterable[str],
) -> dict[str, int]:
    """
    removed codes를 nfs(latest/snapshots)에서 모두 삭제.
    """
    codes = [str(c).strip() for c in removed_codes if c and str(c).strip()]
    if not codes:
        return {"latest_deleted": 0, "snapshots_deleted": 0}

    return await delete_codes_from_nfs(db, codes=codes, endpoint=None)
