from inbound_hub.proposals.naming import build_proposal_artifact_name


def test_human_readable_name_and_stable_id() -> None:
    item = build_proposal_artifact_name(
        "Berlin Concert Venues",
        stable_seed="email:thread-123:message-456",
        date_label="November 2026",
    )
    assert item.source_artifact.startswith("berlin-concert-venues-november-2026-p")
    assert item.source_artifact.endswith(".json")
    assert item.proposal_id.startswith("proposal-")
    assert item.display_name == "Berlin Concert Venues"


def test_same_seed_keeps_same_identity() -> None:
    a = build_proposal_artifact_name("First title", stable_seed="same")
    b = build_proposal_artifact_name("Updated title", stable_seed="same")
    assert a.proposal_id == b.proposal_id
