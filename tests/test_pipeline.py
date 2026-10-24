import asyncio
import json

import httpx
import pytest
from test_musician import event

from inbound_hub.coordinator import Coordinator
from inbound_hub.domains.registry import DomainPluginRegistration, DomainPluginRegistry
from inbound_hub.integrations.nginx_qa import NginxQaClient, NginxQaProposalTarget
from inbound_hub.pipeline import Pipeline, ProjectBinding, Store
from inbound_hub.sources import AdapterRuntime, EmlFolder


def pipeline(tmp_path, plugin, handler, notifier=None):
    registry = DomainPluginRegistry()
    registry.register(DomainPluginRegistration(plugin.metadata, plugin))
    store = Store(str(tmp_path / "hub.db"), ("secret-producer-token",))
    client = NginxQaClient(
        NginxQaProposalTarget("https://nginx.invalid", "9008"),
        "secret-producer-token",
        httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    return Pipeline(
        store,
        Coordinator(registry),
        ProjectBinding(
            "musician-booking",
            {"kind": "legacy_json", "payload": {"sprint_type": "legacy_v1", "actors": []}},
        ),
        client,
        notifier,
    )


def test_delivery_restart_dedupe_notifications_and_status(tmp_path, plugin):
    calls, messages = [], []

    def handler(request):
        calls.append(request)
        if request.method == "POST":
            return httpx.Response(201, json={"proposal": {"pending_sprint_id": "pending-1"}})
        return httpx.Response(200, json={"status": {"activation_state": "not_started"}})

    async def notifier(text):
        messages.append(text)

    p = pipeline(tmp_path, plugin, handler, notifier)
    p.store.ingest(event())
    p.store.ingest(event().model_copy(update={"event_id": "duplicate"}))
    asyncio.run(p.tick())
    assert len([x for x in calls if x.method == "POST"]) == 1
    assert len(messages) == 2
    assert p.store.db.execute("SELECT status FROM proposals").fetchone()[0] == "not_started"
    p.store.db.close()
    p.store = Store(str(tmp_path / "hub.db"))
    asyncio.run(p.tick())
    assert len([x for x in calls if x.method == "POST"]) == 1
    assert not any("/start" in str(x.url) for x in calls)
    assert "secret-producer-token" not in (tmp_path / "hub.db").read_bytes().decode(errors="ignore")


def test_retry_and_nonretryable_auth_failure(tmp_path, plugin):
    codes = [503, 401]
    p = pipeline(tmp_path, plugin, lambda r: httpx.Response(codes.pop(0)))
    p.store.ingest(event())
    asyncio.run(p.tick())
    assert p.store.db.execute("SELECT state FROM proposals").fetchone()[0] == "queued"
    p.store.db.execute("UPDATE proposals SET due=0")
    p.store.db.commit()
    asyncio.run(p.tick())
    assert p.store.db.execute("SELECT state FROM proposals").fetchone()[0] == "blocked"


def test_secret_conflict_and_correspondence(tmp_path, plugin):
    p = pipeline(tmp_path, plugin, lambda r: pytest.fail("No network for correspondence"))
    with pytest.raises(ValueError):
        p.store.ingest(event("password: forbidden"))
    p.store.ingest(event("Thank you"))
    with pytest.raises(ValueError):
        p.store.ingest(event("changed"))
    asyncio.run(p.tick())
    assert p.store.db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0


def test_eml_runtime_isolates_failure_and_checkpoints(tmp_path, plugin):
    folder = tmp_path / "mail"
    folder.mkdir()
    (folder / "offer.eml").write_text(
        "From: organizer@example.invalid\nSubject: Concert\nDate: Sat, 24 Oct 2026 10:00:00 +0000\nContent-Type: text/plain\n\nvenue: Hall\ncity: Berlin\nproposed_date: 2027-05-01"
    )
    p = pipeline(tmp_path, plugin, lambda r: httpx.Response(503))

    class Broken:
        async def poll(self, checkpoint):
            raise OSError("secret-producer-token")

    runtime = AdapterRuntime(p.store)
    runtime.register("email", EmlFolder(folder, {"artist_id": "alpha"}))
    runtime.register("broken", Broken())
    asyncio.run(runtime.tick())
    assert runtime.status["email"]["state"] == "Running"
    assert runtime.status["broken"]["error"] == "OSError"
    assert p.store.db.execute("SELECT count(*) FROM events").fetchone()[0] == 1
    runtime.pause(True)
    assert runtime.status["email"]["state"] == "Paused"


def test_notification_outage_does_not_block_proposal(tmp_path, plugin):
    async def broken(text):
        raise OSError("outage")

    p = pipeline(
        tmp_path,
        plugin,
        lambda r: httpx.Response(201, json={"proposal": {"pending_sprint_id": "p"}}),
        broken,
    )
    p.store.ingest(event())
    asyncio.run(p.tick())
    assert p.store.db.execute("SELECT state FROM proposals").fetchone()[0] == "submitted"
    assert p.store.db.execute("SELECT count(*) FROM notifications WHERE sent=0").fetchone()[0] > 0


def test_metadata_credentials_rejected(tmp_path):
    store = Store(str(tmp_path / "security.db"))
    with pytest.raises(ValueError):
        store.ingest(
            event().model_copy(update={"metadata": {"nested": {"access_token": "unknown-secret"}}})
        )
    assert store.db.execute("SELECT count(*) FROM events").fetchone()[0] == 0


def test_service_auth_lifecycle_and_tray(tmp_path, plugin):
    from fastapi.testclient import TestClient

    from inbound_hub.service import create_service
    from inbound_hub.tray import TrayController

    p = pipeline(tmp_path, plugin, lambda r: httpx.Response(503))
    runtime = AdapterRuntime(p.store)

    class Empty:
        async def poll(self, checkpoint):
            return [], "1"

    runtime.register("email", Empty())
    restart_requests = []
    app = create_service(p, runtime, "x" * 32, lambda: restart_requests.append(True))
    with TestClient(app) as client:
        assert client.get("/control/status").status_code == 401
        tray = TrayController("http://localhost", "x" * 32, client)
        assert "email" in tray.status()["adapters"]
        tray.action("pause")
        assert tray.status()["adapters"]["email"]["state"] == "Paused"
        tray.action("resume")
        assert tray.status()["adapters"]["email"]["state"] == "Running"
        tray.action("restart")
        assert restart_requests == [True]
        with pytest.raises(ValueError):
            tray.action("stop")


def test_telegram_chat_scope_and_checkpoint():
    from inbound_hub.sources import TelegramSource

    def handler(request):
        return httpx.Response(
            200,
            json={
                "ok": True,
                "result": [
                    {
                        "update_id": 1,
                        "message": {
                            "message_id": 3,
                            "chat": {"id": 42},
                            "text": "concert",
                            "date": 1000,
                        },
                    },
                    {
                        "update_id": 2,
                        "message": {
                            "message_id": 4,
                            "chat": {"id": 99},
                            "text": "private",
                            "date": 1000,
                        },
                    },
                ],
            },
        )

    source = TelegramSource(
        "secret", "bot", {"42"}, client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    events, offset = asyncio.run(source.poll(None))
    assert offset == "3" and len(events) == 1 and events[0].channel == "telegram"
    assert "secret" not in events[0].model_dump_json()


def test_imap_size_gate_and_checkpoint(monkeypatch):
    from inbound_hub.sources import ImapSource

    raw = b"From: example@example.invalid\nContent-Type: text/plain\n\nConcert"
    calls = []

    class FakeImap:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def login(self, *args):
            pass

        def select(self, *args, **kwargs):
            assert kwargs["readonly"] is True

        def response(self, name):
            return name, [b"123"]

        def uid(self, command, *args):
            calls.append((command, args))
            if command == "search":
                return "OK", [b"1"]
            if args[-1] == "(RFC822.SIZE)":
                return "OK", [b"1 (RFC822.SIZE 100)"]
            return "OK", [(b"1", raw)]

    monkeypatch.setattr("inbound_hub.sources.imaplib.IMAP4_SSL", FakeImap)
    source = ImapSource("mail.invalid", "user", "secret")
    events, checkpoint = asyncio.run(source.poll(None))
    assert checkpoint == "123:1" and len(events) == 1
    assert calls[-2][1][-1] == "(RFC822.SIZE)"
    assert "secret" not in events[0].model_dump_json()


def test_pending_proposal_carries_specialist_roles(tmp_path, plugin):
    from inbound_hub.domains.musician import ROLES

    seen = []

    def handler(request):
        if request.method == "POST":
            seen.append(json.loads(request.content))
        return httpx.Response(201, json={"proposal": {"pending_sprint_id": "p"}})

    p = pipeline(tmp_path, plugin, handler)
    p.binding = ProjectBinding(
        "musician-booking",
        p.binding.candidate,
        {role: {"id": f"agent-{i}", "phone": str(2100 + i)} for i, role in enumerate(ROLES)},
    )
    p.store.ingest(event())
    asyncio.run(p.tick())
    actors = seen[0]["candidate"]["payload"]["agents"]["items"]
    assert len(actors) == 6
    assert all(plugin.profiles.commit in actor["tasks"][0] for actor in actors)


def test_telegram_logs_redact_token(caplog):
    import logging

    from inbound_hub.sources import TelegramNotifier

    token = "telegram-secret-credential"
    notifier = TelegramNotifier(
        token,
        "42",
        httpx.AsyncClient(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"ok": True}))
        ),
    )
    with caplog.at_level(logging.INFO, logger="httpx"):
        asyncio.run(notifier("Status only"))
    assert token not in caplog.text


