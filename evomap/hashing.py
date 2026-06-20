"""Content-addressable IDs for EvoMap GEP assets."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


ASSET_ID_PREFIX = "sha256:"


def asset_payload(asset: Mapping[str, Any]) -> dict[str, Any]:
    """Return the top-level asset payload used for hashing.

    EvoMap documents asset identity as the SHA-256 of canonical JSON after
    removing the asset's own top-level ``asset_id`` field. Nested references to
    other assets are intentional content and must remain in the payload.
    """
    payload = deepcopy(dict(asset))
    payload.pop("asset_id", None)
    return payload


def canonical_json(value: Any) -> str:
    """Serialize JSON with deterministic key order and compact separators."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_asset_id(asset: Mapping[str, Any]) -> str:
    """Compute ``sha256:<hex>`` for an EvoMap asset."""
    encoded = canonical_json(asset_payload(asset)).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()
    return f"{ASSET_ID_PREFIX}{digest}"


def attach_asset_id(asset: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``asset`` with its deterministic ``asset_id`` set."""
    out = deepcopy(dict(asset))
    out["asset_id"] = compute_asset_id(out)
    return out


def verify_asset_id(asset: Mapping[str, Any]) -> bool:
    """Check whether an asset's claimed ID matches its content."""
    claimed = asset.get("asset_id")
    return isinstance(claimed, str) and claimed == compute_asset_id(asset)
