# db2_hj3415/universe/repo.py
from __future__ import annotations

from datetime import datetime
from typing import Sequence

from pymongo import ASCENDING, DESCENDING
from pymongo.asynchronous.database import AsyncDatabase
from common_hj3415.utils.time import utcnow
from contracts_hj3415.universe.dto import UniverseItemDTO, UniversePayloadDTO
from contracts_hj3415.universe.types import UniverseNames

from .domain import (
    UNIVERSE_LATEST_COL,
    UNIVERSE_SNAPSHOTS_COL,
    UniverseItem,
    UniverseLatestDoc,
    UniverseSnapshotDoc,
    build_universe_latest_doc,
    build_universe_snapshot_doc,
)


async def ensure_indexes(
    db: AsyncDatabase,
    *,
    snapshot_ttl_days: int | None,
) -> None:
    """universe latest/snapshots 컬렉션 인덱스를 생성한다."""
    latest = db[UNIVERSE_LATEST_COL]
    snapshots = db[UNIVERSE_SNAPSHOTS_COL]

    # latest는 _id=universe (기본 유니크) + asof 조회용
    await latest.create_index([("universe", ASCENDING)])  # 선택(명시)
    await latest.create_index([("asof", DESCENDING)])

    # snapshots는 universe 타임라인 조회
    await snapshots.create_index([("universe", ASCENDING), ("asof", DESCENDING)])

    if snapshot_ttl_days is not None:
        expire_seconds = int(snapshot_ttl_days) * 24 * 60 * 60
        await snapshots.create_index(
            [("asof", ASCENDING)],
            expireAfterSeconds=expire_seconds,
            name="ttl_asof",
        )


async def upsert_latest(
    db: AsyncDatabase,
    *,
    universe: UniverseNames,
    items: list[UniverseItemDTO],
    asof: datetime | None = None,
    source: str = "unknown",
) -> None:
    """universe latest 문서를 upsert한다."""
    doc = build_universe_latest_doc(
        universe=universe,
        items=items,
        asof=asof or utcnow(),
        source=source,
    )
    await db[UNIVERSE_LATEST_COL].update_one(
        {"_id": universe},
        {"$set": doc},
        upsert=True,
    )


async def insert_snapshot(
    db: AsyncDatabase,
    *,
    universe: UniverseNames,
    items: list[UniverseItemDTO],
    asof: datetime | None = None,
    source: str = "unknown",
) -> None:
    """universe snapshot을 신규로 저장한다."""
    doc = build_universe_snapshot_doc(
        universe=universe,
        items=items,
        asof=asof or utcnow(),
        source=source,
    )
    await db[UNIVERSE_SNAPSHOTS_COL].insert_one(doc)


def _latest_doc_to_dto(doc: UniverseLatestDoc) -> UniversePayloadDTO:
    return {
        "universe": doc["universe"],
        "asof": doc["asof"].isoformat(),
        "source": doc["source"],
        "items": doc["items"],  # UniverseItem == UniverseItemDTO 구조 호환
    }

def _snapshot_doc_to_dto(doc: UniverseSnapshotDoc) -> UniversePayloadDTO:
    return {
        "universe": doc["universe"],
        "asof": doc["asof"].isoformat(),
        "source": doc["source"],
        "items": doc["items"],
    }


async def get_latest(
    db: AsyncDatabase,
    *,
    universe: UniverseNames,
) -> UniversePayloadDTO | None:
    doc = await db[UNIVERSE_LATEST_COL].find_one({"_id": universe})
    if not doc:
        return None
    return _latest_doc_to_dto(doc)


async def list_snapshots(
    db: AsyncDatabase,
    *,
    universe: UniverseNames,
    limit: int = 30,
    desc: bool = True,
) -> list[UniversePayloadDTO]:
    order = DESCENDING if desc else ASCENDING
    cur = (
        db[UNIVERSE_SNAPSHOTS_COL]
        .find({"universe": universe})
        .sort("asof", order)
        .limit(limit)
    )
    docs = await cur.to_list(length=limit)
    return [_snapshot_doc_to_dto(d) for d in docs]

def extract_codes(items: Sequence[UniverseItem]) -> list[str]:
    codes: list[str] = []
    for it in items:
        code = (it.get("code") or "").strip()
        if code:
            codes.append(code)
    return codes

async def list_universe_codes(db, *, universe: UniverseNames) -> list[str]:
    doc: UniverseLatestDoc | None = await get_latest(db, universe=universe)
    if not doc:
        return []
    return extract_codes(doc["items"])