def test_sprint_update_requires_review_and_never_submits(tmp_path, plugin):
    p = pipeline(tmp_path, plugin, lambda r: pytest.fail("No submission for update intent"))
    p.store.ingest(event(sprint_id="existing", artist_id="alpha"))
    asyncio.run(p.tick())
    assert p.store.db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 0
    result = json.loads(p.store.db.execute("SELECT result FROM events").fetchone()[0])
    assert result["coordinator_route"] == "sprint_update"
    assert result["update_intent"]["status"] == "requires_review"


def test_folder_adapter_deduplicates_stable_content(tmp_path):
    from inbound_hub.sources import FolderSource

    (tmp_path / "request.txt").write_text("Concert")
    source = FolderSource(tmp_path)
    first, _ = asyncio.run(source.poll(None))
    second, _ = asyncio.run(source.poll(None))
    assert first[0].event_id == second[0].event_id and first[0].channel == "folder"


def test_windows_host_restarts_only_on_explicit_request():
    from inbound_hub.windows_service import ServiceHost

    runs = []
    host = None

    class Server:
        def __init__(self, config):
            self.should_exit = False

        def run(self):
            runs.append(True)
            if len(runs) == 1:
                host.restart()
            else:
                host.stop()

    host = ServiceHost(factory=lambda restart: (object(), 8080), server_factory=Server)
    host.run()
    assert len(runs) == 2


def test_telegram_rejects_empty_credentials_and_redacts_polling_logs():
    import logging

    from inbound_hub.sources import SecretLogFilter, TelegramNotifier, TelegramSource

    for constructor in (lambda: SecretLogFilter(""), lambda: TelegramNotifier("", "1"),
                        lambda: TelegramSource("", "telegram", ["1"])):
        with pytest.raises(ValueError, match="nonempty"):
            constructor()
    record = logging.LogRecord("httpx", logging.INFO, "", 0,
                               "GET https://api.telegram.org/bot%s/getUpdates", ("test-secret",), None)
    assert SecretLogFilter("test-secret").filter(record)
    assert "test-secret" not in record.getMessage()
