# Proposal Naming v1

## Goal

Proposal JSON filenames must be understandable to a human while remaining technically stable through an internal ID.

## Filename format

Use:

```text
<readable-topic>[-<date-if-useful>]-<short-id>.json
```

Examples:

```text
berlin-concert-venues-november-2026-p7f3a2.json
fix-payment-api-timeout-p91c4e.json
artist-tour-routing-germany-p31bd8.json
```

Rules:

- readable topic first;
- lowercase ASCII slug;
- words separated by hyphens;
- keep the visible topic concise;
- add a date only when it materially helps a person understand the proposal;
- append a short collision-resistant ID;
- extension is always `.json`.

## Required JSON fields

Every proposal JSON must include:

```json
{
  "proposal_id": "proposal-<stable-id>",
  "source_artifact": "<human-readable-filename>.json",
  "display_name": "<human readable title>"
}
```

`proposal_id` is the authoritative technical identity.

The filename is for people and may be regenerated before publication if needed. Systems must not depend on the readable slug for identity.

## Cross-system linking

Inbound Hub:
- generates `proposal_id`;
- generates `source_artifact`;
- records lightweight audit events under `proposal_id`.

nginx-qa:
- receives and stores the same `proposal_id` and `source_artifact`;
- exposes them in pending-sprint metadata/UI where available.

This provides a human-readable cross-system reference while keeping a stable internal identifier.
