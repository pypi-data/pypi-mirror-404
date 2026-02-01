# db2_hj3415/nfs/repo.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence, Mapping

from pymongo import ASCENDING, DESCENDING, UpdateOne
from pymongo.asynchronous.database import AsyncDatabase

from contracts_hj3415.nfs.types import Endpoints
from common_hj3415.utils.time import utcnow

from .domain import (
    LATEST_COL,
    SNAPSHOTS_COL,
    NfsLatestDoc,
    NfsSnapshotDoc,
    build_latest_doc,
    build_snapshot_doc,
    latest_id,
)

async def ensure_indexes(
    db: AsyncDatabase,
    *,
    snapshot_ttl_days: int | None,
) -> None:
    """NFS latest/snapshots 컬렉션에 필요한 인덱스 및 TTL 인덱스를 생성한다."""
    latest = db[LATEST_COL]
    snapshots = db[SNAPSHOTS_COL]

    await latest.create_index([("endpoint", ASCENDING), ("code", ASCENDING)])
    await snapshots.create_index([("endpoint", ASCENDING), ("code", ASCENDING), ("asof", DESCENDING)])

    await latest.create_index([("code", ASCENDING)])
    await snapshots.create_index([("code", ASCENDING)])

    if snapshot_ttl_days is not None:
        expire_seconds = int(snapshot_ttl_days) * 24 * 60 * 60
        await snapshots.create_index(
            [("asof", ASCENDING)],
            expireAfterSeconds=expire_seconds,
            name="ttl_asof",
        )


# -----------------------------------------------------------------------------
# Writes (payload-first)
# -----------------------------------------------------------------------------

async def upsert_latest_payload(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    payload: dict[str, Any],
    asof: datetime | None = None,
    code: str,
) -> None:
    """특정 endpoint/code의 latest 문서를 payload 기준으로 upsert한다."""
    doc: NfsLatestDoc = build_latest_doc(
        endpoint=endpoint,
        code=str(code).strip(),
        payload=payload,
        asof=asof or utcnow(),
    )

    await db[LATEST_COL].update_one(
        {"_id": doc["_id"]},
        {"$set": doc},
        upsert=True,
    )

async def upsert_latest_payload_many(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    items: Mapping[str, dict[str, Any]],  # {code: payload}
    asof: datetime | None = None,
    ordered: bool = False,
) -> dict[str, int]:
    """단일 endpoint에서 여러 code의 latest 문서를 payload 기준으로 upsert한다."""
    ts = asof or utcnow()

    ops: list[UpdateOne] = []
    for code, payload in items.items():
        code_s = str(code).strip()
        if not code_s:
            continue

        doc = build_latest_doc(
            endpoint=endpoint,
            code=code_s,
            payload=payload,
            asof=ts,
        )

        ops.append(
            UpdateOne(
                {"_id": doc["_id"]},
                {"$set": doc},
                upsert=True,
            )
        )

    if not ops:
        return {"matched": 0, "modified": 0, "upserted": 0}

    res = await db[LATEST_COL].bulk_write(ops, ordered=ordered)
    return {
        "matched": int(res.matched_count),
        "modified": int(res.modified_count),
        "upserted": len(getattr(res, "upserted_ids", {}) or {}),
    }


async def insert_snapshot_payload(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    payload: dict[str, Any],
    asof: datetime | None = None,
    code: str,
) -> None:
    """단일 payload를 snapshot 컬렉션에 신규 스냅샷으로 저장한다."""
    doc: NfsSnapshotDoc = build_snapshot_doc(
        endpoint=endpoint,
        code=str(code).strip(),
        payload=payload,
        asof=asof or utcnow(),
    )
    await db[SNAPSHOTS_COL].insert_one(doc)


async def insert_snapshots_payload_many(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    items: Mapping[str, dict[str, Any]],  # {code: payload}
    asof: datetime | None = None,
) -> None:
    """여러 code별 payload를 하나의 배치(asof) 스냅샷으로 저장한다."""
    docs: list[NfsSnapshotDoc] = []
    ts = asof or utcnow()

    for code, payload in items.items():
        code_s = str(code).strip()
        if not code_s:
            continue

        docs.append(
            build_snapshot_doc(
                endpoint=endpoint,
                code=code_s,
                payload=payload,
                asof=ts,
            )
        )

    if docs:
        await db[SNAPSHOTS_COL].insert_many(docs)


# -----------------------------------------------------------------------------
# Reads
# -----------------------------------------------------------------------------

