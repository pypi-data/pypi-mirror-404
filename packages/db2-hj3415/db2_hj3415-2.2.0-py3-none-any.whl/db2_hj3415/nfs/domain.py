# db2_hj3415/nfs/domain.py
from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict

from contracts_hj3415.nfs.types import Endpoints
from db2_hj3415.common.hash_utils import stable_sha256


LATEST_COL = "nfs_latest"
SNAPSHOTS_COL = "nfs_snapshots"


class NfsLatestDoc(TypedDict):
    _id: str
    endpoint: str
    code: str
    asof: datetime
    payload: dict[str, Any]
    payload_hash: str


class NfsSnapshotDoc(TypedDict):
    endpoint: str
    code: str
    asof: datetime
    payload: dict[str, Any]
    payload_hash: str



def latest_id(endpoint: Endpoints, code: str) -> str:
    return f"{endpoint}:{code}"


def compute_payload_hash(payload: dict[str, Any]) -> str:
    return stable_sha256(payload)


def build_latest_doc(
    *,
    endpoint: Endpoints,
    code: str,
    payload: dict[str, Any],
    asof: datetime,
) -> NfsLatestDoc:
    return {
        "_id": latest_id(endpoint, code),
        "endpoint": endpoint,
        "code": code,
        "asof": asof,
        "payload": payload,
        "payload_hash": compute_payload_hash(payload),
    }


def build_snapshot_doc(
    *,
    endpoint: Endpoints,
    code: str,
    payload: dict[str, Any],
    asof: datetime,
) -> NfsSnapshotDoc:
    return {
        "endpoint": endpoint,
        "code": code,
        "asof": asof,
        "payload": payload,
        "payload_hash": compute_payload_hash(payload),
    }