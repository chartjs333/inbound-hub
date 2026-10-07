from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


_SLUG_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class ProposalArtifactName:
    proposal_id: str
    source_artifact: str
    display_name: str


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value.casefold()).strip("-")
    return slug or "proposal"


def build_proposal_artifact_name(
    display_name: str,
    *,
    stable_seed: str,
    date_label: str | None = None,
) -> ProposalArtifactName:
    digest = hashlib.sha256(stable_seed.encode("utf-8")).hexdigest()
    short_id = "p" + digest[:6]
    proposal_id = "proposal-" + digest[:20]

    parts = [_slugify(display_name)]
    if date_label:
        parts.append(_slugify(date_label))
    parts.append(short_id)
    source_artifact = "-".join(part for part in parts if part) + ".json"

    return ProposalArtifactName(
        proposal_id=proposal_id,
        source_artifact=source_artifact,
        display_name=display_name.strip() or "Proposal",
    )
