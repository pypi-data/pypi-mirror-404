# db2_hj3415/common/hash_utils.py
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _normalize(obj: Any) -> Any:
    """Normalize a payload into a stable JSON-serializable form.

    This is used to create deterministic hashes for NFS payload diffs.

    Rules
    - dict: normalize values recursively
    - list/tuple: normalize items
    - datetime/date: ISO 8601 string
    - Decimal: string
    - float NaN/Inf: None (treat as missing)
    - other: keep as-is when JSON serializable, else str(obj)
    """

    if obj is None:
        return None

    if isinstance(obj, (str, int, bool)):
        return obj

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj

    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    if isinstance(obj, dict):
        return {str(k): _normalize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_normalize(v) for v in obj]

    # fallback: try JSON serialization, else string
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def stable_json(payload: Any) -> str:
    """Return deterministic JSON string for hashing."""
    normalized = _normalize(payload)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def stable_sha256(payload: Any) -> str:
    """Compute SHA-256 hex digest for a payload."""
    s = stable_json(payload)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
