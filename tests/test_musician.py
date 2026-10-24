import asyncio
import subprocess
from datetime import UTC, datetime

import pytest
import yaml

from inbound_hub.coordinator import Coordinator
from inbound_hub.domains.musician import RULES, MusicianBookingPlugin, Profiles
from inbound_hub.domains.registry import DomainPluginRegistration, DomainPluginRegistry
from inbound_hub.events import InboundEvent


@pytest.fixture
def plugin(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    root = tmp_path / "profiles/musician-booking"
    root.mkdir(parents=True)
    (root / "profile.yaml").write_text(
        "version: 1\nmode: DRAFT_ONLY\nauthority_file: authority.md\n"
    )
    (root / "authority.md").write_text("No autonomous commitments")
    for artist, fee in [("alpha", 100), ("beta", 200)]:
        folder = tmp_path / "artists" / artist
        folder.mkdir(parents=True)
        (folder / "artist.yaml").write_text(
            yaml.safe_dump(
                {
                    "artist_id": artist,
                    "active": True,
                    "typical_fee_min": fee,
                    "currency": "EUR",
                    "excluded_markets": ["XX"],
                    "minimum_notice_days": 2,
                }
            )
        )
        for name in ("identity", "booking", "repertoire", "rider", "promotion", "authority"):
            (folder / f"{name}.md").write_text(f"{artist}: {name}")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "profiles",
        ],
        check=True,
    )
    return MusicianBookingPlugin(Profiles(tmp_path), {"mailbox": {"bookings": "beta"}})


def event(body="Concert offer\nvenue: Hall\ncity: Berlin\nproposed_date: 2027-05-01", **kwargs):
    return InboundEvent(
        event_id="1",
        external_message_id="source-1",
        channel="email",
        received_at=datetime(2026, 10, 24, tzinfo=UTC),
        body=body,
        metadata=kwargs or {"artist_id": "alpha"},
    )


def test_source_parity_and_profile_provenance(plugin):
    mail = event()
    assert plugin.analyze(mail) == plugin.analyze(mail.model_copy(update={"channel": "telegram"}))
    result = plugin.analyze(mail)
    assert len(result.provenance["profile_commit"]) == 40
    assert result.route == "pending_proposal"
    assert result.canonical_json() == result.canonical_json()


def test_resolution_and_constraints(plugin):
    assert plugin.analyze(event(artist_id="alpha", mailbox="bookings")).artist_id == "alpha"
    assert plugin.analyze(event(mailbox="bookings")).artist_id == "beta"
    assert plugin.analyze(event(artist_id="unknown")).route == "clarification_required"
    assert plugin.analyze(event(untrusted="alpha")).artist_id is None
    a = plugin.analyze(event())
    b = plugin.analyze(event(artist_id="beta"))
    assert a.constraints != b.constraints


@pytest.mark.parametrize(
    "body",
    [
        "Cancel concert",
        "contract",
        "fee?",
        "rider",
        "hotel",
        "press kit",
        "available?",
        "reschedule",
    ],
)
def test_sensitive_or_incomplete_requests_escalate(plugin, body):
    assert plugin.analyze(event(body)).route == "clarification_required"


def test_no_fabrication_and_invalid_values(plugin):
    result = plugin.analyze(event("concert\nfee: -2\nproposed_date: tomorrow"))
    assert result.fields.fee is None and result.fields.proposed_date is None
    assert "fee" in result.missing_fields
    assert result.route == "clarification_required"


def test_coordinator_and_no_sprint_for_correspondence(plugin):
    registry = DomainPluginRegistry()
    registry.register(DomainPluginRegistration(plugin.metadata, plugin))
    coordinator = Coordinator(registry)
    result = asyncio.run(coordinator.handle(event(), "musician-booking"))
    assert result["proposal"].payload["status"] == "pending"
    assert len(result["proposal"].payload["tasks"]) == 6
    for text in ("Thank you", "Cancel concert", ""):
        assert asyncio.run(coordinator.handle(event(text), "musician-booking"))["proposal"] is None


def test_all_intents_and_market_policy(plugin):
    assert len(RULES) == 10
    result = plugin.analyze(event(event().body + "\ncountry: XX"))
    assert result.route == "clarification_required"
    assert "excluded_market" in result.missing_fields


def test_dirty_profiles_do_not_change_provenance(plugin):
    path = plugin.profiles.repository / "artists/alpha/artist.yaml"
    path.write_text("artist_id: attacker")
    reloaded = Profiles(plugin.profiles.repository)
    assert reloaded.artists["alpha"]["artist_id"] == "alpha"
    assert reloaded.commit == plugin.profiles.commit
