"""Backend-only EvoMap/GEP integration helpers for Veridia."""

from evomap.assets import build_bundle, load_trace, validate_trace_contract
from evomap.hashing import attach_asset_id, compute_asset_id, verify_asset_id

__all__ = [
    "attach_asset_id",
    "build_bundle",
    "compute_asset_id",
    "load_trace",
    "validate_trace_contract",
    "verify_asset_id",
]
