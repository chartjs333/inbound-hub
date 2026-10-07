from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from inbound_hub.events import InboundEvent


@dataclass(frozen=True)
class DomainPluginMetadata:
    plugin_id: str
    domain: str
    version: str
    config_schema_version: int
    supported_intents: tuple[str, ...]


@dataclass(frozen=True)
class DomainMatch:
    matched: bool
    confidence: float
    rationale: str = ""
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class DomainExtraction:
    data: dict[str, Any]
    missing_fields: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DomainClassification:
    intent: str
    confidence: float
    rationale: str = ""


@dataclass(frozen=True)
class DomainValidation:
    valid_for_proposal: bool
    missing_required_fields: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    blocked_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class DomainProposal:
    proposal_type: str
    payload: dict[str, Any]
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EscalationDecision:
    required: bool
    reason: str = ""


class DomainPlugin(Protocol):
    metadata: DomainPluginMetadata

    async def match(self, event: InboundEvent, context: dict[str, Any]) -> DomainMatch: ...
    async def extract(self, event: InboundEvent, context: dict[str, Any]) -> DomainExtraction: ...
    async def classify(
        self, extraction: DomainExtraction, context: dict[str, Any]
    ) -> DomainClassification: ...
    async def validate(
        self,
        extraction: DomainExtraction,
        classification: DomainClassification,
        context: dict[str, Any],
    ) -> DomainValidation: ...
    async def propose(
        self,
        extraction: DomainExtraction,
        classification: DomainClassification,
        context: dict[str, Any],
    ) -> DomainProposal | None: ...
    async def escalate(
        self,
        extraction: DomainExtraction,
        classification: DomainClassification,
        context: dict[str, Any],
    ) -> EscalationDecision: ...
