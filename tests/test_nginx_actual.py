"""Opt-in integration against unchanged nginx-qa source, with isolated temporary state."""

import asyncio
import base64
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

import httpx
import pytest

from inbound_hub.integrations.nginx_qa import DeliveryError, NginxQaClient, NginxQaProposalTarget


def test_real_nginx_pending_api(tmp_path, monkeypatch, plugin):
    source = os.environ.get("NGINX_QA_SOURCE")
    if not source:
        pytest.skip("Set NGINX_QA_SOURCE to an unchanged nginx-qa checkout")
    sys.path.insert(0, str(Path(source).resolve()))
    monkeypatch.chdir(tmp_path)
    main = importlib.import_module("main")
    monkeypatch.setattr(main, "git_config_path", tmp_path / "projects.json")
    monkeypatch.setattr(main, "pending_sprints_path", tmp_path / "pending.json")
    monkeypatch.setattr(main, "git_config_lock", asyncio.Lock())
    monkeypatch.setattr(main, "pending_sprints_lock", asyncio.Lock())
    project = {
        "project_name": "Contract test",
        "git_address": "https://github.com/example/project.git",
        "git_context_key": "github.com/example/project",
        "project_phone": "9008",
        "groups": [],
        "group_relationships": [],
        "customer_reporting": {},
    }
    main.git_config_path.write_text(
        json.dumps(
            {
                main.PROJECTS_KEY: {project["git_context_key"]: project},
                main.PHONE_GIT_CONTEXTS_KEY: {"9008": {**project, "phone": "9008"}},
            }
        )
    )
    token = base64.urlsafe_b64encode(b"A" * 32).decode().rstrip("=")
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "producers": [
                    {
                        "producer_id": "inbound-hub",
                        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                        "project_ids": ["9008"],
                        "actions": ["create", "read"],
                    }
                ],
            }
        )
    )
    registry.chmod(0o600)
    monkeypatch.setenv(main.INBOUND_PRODUCER_REGISTRY_ENV, str(registry))

    async def exercise():
        transport = httpx.ASGITransport(app=main.app)
        client = NginxQaClient(
            NginxQaProposalTarget("http://127.0.0.1", "9008"),
            token,
            httpx.AsyncClient(transport=transport),
        )
        payload = {
            "schema_version": 1,
            "proposal_id": "hub-integration",
            "idempotency_key": "hub-integration",
            "source": {"source_type": "email", "message_id": "mail-1"},
            "summary": "Booking review",
            "candidate": {
                "kind": "legacy_json",
                "payload": {"sprint_type": "legacy_v1", "actors": []},
            },
        }
        first = await client.create(payload)
        again = await client.create(payload)
        assert again["deduplicated"] is True
        assert first["proposal"]["pending_sprint_id"] == again["proposal"]["pending_sprint_id"]
        status = await client.status(first["proposal"]["pending_sprint_id"], "integration")
        assert status["status"]["activation_state"] == "not_started"
        from inbound_hub.coordinator import Coordinator
        from inbound_hub.domains.musician import ROLES
        from inbound_hub.domains.registry import DomainPluginRegistration, DomainPluginRegistry
        from inbound_hub.pipeline import Pipeline, ProjectBinding, Store
        from inbound_hub.sources import parse_email

        registry = DomainPluginRegistry()
        registry.register(DomainPluginRegistration(plugin.metadata, plugin))
        store = Store(str(tmp_path / "hub-state.db"))
        binding = ProjectBinding(
            "musician-booking",
            payload["candidate"],
            {role: {"id": f"booking-{i}", "phone": str(2200 + i)} for i, role in enumerate(ROLES)},
        )
        pipeline = Pipeline(store, Coordinator(registry), binding, client)
        mail = parse_email(
            b"From: booking@example.invalid\nSubject: Concert\n"
            b"Date: Sat, 24 Oct 2026 10:00:00 +0000\nContent-Type: text/plain\n\n"
            b"venue: Hall\ncity: Berlin\nproposed_date: 2027-05-01",
            "mail-integration",
            {"artist_id": "alpha"},
        )
        store.ingest(mail)
        await pipeline.tick()
        state, observed_status = store.db.execute("SELECT state,status FROM proposals").fetchone()
        assert state == "submitted" and observed_status.endswith("not_started")
        candidate = json.loads(store.db.execute("SELECT body FROM proposals").fetchone()[0])[
            "candidate"
        ]
        assert len(candidate["payload"]["agents"]["items"]) == 6
        store.ingest(mail)
        await pipeline.tick()
        assert store.db.execute("SELECT count(*) FROM proposals").fetchone()[0] == 1
        store.db.close()
        client.token = base64.urlsafe_b64encode(b"B" * 32).decode().rstrip("=")
        with pytest.raises(DeliveryError) as error:
            await client.create(payload)
        assert error.value.status in (401, 403)
        await client.close()

    asyncio.run(exercise())
