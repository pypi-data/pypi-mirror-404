# db2_hj3415/universe/domain.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, TypedDict

# ---- domain constants / aliases ----

UNIVERSE_LATEST_COL = "universe_latest"
UNIVERSE_SNAPSHOTS_COL = "universe_snapshots"

# ---- domain types ----

class UniverseItem(TypedDict, total=False):
    """
    최소 확장 대비:
    - code: 식별자(필수)
    - name: 표시명(옵션)
    - market: KRX/US 등 (옵션)
    - meta: 기타(옵션)
    """
    code: str
    name: str
    market: str
    meta: dict[str, Any]


class UniverseLatestDoc(TypedDict):
    _id: str                 # universe_name
    universe: str
    asof: datetime
    source: str              # ex) "samsungfund"
    items: list[UniverseItem]


class UniverseSnapshotDoc(TypedDict):
    universe: str
    asof: datetime
    source: str
    items: list[UniverseItem]


# ---- domain rules / normalization ----

def normalize_items(items: Iterable[Any]) -> list[UniverseItem]:
    """
    krx 프로젝트 CodeItem(dataclass) / dict / pydantic model 등
    최대한 받아서 UniverseItem(list[dict])로 정규화.
    """
    out: list[UniverseItem] = []
    for it in items:
        if it is None:
            continue

        # pydantic v2
        if hasattr(it, "model_dump"):
            d = it.model_dump()
        elif isinstance(it, dict):
            d = dict(it)
        else:
            # dataclass / 객체 접근 fallback
            d = {
                "code": getattr(it, "code", None),
                "name": getattr(it, "name", None),
                "market": getattr(it, "market", None),
                "meta": getattr(it, "meta", None),
            }

        code = (d.get("code") or "").strip()
        if not code:
            continue

        item: UniverseItem = {"code": code}

        name = d.get("name")
        if isinstance(name, str) and name.strip():
            item["name"] = name.strip()

        market = d.get("market")
        if isinstance(market, str) and market.strip():
            item["market"] = market.strip()

        meta = d.get("meta")
        if isinstance(meta, dict) and meta:
            item["meta"] = meta

        out.append(item)

    return out


# ---- doc builders (domain) ----

def build_universe_latest_doc(
    *,
    universe: str,
    items: Iterable[Any],
    asof: datetime,
    source: str,
) -> UniverseLatestDoc:
    return {
        "_id": universe,
        "universe": universe,
        "asof": asof,
        "source": source,
        "items": normalize_items(items),
    }


def build_universe_snapshot_doc(
    *,
    universe: str,
    items: Iterable[Any],
    asof: datetime,
    source: str,
) -> UniverseSnapshotDoc:
    return {
        "universe": universe,
        "asof": asof,
        "source": source,
        "items": normalize_items(items),
    }