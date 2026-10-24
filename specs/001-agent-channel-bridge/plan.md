# Plan: inbound-hub
## Existing boundary
Keep Email/Telegram/Folder -> normalized inbound event -> sprint proposal -> nginx-qa intact.
## New isolated subsystem
Channel Registry (scope/capabilities/policy), Outbound Dispatcher, adapter interface, Human Presence Store, QR Checkpoint Registry, durable request/event store and callback client to nginx-qa.
## Adapter surface
resolve_channel; get_capabilities; send_message; request_data; request_live_session; get_status; cancel. Device adapters read-only for MVP. Capability check before dispatch.
## Security and failure
Signed requests/callbacks, project-scope auth, operator consent for voice/camera, presence TTL, default-offline, replay/idempotency, media validation, encrypted credentials, artifact reference and audit. No arbitrary instruments commands; no authorization encoded in QR.
## Tests
Offline/online simulation, parallel channels, connection loss/retries, duplicate/reordered events, QR spoof, unauthorized cross-project, end-to-end with nginx-qa disposable active sprint.