async def get_latest(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    code: str,
) -> dict[str, Any] | None:
    """endpoint와 code에 해당하는 latest 문서를 조회한다."""
    return await db[LATEST_COL].find_one({"_id": latest_id(endpoint, code)})


async def list_snapshots(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    code: str,
    limit: int = 50,
    desc: bool = True,
) -> list[dict[str, Any]]:
    """특정 endpoint/code의 스냅샷 이력을 시간순으로 조회한다."""
    order = DESCENDING if desc else ASCENDING
    cur = (
        db[SNAPSHOTS_COL]
        .find({"endpoint": endpoint, "code": code})
        .sort("asof", order)
        .limit(limit)
    )
    return await cur.to_list(length=limit)


# -----------------------------------------------------------------------------
# Delete helpers
# -----------------------------------------------------------------------------

def _clean_codes(codes: Sequence[str]) -> list[str]:
    """
    코드 리스트를 정규화하여 공백 제거·빈값 제거·중복 제거(순서 유지)한다.
    입력: "005930", " 005930 ", None, "", "035420" 같은 지저분한 코드 리스트
    출력: ["005930", "035420"] 같은 안전한 코드 리스트
    """
    out: list[str] = []
    for c in codes:
        s = str(c).strip()
        if s:
            out.append(s)

    seen: set[str] = set()
    uniq: list[str] = []
    for c in out:
        if c in seen:
            continue
        seen.add(c)
        uniq.append(c)
    return uniq


async def delete_code_from_nfs(
    db: AsyncDatabase,
    *,
    code: str,
    endpoint: Endpoints | None = None,
) -> dict[str, int]:
    """단일 code를 latest/snapshots에서 삭제한다 (endpoint 선택 가능)."""
    code = str(code).strip()
    if not code:
        return {"latest_deleted": 0, "snapshots_deleted": 0}

    latest_filter: dict[str, Any] = {"code": code}
    snaps_filter: dict[str, Any] = {"code": code}
    if endpoint is not None:
        latest_filter["endpoint"] = endpoint
        snaps_filter["endpoint"] = endpoint

    r1 = await db[LATEST_COL].delete_many(latest_filter)
    r2 = await db[SNAPSHOTS_COL].delete_many(snaps_filter)

    return {"latest_deleted": int(r1.deleted_count), "snapshots_deleted": int(r2.deleted_count)}


async def delete_codes_from_nfs(
    db: AsyncDatabase,
    *,
    codes: Sequence[str],
    endpoint: Endpoints | None = None,
) -> dict[str, int]:
    """여러 code를 latest/snapshots에서 한 번에 삭제한다."""
    codes_ = _clean_codes(codes)
    if not codes_:
        return {"latest_deleted": 0, "snapshots_deleted": 0}

    latest_filter: dict[str, Any] = {"code": {"$in": codes_}}
    snaps_filter: dict[str, Any] = {"code": {"$in": codes_}}
    if endpoint is not None:
        latest_filter["endpoint"] = endpoint
        snaps_filter["endpoint"] = endpoint

    r1 = await db[LATEST_COL].delete_many(latest_filter)
    r2 = await db[SNAPSHOTS_COL].delete_many(snaps_filter)

    return {"latest_deleted": int(r1.deleted_count), "snapshots_deleted": int(r2.deleted_count)}


async def delete_codes_split(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    codes: Sequence[str],
    latest: bool = True,
    snapshots: bool = True,
) -> dict[str, int]:
    """특정 endpoint에서 latest와 snapshots 삭제 여부를 선택적으로 제어한다."""
    codes_ = _clean_codes(codes)
    if not codes_:
        return {"latest_deleted": 0, "snapshots_deleted": 0}

    latest_deleted = 0
    snapshots_deleted = 0

    if latest:
        r1 = await db[LATEST_COL].delete_many({"endpoint": endpoint, "code": {"$in": codes_}})
        latest_deleted = int(r1.deleted_count)

    if snapshots:
        r2 = await db[SNAPSHOTS_COL].delete_many({"endpoint": endpoint, "code": {"$in": codes_}})
        snapshots_deleted = int(r2.deleted_count)

    return {"latest_deleted": latest_deleted, "snapshots_deleted": snapshots_deleted}


# ---- intention-revealing wrappers ----

async def delete_codes_for_endpoint(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    codes: Sequence[str],
) -> dict[str, int]:
    """특정 endpoint의 latest/snapshots에서 여러 code를 삭제한다."""
    return await delete_codes_from_nfs(db, codes=codes, endpoint=endpoint)


