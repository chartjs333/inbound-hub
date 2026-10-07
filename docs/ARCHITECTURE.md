# Inbound Hub Architecture v1

## Boundary

Inbound Hub owns source ingestion and proposal synthesis. nginx-qa owns pending-sprint review, Play/Start and execution.

## Components

1. Source adapters: Email, Telegram, Folder and future plugins.
2. Normalized event layer: one source-neutral event contract.
3. Coordinator: classification, project resolution and routing.
4. Proposal synthesizer: produces a candidate sprint proposal.
5. nginx-qa client: submits proposals through the versioned API only.
6. Notification publisher: Telegram/operator status without becoming the machine transport.
7. Persistence: dedupe, conversations, proposal lineage and audit.
8. Tray controller: optional Windows operator shell; service remains independent.

## MVP flow

Email -> EmailAdapter -> InboundEvent -> Coordinator -> Proposal -> nginx-qa API -> Pending Sprints -> operator Play.
