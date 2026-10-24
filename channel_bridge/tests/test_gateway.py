import hashlib

import pytest
from fastapi.testclient import TestClient

from agent_channel_bridge.api import create_app
from agent_channel_bridge.gateway import Gateway, canonical, signature
from agent_channel_bridge.models import Channel, Plugin, Request
from agent_channel_bridge.simulator import (
    NginxQaSimulator,
    SimulatedAdapter,
    SmartCardIdentitySimulator,
)

KEY, IDKEY, PLUGINKEY = b"t" * 32, b"i" * 32, b"p" * 32


@pytest.fixture
def system(tmp_path):
    now = [1000.0]
    nginx = NginxQaSimulator(KEY, {("project", "sprint", "assignment", "agent")}, lambda: now[0])
    gateway = Gateway(
        str(tmp_path / "state.db"), KEY, IDKEY, PLUGINKEY, nginx.active, lambda: now[0]
    )
    gateway.register_channel(
        Channel(
            channel_id="human",
            type="human",
            owner="user",
            project_id="project",
            agents={"agent"},
            capabilities={"send_message", "request_live_session"},
            consent={"request_live_session"},
        )
    )
    yield gateway, nginx, now
    gateway.close()


def request(gateway, ident="r1", **kwargs):
    return Request(
        request_id=ident,
        idempotency_key=ident,
        correlation_id="corr",
        project_id="project",
        sprint_id="sprint",
        assignment_id="assignment",
        agent_id="agent",
        channel_id="human",
        operation="send_message",
        created_at=gateway.clock(),
    ).model_copy(update=kwargs)


def submit(gateway, req):
    body = req.model_dump_json().encode()
    stamp = str(gateway.clock())
    return gateway.intake(body, stamp, signature(KEY, stamp, body))


def login(gateway, user="user", workstation="station"):
    nonce = gateway.challenge(user, "project", workstation)
    proof, digest = SmartCardIdentitySimulator(IDKEY).prove(gateway, nonce)
    return gateway.login(proof, digest)


def device(gateway):
    plugin = Plugin(
        plugin_id="microscope",
        version="1.0",
        runtime_target="ios",
        models={"scope"},
        capabilities={"request_data", "request_observation"},
        sha256="a" * 64,
        install_source="https://apps.apple.com/app/trusted",
        minimum_app_version=(1, 0, 0),
        approved=True,
    )
    gateway.register_plugin(
        plugin,
        signature(PLUGINKEY, "manifest-v1", canonical(plugin.model_dump(mode="json")).encode()),
    )
    gateway.register_checkpoint("qr", "project", "device", "scope", "simulated")
    gateway.register_channel(
        Channel(
            channel_id="scope",
            type="device",
            owner="user",
            project_id="project",
            agents={"agent"},
            device_id="device",
            plugin_id="microscope",
            capabilities={"request_data", "request_observation"},
            consent={"request_observation"},
            required_assurance_level=2,
        )
    )
    session = login(gateway)
    gateway.activate(session, "qr", "microscope", (1, 0, 0), True)
    grant = gateway.grant(session, "scope", "agent", "request_observation")
    return session, grant


def test_intake_dedupe_conflict_and_restart(system):
    g, nginx, now = system
    req = request(g)
    assert submit(g, req) == submit(g, req)
    with pytest.raises(ValueError):
        submit(g, req.model_copy(update={"payload": {"text": "different"}}))
    # A second process connection sees durable pending work.
    path = g.db.execute("PRAGMA database_list").fetchone()[2]
    second = Gateway(path, KEY, IDKEY, PLUGINKEY, nginx.active, lambda: now[0])
    adapter = SimulatedAdapter()
    second.dispatch(adapter)
    second.close()
    assert len(adapter.deliveries) == 1
    assert g.db.execute("SELECT status FROM requests").fetchone()[0] == "delivered"


@pytest.mark.parametrize(
    "online,stale,expected",
    [
        (False, False, "send_message"),
        (True, False, "request_live_session"),
        (True, True, "send_message"),
    ],
)
def test_presence(system, online, stale, expected):
    g, _, now = system
    session = login(g)
    g.presence(session, "human", online)
    if stale:
        now[0] += 61
    submit(g, request(g, operation="request_live_session"))
    adapter = SimulatedAdapter()
    g.dispatch(adapter)
    assert adapter.deliveries["r1"]["operation"] == expected


