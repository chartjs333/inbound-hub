import base64
import hashlib
import io

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from PIL import Image

from agent_channel_bridge.api import create_app
from agent_channel_bridge.gateway import Gateway, canonical, signature
from agent_channel_bridge.models import Channel, Request
from agent_channel_bridge.security import ArtifactStore, TrustStore
from agent_channel_bridge.simulator import SimulatedAdapter


@pytest.fixture
def mobile(tmp_path):
    identity = Ed25519PrivateKey.generate()
    publisher = Ed25519PrivateKey.generate()
    trust = TrustStore(
        {
            "identity": {"current": identity.public_key().public_bytes_raw()},
            "plugin": {"current": publisher.public_key().public_bytes_raw()},
        }
    )
    g = Gateway(
        str(tmp_path / "mobile.db"),
        b"t" * 32,
        b"i" * 32,
        b"p" * 32,
        lambda r: r.project_id == "project",
        clock=lambda: 1000,
        trust=trust,
    )
    g.register_channel(
        Channel(
            channel_id="human",
            type="human",
            owner="user",
            project_id="project",
            agents={"agent"},
            capabilities={"send_message", "request_observation"},
            consent={"request_observation"},
        )
    )
    artifacts = ArtifactStore(tmp_path / "artifacts")
    app = create_app(
        g, artifacts=artifacts, idp_url="https://identity.test/login", origin="https://hub.test"
    )
    client = TestClient(app, base_url="https://hub.test")
    yield g, client, identity, artifacts
    client.close()
    g.close()


def signed(key, proof):
    return (
        "current." + base64.b64encode(key.sign(b"identity\0" + canonical(proof).encode())).decode()
    )


