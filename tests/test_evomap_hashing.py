from evomap.hashing import attach_asset_id, canonical_json, compute_asset_id, verify_asset_id


def test_canonical_json_sorts_keys_recursively():
    assert canonical_json({"b": 1, "a": {"d": 4, "c": 3}}) == '{"a":{"c":3,"d":4},"b":1}'


def test_asset_id_is_deterministic_and_ignores_claimed_id():
    left = {"type": "Gene", "summary": "same", "nested": {"b": 2, "a": 1}}
    right = {"nested": {"a": 1, "b": 2}, "summary": "same", "type": "Gene", "asset_id": "sha256:bad"}
    assert compute_asset_id(left) == compute_asset_id(right)


def test_attach_and_verify_asset_id():
    asset = attach_asset_id({"type": "Capsule", "summary": "hello"})
    assert asset["asset_id"].startswith("sha256:")
    assert verify_asset_id(asset)
    assert not verify_asset_id({**asset, "summary": "changed"})