def test_unknown_presence_and_unanswered_fallback(system):
    g, _, now = system
    session = login(g)
    g.presence(session, "human", True)
    submit(g, request(g, operation="request_live_session"))
    adapter = SimulatedAdapter()
    adapter.failures = 2
    for _ in range(3):
        g.dispatch(adapter)
        now[0] += 5
    assert adapter.deliveries["r1"]["operation"] == "send_message"


@pytest.mark.parametrize(
    "change",
    [
        {"project_id": "other"},
        {"agent_id": "other"},
        {"sprint_id": "inactive"},
        {"operation": "request_data"},
        {"created_at": 0},
    ],
)
def test_unauthorized_intake(system, change):
    g, _, _ = system
    with pytest.raises(PermissionError):
        submit(g, request(g, **change))


def test_transport_replay_and_malicious_payload(system):
    g, _, _ = system
    body = request(g).model_dump_json().encode()
    with pytest.raises(PermissionError):
        g.intake(body, "1000", "forged")
    with pytest.raises(PermissionError):
        g.intake(body, "0", signature(KEY, "0", body))
    with pytest.raises(ValueError):
        submit(g, request(g, payload={"command": "actuate"}))


def test_callback_outage_dedup_and_correlation(system):
    g, nginx, now = system
    submit(g, request(g))
    g.dispatch(SimulatedAdapter())
    nginx.failures = 2
    g.callbacks(nginx.receive)
    now[0] += 10
    g.callbacks(nginx.receive)
    g.callbacks(nginx.receive)
    assert len(nginx.events) == 2
    assert {e["correlation_id"] for e in nginx.events.values()} == {"corr"}


def test_cancel_deadline_and_independent_requests(system):
    g, _, _ = system
    submit(g, request(g, "cancel"))
    g.cancel("cancel", "project")
    submit(g, request(g, "expire", deadline=999))
    submit(g, request(g, "ok"))
    g.dispatch(SimulatedAdapter())
    assert dict(g.db.execute("SELECT id,status FROM requests")) == {
        "cancel": "cancelled",
        "expire": "expired",
        "ok": "delivered",
    }


def test_device_observation_and_no_qr_authority(system):
    g, nginx, _ = system
    session, grant = device(g)
    with pytest.raises(PermissionError):
        submit(g, request(g, channel_id="scope", operation="request_observation"))
    req = request(
        g,
        channel_id="scope",
        operation="request_observation",
        checkpoint_id="qr",
        experiment_id="experiment",
        payload={"grant_id": grant},
    )
    submit(g, req)
    g.dispatch(SimulatedAdapter())
    data = b"simulated read-only observation"
    digest = hashlib.sha256(data).hexdigest()
    g.observation("r1", session, "artifact://sha256/" + digest, digest, data)
    g.callbacks(nginx.receive)
    response = next(e for e in nginx.events.values() if e["event_type"] == "response_received")
    assert response["sha256"] == digest
    assert response["source_metadata"]["experiment_id"] == "experiment"
    with pytest.raises(ValueError):
        g.observation("r1", session, "artifact://sha256/" + digest, digest, data)


def test_revocation_rechecked_on_dispatch(system):
    g, _, _ = system
    session, grant = device(g)
    submit(
        g,
        request(
            g, channel_id="scope", operation="request_observation", payload={"grant_id": grant}
        ),
    )
    g.revoke(session)
    adapter = SimulatedAdapter()
    g.dispatch(adapter)
    assert not adapter.deliveries
    assert g.db.execute("SELECT status FROM requests").fetchone()[0] == "rejected"


def test_forgery_challenge_replay_uid_and_switch(system):
    g, _, _ = system
    nonce = g.challenge("user", "project", "station")
    sim = SmartCardIdentitySimulator(IDKEY)
    proof, digest = sim.prove(g, nonce, method="static_uid")
    with pytest.raises(PermissionError):
        g.login(proof, digest)
    proof, digest = sim.prove(g, nonce)
    first = g.login(proof, digest)
    with pytest.raises(PermissionError):
        g.login(proof, digest)
    login(g, user="other")
    with pytest.raises(PermissionError):
        g.session(first)


def test_qr_manifest_and_module_permissions(system):
    g, _, _ = system
    session, _ = device(g)
    with pytest.raises(PermissionError):
        g.discover("forged-qr", "project")
    with pytest.raises(PermissionError):
        g.discover("qr", "other")
    with pytest.raises(PermissionError):
        g.activate(session, "qr", "microscope", (0, 0, 1), True)
    with pytest.raises(PermissionError):
        g.grant(session, "scope", "intruder", "request_observation")
    with pytest.raises(PermissionError):
        g.grant(session, "scope", "agent", "configure_device")


