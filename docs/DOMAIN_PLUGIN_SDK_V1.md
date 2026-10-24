# Domain Plugin SDK v1

## Purpose

Define one stable contract for semantic/domain modules such as:
- musician-booking
- software-development
- sales
- recruiting
- support
- future domains

Source adapters answer "where did the data come from?".
Domain plugins answer "what does it mean and what workflow should be proposed?".

## Required plugin identity

Every domain plugin declares:
- plugin_id
- domain
- version
- config_schema_version
- supported_intents

## Required interface

Each domain plugin implements:

- match(event, context) -> DomainMatch
- extract(event, context) -> DomainExtraction
- classify(extraction, context) -> DomainClassification
- validate(extraction, classification, context) -> DomainValidation
- propose(extraction, classification, context) -> DomainProposal | None
- escalate(extraction, classification, context) -> EscalationDecision

## Match

match() returns:
- matched: bool
- confidence: 0..1
- rationale
- candidate_profile/project/subject identifiers when relevant

A low-confidence match must not silently claim the event.

## Extract

extract() converts normalized InboundEvent content into domain-specific structured data.

Rules:
- never fabricate missing values;
- preserve provenance references;
- keep explicit missing_fields;
- keep source-independent semantics.

## Classify

classify() returns a domain-specific intent and confidence.

Examples:
- musician-booking: new_concert_offer, availability_request, rider_request
- software-development: bug_report, feature_request, incident, question

## Validate

validate() reports:
- valid_for_proposal
- missing_required_fields
- warnings
- blocked_reasons

Validation must be deterministic where possible and must not mutate external systems.

## Propose

propose() returns a source-neutral proposal for the coordinator.

A domain plugin must not:
- start an nginx-qa sprint;
- call Play/start-from-git directly;
- mutate active sprint state;
- send autonomous external replies unless a separate correspondence policy authorizes it.

## Escalate

escalate() decides when human/operator intervention is required.

Examples:
- ambiguous subject/project
- legal/commercial commitment
- missing critical data
- conflicting instructions
- confidence below configured threshold

## Profiles

Domain plugins may load Git-versioned profiles.
Profile selection must be deterministic when possible and exact Git provenance must be retained.

## Registration

Domain plugins register through DomainPluginRegistry.
The central coordinator must not contain domain-specific if/else branches.

## Testing requirements

Every plugin must include contract tests for:
- match confidence and non-match behavior
- extraction without fabrication
- classification
- validation
- escalation
- proposal generation
- source parity (same meaning from Email/Telegram where applicable)
- provenance retention
- no direct activation side effects
