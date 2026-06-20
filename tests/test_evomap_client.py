import json

import pytest

from evomap.client import EvoMapHTTPError, NodeCredentials, build_envelope, validate_bundle


def test_build_envelope_matches_gep_a2a_shape():
    envelope = build_envelope("publish", {"assets": []}, sender_id="node_123")
    assert envelope["protocol"] == "gep-a2a"
    assert envelope["protocol_version"] == "1.0.0"
    assert envelope["message_type"] == "publish"
    assert envelope["sender_id"] == "node_123"
    assert envelope["message_id"].startswith("msg_")
    assert envelope["timestamp"].endswith("Z")


def test_node_credentials_from_env(monkeypatch):
    monkeypatch.setenv("EVOMAP_NODE_ID", "node_abc")
    monkeypatch.setenv("EVOMAP_NODE_SECRET", "secret")
    assert NodeCredentials.from_env() == NodeCredentials("node_abc", "secret")


def test_node_credentials_requires_env(monkeypatch):
    monkeypatch.delenv("EVOMAP_NODE_ID", raising=False)
    monkeypatch.delenv("EVOMAP_NODE_SECRET", raising=False)
    with pytest.raises(RuntimeError, match="EVOMAP_NODE_ID"):
        NodeCredentials.from_env()


def test_validate_bundle_uses_validate_endpoint(monkeypatch):
    calls = []

    def fake_post(path, envelope, node_secret=None, base_url="https://evomap.ai", timeout=30.0):
        calls.append((path, envelope, node_secret, base_url, timeout))
        return {"payload": {"decision": "accepted"}}

    monkeypatch.setattr("evomap.client.post_envelope", fake_post)
    response = validate_bundle(
        [{"type": "Gene", "asset_id": "sha256:1"}, {"type": "Capsule", "asset_id": "sha256:2"}],
        NodeCredentials("node_abc", "secret"),
        base_url="https://example.test",
        timeout=5,
    )
    path, envelope, secret, base_url, timeout = calls[0]
    assert response["payload"]["decision"] == "accepted"
    assert path == "/a2a/validate"
    assert envelope["message_type"] == "publish"
    assert envelope["payload"]["assets"][0]["type"] == "Gene"
    assert secret == "secret"
    assert base_url == "https://example.test"
    assert timeout == 5


def test_http_error_keeps_bounded_body():
    error = EvoMapHTTPError(422, json.dumps({"error": "bad"}) * 1000)
    assert error.status == 422
    assert len(error.body) <= 2000
