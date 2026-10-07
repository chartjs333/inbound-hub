# Musician Booking Domain Adapter v1

## Purpose

Add a domain-specific interpretation layer for musicians and concert booking without coupling source ingestion to the music domain.

Source adapters (Email, Telegram, Folder, etc.) still emit the same normalized InboundEvent.
The Musician Booking Domain Adapter consumes normalized events after source ingestion and enriches/classifies them for concert-management workflows.

## Recognized intents

- new_concert_offer
- venue_outreach_opportunity
- availability_request
- fee_or_budget_question
- technical_rider_request
- hospitality_or_travel_question
- contract_or_legal_question
- promotion_or_press_request
- schedule_change
- cancellation
- ordinary_correspondence
- clarification_required
- ignore

## Extracted domain fields

When present:
- artist/project identity
- organizer/contact
- venue name
- city/country
- proposed date/time
- event type
- audience/capacity
- fee/currency
- payment terms
- performance duration
- technical rider requirements
- hospitality/travel/accommodation
- promotion/press requirements
- deadlines
- attachments/references
- confidence and missing fields

## Proposal behavior

The adapter does not create or activate an nginx-qa sprint directly.

It returns domain context to the central Inbound Coordinator. The coordinator may then:
- create a pending sprint proposal;
- ask for clarification;
- mark the conversation waiting for reply;
- treat it as correspondence only.

A proposal for concert work should use domain roles such as:
- Booking Manager
- Venue Researcher
- Artist Manager
- PR/Promotion Manager
- Logistics Coordinator
- Contract/Commercial Reviewer

## Safety and approval boundaries

The MVP must not autonomously:
- sign or accept contracts;
- confirm a final fee;
- make legal commitments;
- cancel a confirmed event;
- expose private contact/payment data;
- send autonomous replies unless a later delegated-correspondence policy explicitly permits it.

## Integration

Input:
- normalized InboundEvent

Output:
- MusicianBookingContext
- classified intent
- extracted structured fields
- recommended coordinator route
- proposed specialist roles when a sprint is appropriate

The implementation must be source-neutral: the same email or Telegram message describing the same concert request should produce equivalent domain context.


## Multi-artist support

The Musician Booking Domain Adapter is shared across artists. Artist-specific behavior is loaded from an Artist Profile selected before proposal generation.

Suggested structure:

```text
artists/<artist-id>/
  artist.yaml
  identity.md
  booking.md
  repertoire.md
  rider.md
  promotion.md
  authority.md
```

`artist.yaml` should contain machine-readable fields such as:
- artist_id
- display_name
- active/inactive
- genres/instrument
- home_city/country
- preferred_markets
- excluded_markets
- typical_fee_min/max/currency (optional)
- minimum_notice_days
- default_performance_duration
- profile file paths
- escalation rules

The Markdown files hold richer context:
- identity.md — positioning, biography, artist identity
- booking.md — booking preferences, preferred venues/events, timing constraints
- repertoire.md — program/repertoire context
- rider.md — technical/hospitality requirements
- promotion.md — press kit, positioning, promo requirements
- authority.md — what may or may not be decided automatically

Artist resolution order:
1. explicit artist/project id in source metadata;
2. known mailbox/thread/project mapping;
3. configured contact/project mapping;
4. content-based candidate resolution only as a suggestion;
5. if ambiguous, route to clarification_required and do not create a sprint proposal.

The selected artist profile and exact Git commit must be attached to MusicianBookingContext/proposal provenance.

The same source message must never silently switch artists based only on model inference.
