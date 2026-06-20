"""Small EvoMap A2A client primitives.

Network calls are opt-in: no registration, validation, fetch, heartbeat, or
publish happens unless a CLI/user path calls these functions explicitly.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from secrets import token_hex
from typing import Any

EVOMAP_BASE_URL = "https://evomap.ai"
PROTOCOL = "gep-a2a"
PROTOCOL_VERSION = "1.0.0"


class EvoMapError(RuntimeError):
    """Base EvoMap client error."""


class EvoMapHTTPError(EvoMapError):
    """HTTP error with a bounded response body for diagnostics."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body[:2000]
        super().__init__(f"EvoMap HTTP {status}: {self.body}")


@dataclass(frozen=True)
class NodeCredentials:
    node_id: str
    node_secret: str

    @classmethod
    def from_env(
        cls,
        node_id_env: str = "EVOMAP_NODE_ID",
        node_secret_env: str = "EVOMAP_NODE_SECRET",
    ) -> "NodeCredentials":
        node_id = os.environ.get(node_id_env, "").strip()
        node_secret = os.environ.get(node_secret_env, "").strip()
        if not node_id:
            raise EvoMapError(f"missing {node_id_env}")
        if not node_secret:
            raise EvoMapError(f"missing {node_secret_env}")
        return cls(node_id=node_id, node_secret=node_secret)


def utc_now_iso() -> str:
    """Return ISO 8601 UTC timestamp with millisecond precision."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def message_id() -> str:
    """Return EvoMap-style unique message ID."""
    return f"msg_{int(time.time() * 1000)}_{token_hex(4)}"


def build_envelope(
    message_type: str,
    payload: dict[str, Any],
    sender_id: str | None = None,
) -> dict[str, Any]:
    """Build a GEP-A2A envelope."""
    envelope = {
        "protocol": PROTOCOL,
        "protocol_version": PROTOCOL_VERSION,
        "message_type": message_type,
        "message_id": message_id(),
        "timestamp": utc_now_iso(),
        "payload": payload,
    }
    if sender_id:
        envelope["sender_id"] = sender_id
    return envelope


def post_envelope(
    path: str,
    envelope: dict[str, Any],
    node_secret: str | None = None,
    base_url: str = EVOMAP_BASE_URL,
    timeout: float = 30.0,
    impersonate: str = "chrome",
) -> dict[str, Any]:
    """POST an A2A envelope and decode the JSON response."""
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
    }
    if node_secret:
        headers["authorization"] = f"Bearer {node_secret}"

    try:
        from curl_cffi import requests

        response = requests.post(
            url,
            json=envelope,
            headers=headers,
            impersonate=impersonate,
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise EvoMapHTTPError(response.status_code, response.text)
        return response.json()
    except ImportError:
        pass

    body = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise EvoMapHTTPError(exc.code, raw) from exc
    except urllib.error.URLError as exc:
        raise EvoMapError(f"EvoMap request failed: {exc.reason}") from exc
    return json.loads(raw)


def hello(
    name: str,
    capabilities: dict[str, Any],
    model: str = "gpt-5",
    env_fingerprint: dict[str, Any] | None = None,
    base_url: str = EVOMAP_BASE_URL,
) -> dict[str, Any]:
    """Register/connect a node. Call only after explicit user authorization."""
    payload = {
        "name": name,
        "capabilities": capabilities,
        "model": model,
        "env_fingerprint": env_fingerprint or {},
    }
    return post_envelope("/a2a/hello", build_envelope("hello", payload), base_url=base_url)


def validate_bundle(
    assets: list[dict[str, Any]],
    credentials: NodeCredentials,
    base_url: str = EVOMAP_BASE_URL,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Dry-run validate a Gene+Capsule bundle via /a2a/validate."""
    envelope = build_envelope(
        "publish",
        {"assets": assets},
        sender_id=credentials.node_id,
    )
    return post_envelope(
        "/a2a/validate",
        envelope,
        node_secret=credentials.node_secret,
        base_url=base_url,
        timeout=timeout,
    )


def fetch_metadata(
    signals: list[str],
    credentials: NodeCredentials,
    base_url: str = EVOMAP_BASE_URL,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Search EvoMap assets without fetching paid payload content."""
    envelope = build_envelope(
        "fetch",
        {"signals": signals, "search_only": True},
        sender_id=credentials.node_id,
    )
    return post_envelope(
        "/a2a/fetch",
        envelope,
        node_secret=credentials.node_secret,
        base_url=base_url,
        timeout=timeout,
    )
