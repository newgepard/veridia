import pytest

from evomap.assets import build_bundle, trace_quality_score, validate_trace_contract
from evomap.hashing import verify_asset_id


def trace_fixture():
    return {
        "game_id": "veridia-ca-test",
        "codename": "veridia-ca",
        "config": {"width": 2, "height": 2, "steps": 2, "microscope": "template"},
        "frames": [
            {
                "step": 0,
                "width": 2,
                "height": 2,
                "belief": [0.1, 0.8, 0.4, 0.9],
                "type": [0, 1, 0, 1],
                "standing": [0.5, 0.5, 0.4, 0.7],
            },
            {
                "step": 2,
                "width": 2,
                "height": 2,
                "belief": [0.2, 0.7, 0.5, 0.8],
                "type": [0, 1, 0, 1],
                "standing": [0.5, 0.4, 0.4, 0.6],
            },
        ],
        "microscope": [
            {
                "step": 0,
                "x": 0,
                "y": 0,
                "claim": "belief is 0.1",
                "verdict": "truthful",
                "reason": "honest",
            },
            {
                "step": 0,
                "x": 1,
                "y": 0,
                "claim": "I tell the truth",
                "verdict": "lie",
                "reason": "manipulative",
            },
        ],
    }


def test_validate_trace_contract_summarizes_trace():
    summary = validate_trace_contract(trace_fixture())
    assert summary["frames"] == 2
    assert summary["width"] == 2
    assert summary["height"] == 2
    assert summary["microscope_verdicts"] == {"lie": 1, "truthful": 1}


def test_validate_trace_contract_rejects_bad_channels():
    trace = trace_fixture()
    trace["frames"][0]["belief"] = [0.1]
    with pytest.raises(ValueError, match="belief"):
        validate_trace_contract(trace)


def test_build_bundle_creates_verified_gep_triple():
    bundle = build_bundle(trace_fixture(), source_trace="fixtures/test-trace.json", diff_text="diff --git a/a b/a\n+new\n")
    assets = bundle["assets"]
    assert [asset["type"] for asset in assets] == ["Gene", "Capsule", "EvolutionEvent"]
    assert all(verify_asset_id(asset) for asset in assets)
    assert assets[0]["validation"][0].startswith("node -e ")
    assert assets[1]["gene"] == assets[0]["asset_id"]
    assert assets[2]["capsule_id"] == assets[1]["asset_id"]
    assert assets[1]["outcome"]["score"] == trace_quality_score(bundle["summary"])
    assert assets[1]["blast_radius"]["files"] >= 1
    assert assets[1]["blast_radius"]["lines"] >= 1