def test_http_intake(system):
    g, _, _ = system
    client = TestClient(create_app(g))
    body = request(g).model_dump_json().encode()
    assert client.post("/v1/channel-requests", content=body).status_code == 422
    response = client.post(
        "/v1/channel-requests",
        content=body,
        headers={"X-Timestamp": "1000", "X-Signature": signature(KEY, "1000", body)},
    )
    assert response.status_code == 200
    assert response.json()["request_id"] == "r1"


def test_step_up_binding_expiry_and_lockout(system):
    g, _, now = system
    session, _ = device(g)
    now[0] += 61
    with pytest.raises(PermissionError):
        g.grant(session, "scope", "agent", "request_observation")
    nonce = g.challenge(
        "user", "project", "station", "request_observation", "device", "microscope", session
    )
    proof, digest = SmartCardIdentitySimulator(IDKEY).prove(g, nonce, assurance=3)
    grant = g.grant(session, "scope", "agent", "request_observation", proof, digest)
    assert g.get("grant", grant)["session"] == session
    with pytest.raises(PermissionError):
        g.grant(session, "scope", "agent", "request_observation", proof, digest)
    now[0] += 61
    with pytest.raises(PermissionError):
        submit(
            g,
            request(
                g, channel_id="scope", operation="request_observation", payload={"grant_id": grant}
            ),
        )
    nonce = g.challenge("user", "project", "other-station")
    proof, digest = SmartCardIdentitySimulator(IDKEY).prove(g, nonce)
    for _ in range(5):
        with pytest.raises(PermissionError):
            g.login(proof, "forged")
    with pytest.raises(PermissionError):
        g.login(proof, digest)


def test_idle_timeout_and_absolute_expiry(system):
    g, _, now = system
    session = login(g)
    now[0] += 301
    with pytest.raises(PermissionError):
        g.session(session)
    session = login(g)
    now[0] += 3601
    with pytest.raises(PermissionError):
        g.session(session)


def test_one_channel_outage_does_not_block_another(system):
    g, _, now = system
    submit(g, request(g, "first"))
    submit(g, request(g, "second"))
    adapter = SimulatedAdapter()
    adapter.failures = 1
    g.dispatch(adapter)
    assert "second" in adapter.deliveries
    assert "first" not in adapter.deliveries
    now[0] += 3
    g.dispatch(adapter)
    assert len(adapter.deliveries) == 2


def test_tampered_manifest_and_observation(system):
    g, _, _ = system
    session, grant = device(g)
    plugin = Plugin(**g.get("plugin", "microscope"))
    with pytest.raises(PermissionError):
        g.register_plugin(plugin, "forged")
    submit(
        g,
        request(
            g, channel_id="scope", operation="request_observation", payload={"grant_id": grant}
        ),
    )
    g.dispatch(SimulatedAdapter())
    with pytest.raises(ValueError):
        g.observation("r1", session, "artifact://sha256/" + "a" * 64, "a" * 64, b"tampered")


def test_https_callbacks_use_configured_destination(system):
    import httpx

    from agent_channel_bridge.transport import CallbackClient

    g, nginx, _ = system

    def receive(req):
        nginx.receive(req.content, req.headers["X-Timestamp"], req.headers["X-Signature"])
        return httpx.Response(204)

    client = CallbackClient(
        "https://nginx.example.invalid/events", httpx.Client(transport=httpx.MockTransport(receive))
    )
    submit(g, request(g))
    g.dispatch(SimulatedAdapter())
    g.callbacks(client)
    assert len(nginx.events) == 2
    client.close()
    with pytest.raises(ValueError):
        CallbackClient("http://insecure.invalid")


def test_policy_change_invalidates_existing_grant(system):
    g, _, _ = system
    _, grant = device(g)
    submit(
        g,
        request(
            g, channel_id="scope", operation="request_observation", payload={"grant_id": grant}
        ),
    )
    channel = g.get("channel", "scope")
    channel["required_assurance_level"] = 3
    g.register_channel(Channel(**channel))
    adapter = SimulatedAdapter()
    g.dispatch(adapter)
    assert not adapter.deliveries
    assert g.db.execute("SELECT status FROM requests").fetchone()[0] == "rejected"