async def delete_codes_from_all_endpoints(
    db: AsyncDatabase,
    *,
    codes: Sequence[str],
) -> dict[str, int]:
    """모든 endpoint에서 여러 code의 데이터를 삭제한다."""
    return await delete_codes_from_nfs(db, codes=codes, endpoint=None)


async def delete_code_everywhere(
    db: AsyncDatabase,
    *,
    code: str,
) -> dict[str, int]:
    """단일 code를 모든 endpoint에서 삭제한다."""
    return await delete_code_from_nfs(db, code=code, endpoint=None)


async def delete_code_for_endpoint(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    code: str,
) -> dict[str, int]:
    """단일 code를 특정 endpoint에서만 삭제한다."""
    return await delete_code_from_nfs(db, code=code, endpoint=endpoint)


# -----------------------------------------------------------------------------
# Hash diff helpers (change detection)
# -----------------------------------------------------------------------------

async def _get_latest_hash_map(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    codes: list[str] | None = None,
) -> dict[str, str]:
    """latest 컬렉션에서 code별 payload_hash 맵을 조회한다."""
    col = db[LATEST_COL]
    q: dict[str, Any] = {"endpoint": endpoint}
    if codes:
        q["code"] = {"$in": [str(c) for c in codes]}
    cur = col.find(q, {"code": 1, "payload_hash": 1})

    out: dict[str, str] = {}
    async for doc in cur:
        code = str(doc.get("code") or "")
        h = doc.get("payload_hash")
        if code and isinstance(h, str):
            out[code] = h
    return out


async def _get_prev_snapshot_hash_map(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    codes: list[str],
    before_asof: datetime | None = None,
) -> dict[str, str]:
    """이전 snapshot 기준으로 code별 payload_hash 맵을 조회한다."""
    if not codes:
        return {}

    col = db[SNAPSHOTS_COL]
    match: dict[str, Any] = {
        "endpoint": endpoint,
        "code": {"$in": [str(c) for c in codes]},
    }
    if before_asof is not None:
        match["asof"] = {"$lt": before_asof}

    pipeline = [
        {"$match": match},
        {"$sort": {"code": 1, "asof": -1}},
        {"$group": {"_id": "$code", "payload_hash": {"$first": "$payload_hash"}}},
    ]

    out: dict[str, str] = {}
    async for row in col.aggregate(pipeline):
        code = str(row.get("_id") or "")
        h = row.get("payload_hash")
        if code and isinstance(h, str):
            out[code] = h
    return out


async def diff_latest_vs_previous_snapshot(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    codes: list[str] | None = None,
    before_asof: datetime | None = None,
) -> dict[str, Any]:
    """latest와 직전 snapshot을 비교해 변경/신규/누락 code를 계산한다."""
    latest_map = await _get_latest_hash_map(db, endpoint=endpoint, codes=codes)
    target_codes = list(latest_map.keys()) if codes is None else [str(c) for c in codes]

    prev_map = await _get_prev_snapshot_hash_map(
        db, endpoint=endpoint, codes=target_codes, before_asof=before_asof
    )

    changed: list[str] = []
    new: list[str] = []
    for c in target_codes:
        lh = latest_map.get(c)
        ph = prev_map.get(c)
        if lh is None:
            continue
        if ph is None:
            new.append(c)
        elif lh != ph:
            changed.append(c)

    missing_latest = [c for c in prev_map.keys() if c not in latest_map]

    return {
        "endpoint": endpoint,
        "total_latest": len(latest_map),
        "total_prev": len(prev_map),
        "changed": changed,
        "new": new,
        "missing_latest": missing_latest,
    }


async def list_snapshot_asofs(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    limit: int = 10,
) -> list[datetime]:
    """특정 endpoint의 스냅샷 배치(asof) 시점을 최신순으로 조회한다."""
    cur = (
        db[SNAPSHOTS_COL]
        .find({"endpoint": endpoint}, {"asof": 1})
        .sort("asof", DESCENDING)
        .limit(max(limit * 5, 50))
    )

    seen: set[datetime] = set()
    out: list[datetime] = []
    async for doc in cur:
        asof = doc.get("asof")
        if not isinstance(asof, datetime):
            continue
        if asof in seen:
            continue
        seen.add(asof)
        out.append(asof)
        if len(out) >= limit:
            break
    return out


