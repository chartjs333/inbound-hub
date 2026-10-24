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


## Plugin Registry + Mobile Plugin Runtime + Authorization Broker
Implement a versioned Device Registry of QR checkpoint identifiers; signed Plugin Registry with plugin_id, version, runtime target, device compatibility, capabilities, hash/signature, install source and minimum app version; and an authorization broker separating discovery, install, activation and execution.
Mobile flow: scan QR -> resolve trusted device -> list compatible manifests -> check installed approved modules -> offer installation/activation -> authenticate researcher -> check agent and human entitlements -> perform optional short-lived step-up challenge -> issue device/plugin/action-scoped expiring grant -> enforce grant server-side for each operation -> revoke/expire on session end. Android dynamic delivery uses trusted signed platform packaging; iOS relies on App Store-approved bundled/app features, web UI or server-side adapters where code loading is prohibited.
For challenge: avoid sending static reusable PIN to backend/agent. Prefer secure platform authenticator unlock or validated one-time token from trusted verifier; bind code to user, session, device, action, nonce and expiry, with rate limiting and lockout. Validate privilege again on every device request; audit who, why, when and exact action. Initial device adapters remain observation/read-only.


## Card reader adapter and assurance policy
Introduce optional `SmartCardIdentityAdapter` implementing challenge/response verified by trusted identity provider. Issue an identity assertion bound to workstation session, user, project and expiry after one tap; release card immediately. Store authentication assurance attributes separately from authorization grants. Access decision combines session assurance/freshness, action required assurance, policy and per-plugin grant. Step-up triggered only when required. Never accept arbitrary card UID as secure authentication or store raw PIN; log events without credentials. Use simulator for MVP tests.