def sign_in(mobile, user="user"):
    _g, client, key, _ = mobile
    response = client.post(
        "/mobile/challenge",
        headers={"Origin": "https://hub.test"},
        json={"user": user, "project": "project", "workstation": "phone"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    proof = {
        **data["binding"],
        "nonce": data["nonce"],
        "method": "passkey",
        "assurance": 2,
        "session_expires": 4000,
    }
    response = client.post(
        "/mobile/login",
        headers={"Origin": "https://hub.test"},
        json={"proof": proof, "signature": signed(key, proof)},
    )
    assert response.status_code == 200, response.text
    assert (
        "HttpOnly" in response.headers["set-cookie"] and "Secure" in response.headers["set-cookie"]
    )
    return {"Origin": "https://hub.test", "X-CSRF-Token": response.json()["csrf"]}


def intake(g, text="Observation", operation="request_observation"):
    req = Request(
        request_id="r",
        idempotency_key="r",
        correlation_id="c",
        project_id="project",
        sprint_id="s",
        assignment_id="a",
        agent_id="agent",
        channel_id="human",
        operation=operation,
        payload={"text": text},
        created_at=1000,
    )
    body = req.model_dump_json().encode()
    g.intake(body, "1000", signature(b"t" * 32, "1000", body))
    g.dispatch(SimulatedAdapter())


def test_mobile_login_presence_logout_and_csrf(mobile):
    g, c, _, _ = mobile
    assert c.get("/mobile/channels").status_code == 401
    headers = sign_in(mobile)
    assert c.get("/mobile/channels").json()[0]["channel_id"] == "human"
    assert c.post("/mobile/presence/human", json={"online": True}).status_code == 403
    assert (
        c.post(
            "/mobile/presence/human", headers={"Origin": "https://hub.test"}, json={"online": True}
        ).status_code
        == 403
    )
    assert (
        c.post("/mobile/presence/human", headers=headers, json={"online": False}).status_code == 200
    )
    assert g.get("presence", "human")["online"] is False
    assert c.post("/mobile/logout", headers=headers).status_code == 200
    assert c.get("/mobile/session").status_code == 401


def test_artifact_normalization_authorization_and_integrity(mobile):
    g, c, _, store = mobile
    headers = sign_in(mobile)
    intake(g)
    image = io.BytesIO()
    Image.new("RGB", (8, 8), "blue").save(image, format="PNG")
    response = c.post(
        "/mobile/requests/r/observation",
        headers={**headers, "Content-Type": "image/png"},
        content=image.getvalue(),
    )
    assert response.status_code == 200, response.text
    digest = response.json()["sha256"]
    assert hashlib.sha256(store.read(digest)).hexdigest() == digest
    assert c.get("/mobile/requests/r/artifacts/" + digest).status_code == 200
    sign_in(mobile, "other")
    assert c.get("/mobile/requests/r/artifacts/" + digest).status_code == 403
    assert c.get("/mobile/requests").json() == []


@pytest.mark.parametrize(
    "mime,data",
    [
        ("image/svg+xml", b'<svg onload="alert(1)"/>'),
        ("image/png", b"not a png"),
        ("text/plain", b"\xff"),
        ("audio/wav", b"RIFF-malformed"),
    ],
)
def test_malicious_media_rejected(mobile, mime, data):
    _, _, _, store = mobile
    with pytest.raises((ValueError, OSError, EOFError)):
        store.put(data, mime)


def test_public_key_rotation_forgery_and_key_purpose(mobile):
    g, _, key, _ = mobile
    proof = {"nonce": "n"}
    digest = signed(key, proof)
    g.trust.verify("identity", canonical(proof).encode(), digest)
    with pytest.raises(PermissionError):
        g.trust.verify("plugin", canonical(proof).encode(), digest)
    with pytest.raises(PermissionError):
        g.trust.verify("identity", b"changed", digest)
    g.trust.keys["identity"].clear()
    with pytest.raises(PermissionError):
        g.trust.verify("identity", canonical(proof).encode(), digest)


def test_mobile_headers_payload_limits_and_rate_limit(mobile):
    _, c, _, _ = mobile
    response = c.get("/mobile")
    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert (
        c.post(
            "/mobile/login",
            headers={"Origin": "https://hub.test", "Content-Length": "not-number"},
            content=b"{}",
        ).status_code
        == 400
    )
    assert (
        c.post(
            "/mobile/login", headers={"Origin": "https://hub.test"}, content=b"a" * 33000
        ).status_code
        == 413
    )
    for i in range(11):
        response = c.post(
            "/mobile/challenge",
            headers={"Origin": "https://hub.test"},
            json={"user": str(i), "project": "project", "workstation": "phone"},
        )
    assert response.status_code == 429


def test_untrusted_ui_text_is_data(mobile):
    g, c, _, _ = mobile
    sign_in(mobile)
    intake(g, "<img src=x onerror=alert(1)>")
    assert c.get("/mobile/requests").json()[0]["text"] == "<img src=x onerror=alert(1)>"
    script = c.get("/mobile/assets/app.js").text
    assert "innerHTML" not in script and "localStorage" not in script
    assert "event.source!==popup" in script


def test_revoked_identity_key_ends_existing_session(mobile):
    g, c, _, _ = mobile
    sign_in(mobile)
    g.trust.keys["identity"].clear()
    assert c.get("/mobile/session").status_code == 401


def test_pin_cannot_be_persisted_in_signed_assertion(mobile):
    g, c, key, _ = mobile
    nonce = g.challenge("user", "project", "phone")
    proof = {
        **g.get("challenge", nonce),
        "nonce": nonce,
        "method": "passkey",
        "assurance": 2,
        "pin": "1234",
    }
    response = c.post(
        "/mobile/login",
        headers={"Origin": "https://hub.test"},
        json={"proof": proof, "signature": signed(key, proof)},
    )
    assert response.status_code == 403
    assert g.db.execute("SELECT count(*) FROM objects WHERE kind='session'").fetchone()[0] == 0


def test_valid_audio_and_invalid_http_media(mobile):
    import wave

    g, c, _, store = mobile
    audio = io.BytesIO()
    with wave.open(audio, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(16000)
        out.writeframes(b"\0\0" * 160)
    _, digest, _, mime = store.put(audio.getvalue(), "audio/wav")
    assert mime == "audio/wav" and len(store.read(digest)) > 44
    headers = sign_in(mobile)
    intake(g)
    response = c.post(
        "/mobile/requests/r/observation",
        headers={**headers, "Content-Type": "image/png"},
        content=b"bad",
    )
    assert response.status_code == 422
