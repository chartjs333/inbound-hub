"""Conservative, deterministic booking plugin. No network or execution side effects."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, Literal, cast

import yaml
from pydantic import BaseModel, Field

from inbound_hub.domains.contracts import (
    DomainClassification,
    DomainExtraction,
    DomainMatch,
    DomainPluginMetadata,
    DomainProposal,
    DomainValidation,
    EscalationDecision,
)
from inbound_hub.events import InboundEvent

Intent = Literal[
    "new_concert_offer",
    "venue_outreach_opportunity",
    "availability_request",
    "fee_or_budget_question",
    "technical_rider_request",
    "hospitality_or_travel_question",
    "contract_or_legal_question",
    "promotion_or_press_request",
    "schedule_change",
    "cancellation",
    "ordinary_correspondence",
    "clarification_required",
    "ignore",
]
RULES = [
    ("cancellation", r"cancel|отмен"),
    ("contract_or_legal_question", r"contract|legal|exclusive|договор|контракт"),
    ("fee_or_budget_question", r"fee\?|budget\?|гонорар\?|бюджет\?"),
    ("schedule_change", r"reschedule|schedule change|перенос"),
    ("technical_rider_request", r"rider|райдер"),
    ("hospitality_or_travel_question", r"hotel|travel|hospitality|отель|проезд"),
    ("promotion_or_press_request", r"press kit|promotion|пресс|реклам"),
    ("availability_request", r"available|availability|свободн"),
    ("venue_outreach_opportunity", r"outreach|ищем площадк"),
    ("new_concert_offer", r"concert|booking|performance|концерт|выступлен"),
]
ROLES = [
    "Booking Manager",
    "Venue Researcher",
    "Artist Manager",
    "PR/Promotion Manager",
    "Logistics Coordinator",
    "Contract/Commercial Reviewer",
]


class BookingFields(BaseModel):
    organizer: str | None = None
    contact: str | None = None
    venue: str | None = None
    city: str | None = None
    country: str | None = None
    proposed_date: date | None = None
    proposed_time: str | None = None
    event_type: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    fee: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    payment_terms: str | None = None
    performance_duration: str | None = None
    technical_rider: str | None = None
    hospitality: str | None = None
    travel: str | None = None
    accommodation: str | None = None
    promotion: str | None = None
    deadlines: str | None = None


class MusicianBookingContext(BaseModel):
    artist_id: str | None = None
    suggested_artists: list[str] = Field(default_factory=list)
    intent: Intent
    fields: BookingFields
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    missing_fields: list[str]
    route: Literal["pending_proposal", "clarification_required", "correspondence", "ignore"]
    provenance: dict[str, Any]
    constraints: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["DRAFT_ONLY"] = "DRAFT_ONLY"

    def canonical_json(self) -> str:
        return json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))


class Profiles:
    """Read only committed profile blobs: working-tree edits cannot falsify provenance."""

    def __init__(self, repository: Path, ref: str = "HEAD"):
        self.repository = repository
        self.commit = self._git("rev-parse", "--verify", f"{ref}^{{commit}}").strip()
        common = self.read("profiles/musician-booking/profile.yaml")
        self.common = yaml.safe_load(common)
        if self.common["mode"] != "DRAFT_ONLY":
            raise ValueError("Only DRAFT_ONLY profiles are supported")
        self.guidance = {
            key: self.read("profiles/musician-booking/" + value)
            for key, value in self.common.items()
            if key.endswith("_file")
        }
        self.artists: dict[str, dict[str, Any]] = {}
        for path in self._git("ls-tree", "-r", "--name-only", self.commit, "artists").splitlines():
            if path.endswith("/artist.yaml"):
                profile = yaml.safe_load(self.read(path))
                artist_id = profile["artist_id"]
                if path != f"artists/{artist_id}/artist.yaml" or artist_id in self.artists:
                    raise ValueError("Invalid or duplicate artist identity")
                profile["context"] = {
                    name: self.read(f"artists/{artist_id}/{name}.md")
                    for name in (
                        "identity",
                        "booking",
                        "repertoire",
                        "rider",
                        "promotion",
                        "authority",
                    )
                }
                self.artists[artist_id] = profile

    def _git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.repository), *args], text=True)

    def read(self, path: str) -> str:
        if ".." in Path(path).parts or Path(path).is_absolute():
            raise ValueError("Profile paths must be repository-relative")
        return self._git("show", f"{self.commit}:{path}")

    def resolve(self, event: InboundEvent, mappings: dict[str, dict[str, str]]) -> str | None:
        explicit = event.metadata.get("artist_id") or event.metadata.get("project_id")
        if explicit:
            candidates = {str(explicit)}
        else:
            candidates = set()
            for keys in (("mailbox", "thread", "project"), ("contact",)):
                for key in keys:
                    value = {"thread": event.conversation_id, "contact": event.sender}.get(
                        key, event.metadata.get(key)
                    )
                    mapped = mappings.get(key, {}).get(str(value))
                    if mapped:
                        candidates.add(mapped)
                if candidates:
                    break
        if len(candidates) != 1:
            return None
        artist = candidates.pop()
        return artist if self.artists.get(artist, {}).get("active") is True else None


class MusicianBookingPlugin:
    metadata = DomainPluginMetadata(
        "musician-booking",
        "concert-booking",
        "1.0",
        1,
        tuple(x[0] for x in RULES)
        + ("ordinary_correspondence", "clarification_required", "ignore"),
    )

    def __init__(self, profiles: Profiles, mappings: dict[str, dict[str, str]] | None = None):
        self.profiles = profiles
        self.mappings = mappings or {}

    def analyze(self, event: InboundEvent) -> MusicianBookingContext:
        text = "\n".join(filter(None, [event.subject, event.body]))
        intent = next(
            (name for name, pattern in RULES if re.search(pattern, text, re.IGNORECASE)),
            "ordinary_correspondence",
        )
        if not text.strip():
            intent = "ignore"
        # Explicit labelled values only; ambiguous natural language stays unknown.
        values: dict[str, Any] = {}
        invalid = []
        for name in BookingFields.model_fields:
            match = re.search(rf"^{name}:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
            if match:
                try:
                    value = match.group(1).strip()
                    values[name] = getattr(BookingFields.model_validate({name: value}), name)
                except ValueError:
                    invalid.append(name)
        # Accept only unambiguous ISO dates and explicit currency amounts in free text.
        if "proposed_date" not in values and "proposed_date" not in invalid:
            dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text))
            if len(dates) == 1:
                try:
                    values["proposed_date"] = date.fromisoformat(dates.pop())
                except ValueError:
                    invalid.append("proposed_date")
        if "fee" not in values and "fee" not in invalid:
            amounts = set(re.findall(r"\b(\d+(?:\.\d{1,2})?)\s+(EUR|USD|GBP)\b", text))
            if len(amounts) == 1:
                amount, currency = amounts.pop()
                values["fee"], values["currency"] = float(amount), currency
        fields = BookingFields(**values)
        artist = self.profiles.resolve(event, self.mappings)
        missing = [
            name for name in ("venue", "city", "proposed_date") if getattr(fields, name) is None
        ]
        if not artist:
            missing.append("artist_id")
        constraints = self.profiles.artists.get(artist or "", {})
        reasons = list(invalid)
        if fields.country in constraints.get("excluded_markets", []):
            reasons.append("excluded_market")
        if fields.proposed_date and (fields.proposed_date - event.received_at.date()).days < int(
            constraints.get("minimum_notice_days", 0)
        ):
            reasons.append("minimum_notice_days")
        if (
            fields.fee is not None
            and constraints.get("typical_fee_min") is not None
            and (
                fields.currency != constraints.get("currency")
                or fields.fee < constraints["typical_fee_min"]
            )
        ):
            reasons.append("fee_requires_review")
        if intent in ("ordinary_correspondence", "ignore"):
            route = "ignore" if intent == "ignore" else "correspondence"
        elif (
            intent in ("new_concert_offer", "venue_outreach_opportunity")
            and not missing
            and not reasons
        ):
            route = "pending_proposal"
        else:
            route = "clarification_required"
        return MusicianBookingContext(
            artist_id=artist,
            suggested_artists=[
                key
                for key, profile in self.profiles.artists.items()
                if profile.get("display_name")
                and profile["display_name"].casefold() in text.casefold()
            ],
            intent=cast(Intent, intent),
            fields=fields,
            attachments=event.attachments,
            confidence=0.8 if intent not in ("ordinary_correspondence", "ignore") else 0.4,
            rationale="Deterministic keyword classification; explicit labelled extraction only",
            missing_fields=sorted(set(missing + reasons)),
            route=cast(Any, route),
            provenance={
                "event_id": event.event_id,
                "external_message_id": event.external_message_id,
                "source_text": text,
                "profile_commit": self.profiles.commit,
                "profile_version": self.profiles.common["version"],
                "artist_id": artist,
            },
            constraints={**constraints, "domain_guidance": self.profiles.guidance},
        )

    async def match(self, event, context):
        result = self.analyze(event)
        return DomainMatch(
            result.intent not in ("ordinary_correspondence", "ignore"),
            result.confidence,
            result.rationale,
        )

    async def extract(self, event, context):
        result = self.analyze(event)
        return DomainExtraction(
            result.model_dump(mode="json"), tuple(result.missing_fields), result.provenance
        )

    async def classify(self, extraction, context):
        data = extraction.data
        return DomainClassification(data["intent"], data["confidence"], data["rationale"])

    async def validate(self, extraction, classification, context):
        return DomainValidation(
            extraction.data["route"] == "pending_proposal", extraction.missing_fields
        )

    async def propose(self, extraction, classification, context):
        if not (await self.validate(extraction, classification, context)).valid_for_proposal:
            return None
        return DomainProposal(
            "concert-booking",
            {
                "status": "pending",
                "mode": "DRAFT_ONLY",
                "artist_id": extraction.data["artist_id"],
                "tasks": [
                    {
                        "role": role,
                        "constraints": extraction.data["constraints"],
                        "instruction": "Review proposed terms; obtain human approval for commitments",
                    }
                    for role in ROLES
                ],
                "booking": extraction.data,
            },
            extraction.provenance,
        )

    async def escalate(self, extraction, classification, context):
        required = extraction.data["route"] == "clarification_required"
        return EscalationDecision(
            required, "Human clarification or approval required" if required else ""
        )