async def diff_two_snapshot_batches(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    newer_asof: datetime,
    older_asof: datetime,
    include_unchanged: bool = False,
) -> dict[str, Any]:
    """두 스냅샷 배치를 payload_hash 기준으로 비교한다."""
    col = db[SNAPSHOTS_COL]

    pipeline: list[dict[str, Any]] = [
        {"$match": {"endpoint": endpoint, "asof": {"$in": [older_asof, newer_asof]}}},
        {"$project": {"code": 1, "asof": 1, "payload_hash": 1}},
        {"$group": {"_id": "$code", "pairs": {"$push": {"asof": "$asof", "h": "$payload_hash"}}}},
        {
            "$project": {
                "code": "$_id",
                "older": {
                    "$first": {
                        "$filter": {
                            "input": "$pairs",
                            "as": "p",
                            "cond": {"$eq": ["$$p.asof", older_asof]},
                        }
                    }
                },
                "newer": {
                    "$first": {
                        "$filter": {
                            "input": "$pairs",
                            "as": "p",
                            "cond": {"$eq": ["$$p.asof", newer_asof]},
                        }
                    }
                },
            }
        },
    ]

    changed: list[str] = []
    unchanged: list[str] = []
    new_codes: list[str] = []
    removed_codes: list[str] = []

    async for row in col.aggregate(pipeline):
        code = row.get("code")
        if not code:
            continue

        older = row.get("older")
        newer = row.get("newer")

        older_h = older.get("h") if isinstance(older, dict) else None
        newer_h = newer.get("h") if isinstance(newer, dict) else None

        if older_h is None and newer_h is not None:
            new_codes.append(code)
            continue
        if older_h is not None and newer_h is None:
            removed_codes.append(code)
            continue
        if older_h is None and newer_h is None:
            continue

        if older_h != newer_h:
            changed.append(code)
        elif include_unchanged:
            unchanged.append(code)

    result: dict[str, Any] = {
        "endpoint": endpoint,
        "older_asof": older_asof,
        "newer_asof": newer_asof,
        "changed_codes": changed,
        "new_codes": new_codes,
        "removed_codes": removed_codes,
    }
    if include_unchanged:
        result["unchanged_codes"] = unchanged
    return result


async def diff_latest_snapshot_batches(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    include_unchanged: bool = False,
) -> dict[str, Any]:
    """가장 최근 스냅샷과 직전 스냅샷을 비교한다."""
    asofs = await list_snapshot_asofs(db, endpoint=endpoint, limit=2)
    if len(asofs) < 2:
        return {
            "endpoint": endpoint,
            "older_asof": None,
            "newer_asof": asofs[0] if asofs else None,
            "changed_codes": [],
            "new_codes": [],
            "removed_codes": [],
            "note": "need at least 2 snapshot batches",
        }

    newer_asof, older_asof = asofs[0], asofs[1]
    return await diff_two_snapshot_batches(
        db,
        endpoint=endpoint,
        newer_asof=newer_asof,
        older_asof=older_asof,
        include_unchanged=include_unchanged,
    )


async def backfill_payload_hashes(
    db: AsyncDatabase,
    *,
    endpoint: Endpoints,
    which: str = "snapshots",  # "latest"|"snapshots"|"both"
    batch_size: int = 500,
) -> dict[str, int]:
    """payload_hash가 없는 문서에 대해 해시를 계산해 백필한다."""
    updated = 0

    async def _backfill_one(colname: str) -> None:
        nonlocal updated
        col = db[colname]

        cursor = col.find(
            {"endpoint": endpoint, "payload_hash": {"$exists": False}},
            {"_id": 1, "payload": 1},
            batch_size=batch_size,
        )

        ops: list[UpdateOne] = []
        async for row in cursor:
            _id = row.get("_id")
            payload = row.get("payload") or {}
            ops.append(UpdateOne({"_id": _id}, {"$set": {"payload_hash": stable_sha256(payload)}}))

            if len(ops) >= batch_size:
                res = await col.bulk_write(ops, ordered=False)
                updated += int(res.modified_count)
                ops.clear()

        if ops:
            res = await col.bulk_write(ops, ordered=False)
            updated += int(res.modified_count)
            ops.clear()

    from db2_hj3415.common.hash_utils import stable_sha256  # local import to avoid circulars

    if which in ("latest", "both"):
        await _backfill_one(LATEST_COL)
    if which in ("snapshots", "both"):
        await _backfill_one(SNAPSHOTS_COL)

    return {"updated": updated}
